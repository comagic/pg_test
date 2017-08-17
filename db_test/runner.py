# -*- coding:utf-8 -*-
from functools import reduce
import inspect
import sys
import os
import atexit
from db_test import adapter
from db_test import tests as tts
from db_test import validator
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
        self.dbms = DBMS(self, self.args)

        # All tests in one variable
        self.tests = []
        # Separate variable for runned tests
        self.validated_tests = []
        self.exts = {}
        self.python_tests = []
        self.python_validated_tests = []

    def prepare_db(self):
        if not self.save_db:
            # TODO cleanup for DB move to upper level
            atexit.register(self.dbms.clean_all)
        self.dbms.build_db()

    def run_tests(self):
        self.log('green| Run DB tests')
        for t in self.validated_tests:
            t.run()

        self.log('green| Run python-DB tests')
        for pt in self.python_validated_tests:
            pt.run()

    def validate_tests(self):
        if not self.tests and not self.python_tests:
            self.log("red| There is no available tests. Execution is canceled")
            sys.exit()

        _validator = validator.Validator(self.tests)
        ok_tests, failed_tests = _validator.validate()
        for t_name, errs in failed_tests:
            errs_msg = '\n - '.join(errs)
            self.log("%s red|:\n - %s" % (t_name, errs_msg))

        if not ok_tests:
            self.log("red| Error: There is no correctly defined tests. "
                     "Execution is canceled.")
            sys.exit()

        # sort by name to make tests order predicted
        for t_name, t_data in sorted(ok_tests, key=lambda x: x[0]):
            t = tts.DBTest(t_name, t_data, self.dbms, self.log)
            self.validated_tests.append(t)

        for pt in self.python_tests:
            self.python_validated_tests.append(
                tts.PythonTests(pt, self.dbms, self.log))

    def import_tests(self, file_name):
        try:
            test_file = __import__(file_name)
        except Exception as e:
            self.log("red| Can't load file: %s", file_name)
            raise
        self._import_db_tests(test_file)
        self._import_python_tests(test_file)

    def _import_db_tests(self, test_file):
        ''' Load db_tests from imported file '''
        if hasattr(test_file, 'tests'):
            self.tests.extend(test_file.tests)

    def _import_python_tests(self, test_file):
        ''' Load python_tests from imported file '''
        self.python_tests.extend(
            [cls[1] for cls in inspect.getmembers(test_file, inspect.isclass)
             if adapter.Adapter in cls[1].__bases__]
        )

    def load_tests(self):
        ''' Load all "*.py" files for testing '''
        tests_dir = os.path.join(self.test_dir, 'tests')
        sys.path.append(tests_dir)
        self.log("green| Loading tests from: %s", tests_dir)
        for root, dirs, files in os.walk(tests_dir):
            for f in files:
                try:
                    f_name, ext = f.rsplit('.', 1)
                except ValueError as e:
                    self.log("red| Failed to parse file name %s: %s" %
                             (f_name, e))
                if ext == 'py':
                    self.import_tests(f_name)
        self.validate_tests()
