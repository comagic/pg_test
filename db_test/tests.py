import inspect
import re
import difflib
from wasabi import color


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
        self.log("blue| %s %s", self.name, result)

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
            if self.dbms.test_error and not self.match_expected_exception():
                return "red| Failed\n%s" % self.dbms.test_err_msg

        if 'check_sql' in self.data:
            check_kwargs = {
                'db_name': self.data['db'],
                'query': self.data['check_sql']
            }
            if self.data.get('params'):
                check_kwargs.update(self.data['params'])
            res = self.dbms.sql_execute(**check_kwargs)
            if self.dbms.test_error and not self.match_expected_exception():
                return "red| Failed\n%s" % self.dbms.test_err_msg

        if self.dbms.test_error and self.match_expected_exception():
            return "green| Passed"
        if res == self.data['result']:
            return "green| Passed"
        else:
            return ("red|Failed\n"
                    "yellow|expected result:\n"
                    "default| %s\n"
                    "yellow|does not match actual:\n"
                    "default| %s\n"
                    "yellow|diff:\n"
                    "default| %s") % (self.data['result'],
                                      res,
                                      self.diff_strings(
                                          str(self.data['result']),
                                          str(res)))

    def match_expected_exception(self):
        return self.data.get('expected_exception') and \
               re.match(self.data.get('expected_exception'),
                        str(self.dbms.exception).replace('\n', ' '))

    def diff_strings(self, a, b):
        output = []
        matcher = difflib.SequenceMatcher(None, a, b)
        for opcode, a0, a1, b0, b1 in matcher.get_opcodes():
            if opcode == "equal":
                output.append(a[a0:a1])
            elif opcode == "insert":
                output.append(color(b[b0:b1], fg=16, bg="green"))
            elif opcode == "delete":
                output.append(color(a[a0:a1], fg=16, bg="red"))
            elif opcode == "replace":
                output.append(color(b[b0:b1], fg=16, bg="green"))
                output.append(color(a[a0:a1], fg=16, bg="red"))
        return "".join(output)


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
