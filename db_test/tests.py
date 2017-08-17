import inspect


class DBTest:
    def __init__(self, name, data, dbms, log):
        self.dbms = dbms
        self.name = name
        self.data = data
        self.log = log

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

        self.log("blue| %s %s" % (self.name, result))

    def _run(self):
        if self.data['db'] not in self.dbms.db_connections:
            return ("yellow| There is no target DB for testing - %s. "
                    "Available DB names are: %s. Skipped." %
                    (self.data['db'], self.dbms.db_connections.keys()))

        kwargs = {
            'db_name': self.data['db'],
            'query': self.data['sql']
        }
        if 'sql' in self.data:
            if self.data.get('params'):
                kwargs.update(self.data['params'])
            res = self.dbms.sql_execute(**kwargs)
            if self.dbms.test_error:
                return "red| Failed\n%s" % self.dbms.test_err_msg

        if 'check_sql' in self.data:
            check_kwargs = {
                'db_name': self.data['db'],
                'query': self.data['check_sql']
            }
            if self.data.get('params'):
                check_kwargs.update(self.data['params'])
            res = self.dbms.sql_execute(**check_kwargs)
            if self.dbms.test_error:
                return "red| Failed\n%s" % self.dbms.test_err_msg

        if res == self.data['result']:
            return "green| Passed"
        else:
            return ("red| Failed\n Expected result: \n%s \ndoes not much "
                    "actual: \n%s" % (self.data['result'], res))


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
                self.log("blue| %s red| Failed\n %s" % (test[0], e))
        else:
            for test in tests:
                try:
                    test[1](db_class)
                    self.log("blue| %s green| Passed" % test[0])
                except Exception as e:
                    self.log("blue| %s red| Failed\n %s" % (test[0], e))