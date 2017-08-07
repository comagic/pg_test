# -*- coding:utf-8 -*-
import os
import time
import psycopg2
import psycopg2.extras
import subprocess
import sys
import tempfile

from pg_import import executor


time_format = '%Y-%m-%d %h:%M:%s'

refresh_seq = """
    do  language plpgsql $$
    declare
      r record;
      t integer;
      s integer;
    begin
      for r in
        select dep.deptype, cl.relname, att.attname, nsc.nspname, seq.relname as seqname, nss.nspname as seqnsp
          from pg_class seq
          join pg_namespace nss ON seq.relnamespace = nss.oid
          join pg_depend dep on dep.objid = seq.oid
          join pg_class cl ON dep.refobjid = cl.oid
          join pg_attribute att ON dep.refobjid=att.attrelid AND dep.refobjsubid=att.attnum
          join pg_namespace nsc ON cl.relnamespace=nsc.oid
         where seq.relkind = 'S' and deptype = 'a'
      loop
        execute format('select max(%%I) from %%I.%%I', r.attname, r.nspname, r.relname) into t;
        execute format('select last_value from %%I.%%I', r.seqnsp, r.seqname) into s;

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
    def __init__(self, test, args):
        self.docker = args.use_docker or True
        self.test = test
        self.log = self.test.log
        self.host = args.host
        self.port = args.port
        self.test_dir = args.test_dir
        self.db_dirs = args.db_dirs
        self.ext_name = time.strftime('_test_%Y%m%d%H%M%S')
        self.dbs = dict([d.split(':') for d in self.db_dirs])
        self.db_connections = {}
        self.db_connections['sys'] = psycopg2.connect(dbname='postgres', host=self.host, port=self.port, user='postgres')
        self.db_connections['sys'].set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    def ext_db_name(self, db_name):
        return db_name + self.ext_name

    def drop_db(self):
        for db_name in self.dbs:
            try:
                self.log('green| Droping db %s', db_name)
                self.sql_execute('sys', 'drop database %s' % self.ext_db_name(db_name))
            except psycopg2.ProgrammingError as e:
                print("Error: Drop DB is failed, due to: %s" % e)

    def clean_all(self):
        self.disconnect_db()
        self.drop_db()

    def process_pg_import(self, section, db_dir, ext_db_name, extra_data=''):
        ''' Get commands from pg_import and execute them '''
        pg_cmds = FileStub()
        kwargs = {
            'section': {section},
            'src_dir': db_dir,
            'output': pg_cmds
        }
        executor.Executor(**kwargs)()

        final_string = ''.join([extra_data, pg_cmds.read()])
        if self.docker:
            # NOTE Customization commands for docker!
            # replace it due to hardcode in main repo comagic_db
            final_string = final_string.replace(
                '/usr/lib64/pgsql/tablefunc',
                '/usr/lib/postgresql/9.6/lib/tablefunc')

        # Create temporary file for easy debugging and other funny things
        f_name = tempfile.mkstemp(suffix=section)[1]

        # Write pg_import output to file
        with open(f_name, 'w') as f_obj:
            f_obj.write(final_string)

        try:
            # Execute all commands from the file
            res = self.run_pysql_commands(f_name, ext_db_name)
        except Exception as e:
            os.remove(f_name)
            raise e

        if res.stderr:
            sys.exit("Error during execution command: %s. Temporary file with "
                     "DB data is available by path: %s" % (res.stderr, f_name))
        os.remove(f_name)

    def run_pysql_commands(self, f_name, ext_db_name):
        ''' Execute cammand in subprocess to handle Errors '''
        command = ('psql -f %(f_name)s -U postgres -h %(host)s -p %(port)s '
                   '%(ext_db_name)s > /dev/null' % {'f_name': f_name,
                                                    'host': self.host,
                                                    'port': self.port,
                                                    'ext_db_name': ext_db_name}
        )
        return subprocess.run(command, shell=True, check=True,
                              stderr=subprocess.PIPE)

    def build_db(self):
        for db_name, db_dir in self.dbs.items():
            ext_db_name = self.ext_db_name(db_name)
            self.log('green| Creating db %s', db_name)
            self.sql_execute('sys', 'create database %s' % ext_db_name)
            self.log('green| Creating schema')
            self.process_pg_import(
                'pre-data', db_dir, ext_db_name,
                extra_data="set client_min_messages to warning;")

            self.log('green| Loading data')
            self.process_pg_import('data', db_dir, ext_db_name)

            test_data = os.path.join(self.test_dir, 'data', db_name)
            if os.path.exists(test_data):
                self.log('green| Loading test data into database %s' % db_name)
                self.process_pg_import('data', test_data, ext_db_name)

            self.log('green| Creating constraint')
            self.process_pg_import('post-data', db_dir, ext_db_name)

            self.log('green| DB connecting %s', db_name)
            self.db_connections[db_name] = psycopg2.connect(dbname=ext_db_name,
                                                            host=self.host,
                                                            port=self.port,
                                                            user='postgres')
            self.sql_execute(db_name, refresh_seq)

    def disconnect_db(self):
        for db_name in self.dbs:
            self.log('green| DB disconnecting %s', db_name)
            if self.db_connections.get(db_name):
                self.db_connections[db_name].close()
                del self.db_connections[db_name]

    def sql_execute(self, db_name, query, **query_params):
        res = None
        con = None
        try:
            con = self.db_connections[db_name]
            c = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            c.execute(query, query_params)
            if c.rowcount > 0:
                res = c.fetchall()
            con.commit()
        except Exception as e:
            if con:
                con.rollback()
            if self.test.is_debug:
                try:
                    sql = c.mogrify(query, query_params)
                except Exception as ee:
                    sql = 'unpattern(%s %s)  %s' % (ee.__class__.__name__,
                                                    ee, query)
                self.log(
                    'red|Exception on execute sql:\nyellow|%s\nred|%s: %s',
                    sql, e.__class__.__name__, e)
            raise e
        finally:
            while con.notices:
                self.log('yellow|%s', con.notices.pop())
            c.close()
        return res
