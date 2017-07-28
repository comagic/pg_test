# -*- coding:utf-8 -*-
import json
import copy

class Action:
    def __init__(self, test, args):
        self.test = test
        self.is_extend = False
        self.name = None
        self.ext = None
        self._d = self.__dict__
        self._d.update(args)

    def extend(self):
        if self.is_extend:
            return
        self.is_extend = True
        if not self.ext:
            return
        c = self.test.exts.get(self.ext)
        if not c:
            raise Exception('ext %s is not defined' % self.ext)
        c.extend()
        self._d.update(dict(copy.deepcopy(c._d), **self._d))

    def calculate_fields(self):
        self.calculate_action_time()
        if 'calc_fields' not in self._d:
            return
        for f in self.calc_fields.keys():
            self.calculate_field(f)

    def calculate_field(self, field):
        if field not in self.calc_fields:
            return
        f = self.calc_fields[field]
        for i in f.get('depend_fields') or []:
            self.calculate_field(i)
        if f['type'] == 'alias':
            self.calculate_field(f['original_field'])
            self._d[field] = self._d.get(f['original_field'])

        elif f['type'] == 'json_str':
            for i in f['items']:
                self.calculate_field(i)
            self._d[field] = json.dumps({i: self._d.get(i) for i in f['items']})

        elif f['type'] == 'eval':
            self._d[field] = eval(f['cmd'], dict(globals(), **self._d))
        else:
            print('WARNING undefined type (%s) of calc_field' % f['type'])
        del self.calc_fields[field]

    def calculate_action_time(self):
        if 'action_datetime' not in self._d:
            if 'action_date' in self._d and 'action_time' in self._d:
                self.action_datetime = '%s %s' % (self.action_date, self.action_time)
            else:
                self.action_datetime = None

    def run(self):
        if 'sql' in self.__dict__:
            try:
                self.test.dbms.sql_execute(self.database, self.sql, **self.__dict__)
            except Exception as e:
                pass
        if 'check_sql' in self.__dict__:
            try:
                res = self.test.dbms.sql_execute(self.check_database, self.check_sql, **self.__dict__)
                if res and res[0]['result'] == True:
                    return 'green|Ok'
                return 'red|Fail'
            except Exception as e:
                if self.test.is_debug:
                    self.test.log('red|Exception %s: %s', e.__class__.__name__, e)
                return 'red|Exception'
