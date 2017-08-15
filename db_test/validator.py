import copy
from importlib import import_module
from inspect import getargspec


class TestKey:
    def __init__(self, name, _type=str, required=False, check=None):
        self.name = name
        self._type = _type
        self.required = required
        self.check = check

    def custom_check(self, cls_inst, **kwargs):
        if self.check:
            check_method = getattr(cls_inst, self.check)
            check_method(**kwargs)


schema = [
    TestKey('sql', required=True),
    TestKey('result', required=True, _type='any'),
    TestKey('db', required=True),
    TestKey('check_sql'),
    TestKey('params', _type=dict, check='params_check'),
    TestKey('cleanup'),
    TestKey('parent', check='parent_check'),
]


class Validator:

    def __init__(self, tests):
        self.tests = dict(tests)
        if len(self.tests) != len(tests):
            raise Exception("There are name duplications in tests defintions")
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
            for key in (k for k in schema if k.required):
                if key.name not in test_data:
                    errs.append("Required key '%s' is not defined" % key.name)

        # check types of keys
        for key in schema:
            if test_data.get(key.name):
                if (key._type != type(test_data.get(key.name))
                        and key._type != 'any'):
                    errs.append(
                        "Type of the key '%s' is incorrect. Expected - %s, "
                        "actual - %s" % (key.name, key._type,
                                         type(test_data[key.name]))
                    )

        # check unkonown keys in test definition
        schema_keys = [k.name for k in schema]
        for key in test_data.keys():
            if key not in schema_keys:
                errs.append(
                    "Key '%s' is unknown. It will be ignored." % key
                )

        # run custom checks
        for key in schema:
            if key.name in test_data.keys():
                key.custom_check(self,
                                 name=test_name,
                                 data=test_data,
                                 errs=errs)
        return errs

    def params_check(self, name, data, errs):
        params = data.get('params')
        if 'sql' in data:
            try:
                data['sql'] % params
            except TypeError:
                errs.append(
                    "'params' can be substituted to the 'sql' command."
                )

    # TODO add support for multi inheritance with removing parent name
    def parent_check(self, name, data, errs):
        parent = data.get('parent')
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
