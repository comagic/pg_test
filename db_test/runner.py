# -*- coding:utf-8 -*-
import atexit
from functools import reduce
import importlib
import inspect
import os
import sys

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
        self.test_dir = args.test_dir
        self.db_dirs = args.db_dirs
        self.verbose = args.verbose
        self.keep = args.keep
        self.break_on_test = args.break_on_test
        self.dbms = DBMS(self.log, args)

        # All tests in one variable
        self.tests = []
        # Separate variable for runned tests
        self.validated_tests = []
        self.exts = {}
        self.python_tests = []
        self.python_validated_tests = []
        self.failed_count = 0

    def prepare_db(self):
        if not self.keep:
            atexit.register(self.dbms.clean_all)
        self.dbms.build_db()

    def run_tests(self):
        if self.validated_tests:
            self.log('green|Run DB tests:')
        for t in self.validated_tests:
            if t.data['id'] == self.break_on_test:
                self.log('green|break on <%s>', self.break_on_test)
                break
            result = t.run()
            self.failed_count += int(not result.startswith('green| Passed'))
            if self.verbose or result.startswith('green| Passed'):
                self.log("blue|  %s %s", t.name, result)
            else:
                self.log("blue|  %s| red| Failed", t.name)

        if self.failed_count != 0:
            self.log("red|%s tests failed", self.failed_count)
            if not self.verbose:
                self.log("red|  use -v (--verbose) for more details")
        else:
            self.log("green|all tests passed")

        if self.python_validated_tests:
            self.log('green|Run python-DB tests:')
        for pt in self.python_validated_tests:
            pt.run()
        return int(self.failed_count != 0)

    def validate_tests(self):
        if not self.tests and not self.python_tests:
            self.log("red|  There is no available tests. "
                     "Execution is canceled")
            sys.exit(2)

        _validator = validator.Validator(self.tests)
        ok_tests, failed_tests = _validator.validate()
        for t_name, errs in failed_tests:
            errs_msg = '\n - '.join(errs)
            self.log("%s red|:\n - %s" % (t_name, errs_msg))

        if not ok_tests:
            self.log("red| Error:  There is no correctly defined tests. "
                     "Execution is canceled.")
            sys.exit(2)

        # sort by name to make tests order predicted
        for t_name, t_data in sorted(ok_tests, key=lambda x: x[1]['id']):
            t = tts.DBTest(t_name, t_data, self.dbms)
            self.validated_tests.append(t)

        for pt in self.python_tests:
            self.python_validated_tests.append(
                tts.PythonTests(pt, self.dbms, self.log))

    def import_tests(self, directory_name, file_name):
        try:
            if directory_name not in sys.path:
                sys.path.append(directory_name)
            test_file = importlib.import_module(file_name)
        except Exception:
            self.log("red|  Can't load file: %s", file_name)
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
        self.log("green|Loading tests from: %s", tests_dir)
        for root, dirs, files in os.walk(tests_dir):
            for f in files:
                try:
                    f_name, ext = f.rsplit('.', 1)
                except ValueError as e:
                    self.log("red|  Failed to parse file name %s: %s" %
                             (f_name, e))
                if ext == 'py':
                    self.import_tests(root, f_name)
        self.validate_tests()
