class TestCase:
    def __init__(self, test, name, data):
        self.test = test
        self.name = name
        self.data = data

    def run(self):
        result = self._run()
        if self.data.get('cleanup') and 'green' in result:
            kwargs = {
                'db_name': self.data['db'],
                'query': self.data['cleanup']
            }
            res = self.test.dbms.sql_execute(**kwargs)
            if self.test.dbms.test_error:
                return ("red| Cleanup failed\n%s" %
                        self.test.dbms.test_err_msg)
        return result

    def _run(self):
        if self.data['db'] not in self.test.dbms.db_connections:
            return ("yellow| There is no target DB for testing - %s. "
                    "Available DB names are: %s. Skipped." %
                    (self.data['db'], self.test.dbms.db_connections.keys()))
        kwargs = {
            'db_name': self.data['db'],
            'query': self.data['sql']
        }
        if 'sql' in self.data:
            if self.data.get('params'):
                kwargs.update(self.data['params'])
            res = self.test.dbms.sql_execute(**kwargs)
            if self.test.dbms.test_error:
                return ("red| Failed\n%s" % self.test.dbms.test_err_msg)

        if 'check_sql' in self.data:
            check_kwargs = {
                'db_name': self.data['db'],
                'query': self.data['check_sql']
            }
            if self.data.get('params'):
                check_kwargs.update(self.data['params'])
            res = self.test.dbms.sql_execute(**check_kwargs)
            if self.test.dbms.test_error:
                return ("red| Failed\n%s" % self.test.dbms.test_err_msg)

        if res == self.data['result']:
            return "green| Passed"
        else:
            return ("red| Failed\n Expected result: \n%s \ndoes not much "
                    "actual: \n%s" % (self.data['result'], res))

