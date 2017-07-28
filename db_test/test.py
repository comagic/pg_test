# -*- coding:utf-8 -*-
from functools import reduce
import sys
import os
import json
import atexit
from db_test.action import Action
from db_test.dbms import DBMS


colors = {
    'red|': '\033[1m\033[31m',
    'yellow|': '\033[33m',
    'green|': '\033[32m',
    'blue|': '\033[36m',
    'default|': '\033[0m'
}

class Test:
    def __init__(self, args):
        self.args = args
        self.test_dir = args.test_dir
        self.db_dirs = args.db_dirs
        self.is_debug = args.verbose
        self.save_db = args.save
        self.acts_dir = os.path.join(self.test_dir, 'action')

        self.json_items = []
        self.actions = []
        self.exts = {}

    def load_acts(self):
        ''' Parse Actions/Tests from specified  directory '''
        sys.path.append(self.acts_dir)
        for root, dirs, files in os.walk(self.acts_dir):
            for f in files:
                try:
                    f_name, ext = f.rsplit('.', 1)
                except ValueError as e:
                    print("Error: failed to parse file name %s: %s" %
                          (f_name, e))
                if ext == 'py':
                    self.load_file(f_name)
        self.post_loading()

    def init_dbms(self):
        self.dbms = DBMS(self, self.args)
        if not self.save_db:
            # TODO cleanup for DB move to upper level
            atexit.register(self.dbms.clean_all)

    def build_db(self):
        self.dbms.build_db()
        self.dbms.bind_dbs()

    def do_acts(self):
        self.log('green|DB testing')
        for a in self.actions:
            res = a.run()
            if res:
                self.log('blue|%s %s %s', a.action_datetime, a._d.get('check_name', '<nameless>').ljust(30), res)

    def log(self, message, *args):
        message = reduce(lambda m, color: m.replace(*color), colors.items(), message % args)
        print(message + colors['default|'])

    def load_file(self, file_name):
        try:
            self.json_items.extend(__import__(file_name).acts)
        except Exception as e:
            self.log('red|Cant load file: %s', file_name)
            raise

    def post_loading(self):
        for i in self.json_items:
            a = Action(self, i)
            self.actions.append(a)
            if a.name:
                self.exts[a.name] = a

        for a in self.actions:
            a.extend()
        for a in self.actions:
            a.calculate_fields()
        self.actions = sorted([a for a in self.actions if a.action_datetime], key=lambda x: x.action_datetime)
