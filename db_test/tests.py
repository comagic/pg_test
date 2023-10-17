import inspect
import re
import datadiff


class DBTest:
    def __init__(self, name, data, dbms):
        self.dbms = dbms
        self.name = name
        self.data = data
        self.data['params'] = self.data.get('params') or {}

    def run(self):
        result = self._run()
        # Run cleanup only if main logic is success, i.e. result is Success
        if self.data.get('cleanup') and 'green' in result:
            kwargs = {
                'db_name': self.data['db'],
                'query': self.data['cleanup']
            }
            self.dbms.sql_execute(**kwargs)
            if self.dbms.test_error:
                result = ("red| Cleanup failed\n%s" % self.dbms.test_err_msg)
        return result

    def _run(self):
        if self.data['db'] not in self.dbms.db_connections:
            return ("yellow| There is no target DB for testing - %s. "
                    "Available DB names are: %s. Skipped." %
                    (self.data['db'], self.dbms.db_connections.keys()))

        plexor_connections = {
            'plexor_connection_' + db_name: (
                f'dbname={self.dbms.ext_db_name(db_name)} '
                f'host={self.dbms.host} port={self.dbms.port}'
            )
            for db_name in self.dbms.dbs
        }

        if 'sql' in self.data:
            res = self.dbms.sql_execute(
                self.data['db'],
                self.data['sql'],
                **self.data['params'],
                **plexor_connections,
            )
            if self.dbms.test_error:
                if not self.data.get('expected_exception'):
                    return "red| Failed\n%s" % self.dbms.test_err_msg
                elif self.match_expected_exception():
                    return "green| Passed"
                else:
                    return (
                        "red| Failed\n"
                        "yellow|    expected exception:\n"
                        "default|      %s\n"
                        "yellow|    does not match actual exception:\n"
                        "default|      %s\n"
                        "yellow|    details:\n"
                        "default|      %s") % (
                            self.data['expected_exception'],
                            self.dbms.exception.diag.message_primary,
                            '\n     '.join(self.dbms.test_err_msg.split('\n')))

        if self.data.get('global_params_by_sql'):
            params = self.dbms.sql_execute(
                self.data['db'],
                self.data['global_params_by_sql'],
                **self.data['params']
            )
            if self.dbms.test_error:
                return "red| Failed on global_params_by_sql\n%s" % self.dbms.test_err_msg
            if params:
                self.dbms.global_params.update(params[0])

        if self.data.get('check_sql'):
            res = self.dbms.sql_execute(
                self.data['db'],
                self.data['check_sql'],
                **self.data['params']
            )
            if self.dbms.test_error:
                return "red| Failed on check_sql\n%s" % self.dbms.test_err_msg

        if self.data.get('expected_exception'):
            expected_res = 'expected_exception: ' + \
                           self.data['expected_exception']
        else:
            expected_res = self.data['result']

        if res == expected_res:
            return "green| Passed"
        else:
            return (f"red| Failed\n"
                    f"yellow|    expected result:\n"
                    f"default|      {expected_res}\n"
                    f"yellow|    does not match actual:\n"
                    f"default|      {res}\n"
                    f"yellow|    diff:\n"
                    f"default|{self.diff_strings(expected_res, res)}")

    def match_expected_exception(self):
        return (
            self.data.get('expected_exception') and
            re.match(
                self.data.get('expected_exception'),
                str(self.dbms.exception).replace('\n', ' ')
            )
        )

    def diff_strings(self, excepted, result):
        if excepted is None or result is None:
            return ''
        return str(datadiff.diff(
            excepted,
            result,
            fromfile="expected",
            tofile="result",
        ))


class PythonTests:
    def __init__(self, plugin_class, dbms, log):
        self.plugin_class = plugin_class
        self.dbms = dbms
        self.log = log

    def run(self):
        tests = [
            t for t in inspect.getmembers(self.plugin_class,
                                          predicate=inspect.isfunction)
            if t[0].startswith('test_')]
        # sort tests by name
        tests = sorted(tests, key=lambda t: t[0])
        creds = self.dbms.db_credentials()
        try:
            db_class = self.plugin_class(creds)
        except Exception as e:
            for test in tests:
                self.log("blue|  %s red| Failed\n %s" % (test[0], e))
        else:
            for test in tests:
                try:
                    test[1](db_class)
                    self.log("blue|  %s green| Passed" % test[0])
                except Exception as e:
                    self.log("blue|  %s red| Failed\n %s" % (test[0], e))
