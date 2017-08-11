# -*- coding:utf-8 -*-
import json
import copy


class TestKey:
    def __init__(self, name, _type=str, required=False, custom_check=None):
        self.name = name
        self._type = _type
        self.required = required
        self.custom_check = custom_check


db_schema = [
    TestKey('sql', required=True),
    TestKey('result', required=True, _type='any'),
    TestKey('db', required=True),
    TestKey('check_sql'),
    TestKey('params', _type=dict),
    TestKey('parent', custom_check='parent_check'),
    TestKey('cleanup')
]


class Validator:

    def __init__(self, tests):
        tests_dict = dict(tests)
        if len(tests_dict) != len(tests):
            raise Exception("There are name duplications in tests files")
        self.tests = tests_dict
        self.correct_tests = []
        self.broken_tests = []

    def validate(self):
        ''' Validate test schema definition '''

        for name, test_data in self.tests.items():
            errs = self.validate_schema(name, test_data)
            if errs:
                self.broken_tests.append((name, errs))
            else:
                self.correct_tests.append((name, self.tests[name]))

        return self.correct_tests, self.broken_tests

    def validate_schema(self, test_name, test_data):
        errs = []

        # check required
        if not test_data.get('parent'):
            for key in (k for k in db_schema if k.required):
                if key.name not in test_data:
                    errs.append("Required key '%s' is not defined" % key.name)

        # check types of keys
        for key in db_schema:
            if test_data.get(key.name):
                if (key._type != type(test_data.get(key.name))
                        and key._type != 'any'):
                    errs.append(
                        "Type of the key '%s' is incorrect. Expected - %s, "
                        "actual - %s" % (key.name, key._type,
                                         type(test_data[key.name]))
                    )

        # check unkonown keys in test definition
        schema_keys = [k.name for k in db_schema]
        for key in test_data.keys():
            if key not in schema_keys:
                errs.append(
                    "Key '%s' is unknown. It will be ignored." % key
                )

        # run custom checks
        for key in db_schema:
            if key.custom_check:
                check_method = getattr(self, key.custom_check)
                check_method(test_name, test_data, errs)
        return errs

    def parent_check(self, name, data, errs):
        # check parent
        parent = data.get('parent')
        if parent:
            if parent in self.tests:
                # hidden update test according parent link
                if 'parent' in self.tests[parent]:
                    errs.append(
                        "Multi inheritance is not supported for now. "
                        "Use another parent."
                    )
                else:
                    new_data = copy.deepcopy(self.tests[parent])
                    new_data.update(data)
                    self.tests[name] = new_data
            else:
                errs.append(
                    "Parent - '%s' is not presented in list of tests." % parent
                )


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

