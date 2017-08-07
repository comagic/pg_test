# -*- coding:utf-8 -*-
from functools import reduce
import itertools
import sys
import os
import json
import atexit
from db_test.action import TestCase
from db_test.dbms import DBMS


colors = {
    'red|': '\033[1m\033[31m',
    'yellow|': '\033[33m',
    'green|': '\033[32m',
    'blue|': '\033[36m',
    'default|': '\033[0m'
}

class ProcessMixin:
    def log(self, message, *args):
        message = reduce(lambda m, color: m.replace(*color), colors.items(),
                         message % args)
        print(message + colors['default|'])


class TestRunner(ProcessMixin):
    def __init__(self, args):
        self.args = args
        self.test_dir = args.test_dir
        self.db_dirs = args.db_dirs
        self.is_debug = args.verbose
        self.save_db = args.save
        self.tests_dir = os.path.join(self.test_dir, 'tests')

        # split execution for python and for db tests
        self.db_tests = []
        self.python_tests = []

        self.tests = []
        self.exts = {}

    def prepare_db(self):
        self.dbms = DBMS(self, self.args)
        if not self.save_db:
            # TODO cleanup for DB move to upper level
            atexit.register(self.dbms.clean_all)
        self.dbms.build_db()

    def run_tests(self):
        self.log('green| DB testing')
        for s in self.tests:
            res = s.run()
            if res:
                self.log('blue| %s %s',
                          s._d.get('check_name', '<nameless>').ljust(30),
                          res)

    def validate_tests(self):
        if not self.db_tests and not self.python_tests:
            self.log("red| There is no available tests. Execution is canceled")
            sys.exit()

        for i in itertools.chain(self.db_tests, self.python_tests):
            s = TestCase(self, i)
            self.tests.append(s)

    def import_tests(self, file_name):
        try:
            test_file = __import__(file_name)
        except Exception as e:
            self.log("red| Can't load file: %s", file_name)
            raise
        if hasattr(test_file, 'db_tests'):
            self.db_tests.extend(test_file.db_tests)
        if hasattr(test_file, 'python_tests'):
            self.python_tests.extend(test_file.python_tests)

    def load_tests(self):
        ''' Parse Tests from specified directory '''
        sys.path.append(self.tests_dir)
        self.log("green| Loading tests from: %s", self.tests_dir)
        for root, dirs, files in os.walk(self.tests_dir):
            for f in files:
                try:
                    f_name, ext = f.rsplit('.', 1)
                except ValueError as e:
                    self.log("red| Failed to parse file name %s: %s" %
                             (f_name, e))
                if ext == 'py':
                    self.import_tests(f_name)
        self.validate_tests()
