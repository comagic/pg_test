import copy


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
    TestKey('id', required=True),
    TestKey('name', required=True),
    TestKey('sql', required=True),
    TestKey('result', required=True, _type='any'),
    TestKey('db', required=True),
    TestKey('check_sql'),
    TestKey('parent', check='parent_check'),
    TestKey('params', _type=dict, check='params_check'),
    TestKey('cleanup'),
    TestKey('expected_exception', check='expected_exception_check'),
    TestKey('description'),
]


class Validator:
    def __init__(self, tests):
        self.tests = {t['id']: t for t in tests}
        if len(self.tests) != len(tests):
            raise Exception("There are name duplications in tests defintions")
        self.correct_tests = []
        self.broken_tests = []

    def validate(self):
        ''' Validate test schema definition '''

        for test_id, test_data in self.tests.items():
            name = '%s. %s' % (test_id, test_data['name'])
            errs = self.validate_schema(name, test_data)
            if errs:
                self.broken_tests.append((name, errs))
            else:
                self.correct_tests.append((name, self.tests[test_id]))

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
                if ((key._type != 'any'
                     and not isinstance(test_data.get(key.name), key._type))):
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
        params = self.tests[data['id']].get('params')
        if 'sql' in data:
            try:
                data['sql'] % params
            except KeyError as e:
                errs.append(
                    "Parameter %s not found in params" % e
                )

    def parent_check(self, name, data, errs):
        parent = data.get('parent')
        if parent in self.tests:
            # hidden update test according parent link
            if 'parent' in self.tests[parent]:
                self.parent_check(parent, self.tests[parent], errs)
            new_data = copy.deepcopy(self.tests[parent])
            # remove parent for resolved test
            data.pop('parent')
            params = None
            if 'params' in new_data or 'params' in data:
                params = dict(new_data.get('params', {}), **data.get('params', {}))
            new_data.update(data)
            if params:
                new_data.update({'params': params})
            self.tests[data['id']] = new_data
        else:
            errs.append(
                "Parent - '%s' is not presented in list of tests." % parent
            )

    def expected_exception_check(self, name, data, errs):
        actual_data = self.tests[data['id']]
        if actual_data.get('expected_exception') and actual_data.get('check_sql'):
            errs.append(
                "You cannot use expected_exception and check_sql together."
            )
