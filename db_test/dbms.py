# -*- coding:utf-8 -*-
import os
import time
import psycopg2
import psycopg2.extras
import subprocess

from pg_import import executor


time_format = '%Y-%m-%d %h:%M:%s'

refresh_seq = """
    do language plpgsql $$
    declare
      r record;
      t integer;
      s integer;
    begin
      for r in
        select dep.deptype, cl.relname, att.attname, nsc.nspname,
               seq.relname as seqname, nss.nspname as seqnsp
          from pg_class seq
          join pg_namespace nss ON seq.relnamespace = nss.oid
          join pg_depend dep on dep.objid = seq.oid
          join pg_class cl ON dep.refobjid = cl.oid
          join pg_attribute att ON dep.refobjid=att.attrelid AND
                dep.refobjsubid=att.attnum
          join pg_namespace nsc ON cl.relnamespace=nsc.oid
         where seq.relkind = 'S' and deptype = 'a'
      loop
        execute format('select coalesce(max(%I), 0)
                          from %I.%I',
                       r.attname, r.nspname, r.relname) into t;
        execute format('select last_value - (not is_called)::int
                          from %I.%I',
                       r.seqnsp, r.seqname) into s;

        if t <> s then
          perform setval(r.seqnsp ||'.'||r.seqname, t, true);
        end if;
      end loop;
    end;$$;"""


class FileStub:
    '''
    Stub for processing of output of the pg_import parser

    It uses list, for clear debugging and fixing. So each element in the list
    is a content of seprate file in source DB repository.
    '''
    def __init__(self):
        self.data = ""

    def write(self, string):
        self.data = ''.join([self.data, string])

    def read(self):
        return self.data


class DBMS:
    application_name = 'db_test'

    def __init__(self, log, args):
        self.docker = args.use_docker or False
        self.log = log
        self.verbose = args.verbose
        self.host = args.host
        self.port = args.port
        self.username = args.username or os.environ.get('PGUSER', 'postgres')
        self.test_dir = args.test_dir
        self.db_dirs = args.db_dirs
        self.ext_name = time.strftime('_test_%Y%m%d%H%M%S')
        self.dbs = dict([d.split(':') for d in self.db_dirs])
        self.db_connections = {}
        self.connect_db(
            'sys',
            'postgres',
            psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        self.test_error = False
        self.test_err_msg = "green|No error"

    def ext_db_name(self, db_name):
        return db_name + self.ext_name

    def drop_db(self):
        for db_name in self.dbs:
            try:
                self.log('green|Droping db %s', db_name)
                self.sql_execute(
                    'sys', 'drop database %s' % self.ext_db_name(db_name))
            except psycopg2.ProgrammingError as e:
                print("Error: Drop DB is failed, due to: %s" % e)

    def clean_all(self):
        self.disconnect_db()
        self.drop_db()

    def process_pg_import(self, section, db_dir, db_name, extra_data=''):
        ''' Get commands from pg_import and execute them '''
        pg_cmds = FileStub()
        kwargs = {
            'section': {section},
            'src_dir': db_dir,
            'output': pg_cmds
        }
        executor.Executor(**kwargs)()

        final_string = ''.join([extra_data, pg_cmds.read()])

        if section == 'data':
            def build_copy_cmd(header, strs):
                return header + '\n'.join(strs) + "\nEeOoFf$program$;"

            # split data by 127KB
            cmds = []
            final_string += '\n\n'
            tables = final_string.split('\n\\.\n\n')[:-1]
            for t in tables:
                strs = t.split('\n')
                copy = strs.pop(0)
                copy = copy.replace(
                    "from stdin;",
                    'from program $program$cat <<"EeOoFf"\n'
                )
                if not strs:
                    continue
                tmp_strs = []
                cur_len = 0
                for s in strs:
                    s_len = len(s.encode('utf-8'))
                    if cur_len + s_len < 126 * 1024:
                        tmp_strs.append(s)
                        cur_len += s_len
                    else:
                        cmds.append(build_copy_cmd(copy, tmp_strs))
                        tmp_strs = [s]
                        cur_len = s_len
                cmds.append(build_copy_cmd(copy, tmp_strs))
            final_string = '\n\n'.join(cmds)

        self.sql_execute(db_name, final_string)
        if self.exception:
            raise self.exception

    def run_psql_commands(self, f_name, ext_db_name):
        ''' Execute cammand in subprocess to handle Errors '''
        command = (
            'psql -f %(f_name)s -U %(user)s -h %(host)s -p %(port)s '
            '%(ext_db_name)s > /dev/null' % {'f_name': f_name,
                                             'host': self.host,
                                             'port': self.port,
                                             'user': self.username,
                                             'ext_db_name': ext_db_name})
        return subprocess.run(command, shell=True, check=True,
                              stderr=subprocess.PIPE)

    def build_db(self):
        for db_name, db_dir in self.dbs.items():
            ext_db_name = self.ext_db_name(db_name)
            self.log('green|Creating db %s (%s)', db_name, ext_db_name)
            self.sql_execute('sys', 'create database %s' % ext_db_name)
            self.log('green|Creating schema')
            self.connect_db(db_name, ext_db_name)
            self.process_pg_import(
                'pre-data', db_dir, db_name,
                extra_data="set client_min_messages to warning;")

            self.log('green|Loading default data')
            self.process_pg_import('data', db_dir, db_name)

            test_data = os.path.join(self.test_dir, 'data', db_name)
            if os.path.exists(test_data):
                self.log('green|Loading test data into database %s' % db_name)
                self.process_pg_import('data', self.test_dir, db_name)

            self.log('green|Creating constraint')
            self.process_pg_import('post-data', db_dir, db_name)

            self.log('green|DB connecting %s', db_name)
            self.sql_execute(db_name, refresh_seq)

    def connect_db(self, db_name, ext_db_name, isolation_level=None):
        self.db_connections[db_name] = psycopg2.connect(
            dbname=ext_db_name,
            host=self.host,
            port=self.port,
            user=self.username,
            application_name=self.application_name)
        if isolation_level is not None:
            self.db_connections[db_name].set_isolation_level(isolation_level)

    def disconnect_db(self):
        for db_name in self.dbs:
            self.log('green|DB disconnecting %s', db_name)
            if self.db_connections.get(db_name):
                self.db_connections[db_name].close()
                del self.db_connections[db_name]

    def sql_execute(self, db_name, query, **query_params):
        res = None
        con = None
        self.test_error = False
        self.test_err_msg = None
        self.exception = None
        try:
            con = self.db_connections[db_name]
            cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            if query_params:
                cur.execute(query, query_params)
            else:
                cur.execute(query)
            if cur.rowcount > 0:
                try:
                    res = [dict(r) for r in cur.fetchall()]
                except psycopg2.ProgrammingError:
                    # catch error if execute return something on "insert"
                    pass
            con.commit()
        except (Exception, psycopg2.Error) as e:
            if con:
                con.rollback()
            if self.verbose:
                try:
                    sql = cur.mogrify(query, query_params).decode('utf-8')
                except Exception as ee:
                    sql = 'unpattern(%s %s)  %s' % (ee.__class__.__name__,
                                                    ee, query)
                self.test_err_msg = (
                    "red|Exception on execute sql:\ndefault|  %s\nred|%s: %s" %
                    ('\n  '.join(sql.split('\n')), e.__class__.__name__, e))
            self.test_error = True
            self.exception = e
        finally:
            while con.notices:
                self.log('yellow|    %s', con.notices.pop())
            cur.close()
        return res

    def db_credentials(self):
        ''' Returns list of createndials for connecting to Test DB '''
        data = {
            'host': self.host,
            'port': self.port,
            'db_names': [self.ext_db_name(db_name) for db_name in self.dbs]
        }
        return data
