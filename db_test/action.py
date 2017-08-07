# -*- coding:utf-8 -*-
import json
import copy


class ValidateMixin:

    def validate(self):
        ''' Validate test schema difinition '''
        pass

    def parent(self):
        ''' Process test_case with parent option '''
        pass


class TestCase(ValidateMixin):
    def __init__(self, test, args):
        self.test = test
        self.name = None
        self.validate()

    def run(self):
        if 'sql' in self.__dict__:
            try:
                self.test.dbms.sql_execute(self.database, self.sql,
                                           **self.__dict__)
            except Exception as e:
                pass
        if 'check_sql' in self.__dict__:
            try:
                res = self.test.dbms.sql_execute(
                    self.check_database, self.check_sql, **self.__dict__)
                if res and res[0]['result'] == True:
                    return 'green| Ok'
                return 'red| Fail'
            except Exception as e:
                if self.test.is_debug:
                    self.test.log('red| Exception %s: %s',
                                  e.__class__.__name__, e)
                return 'red| Exception'
