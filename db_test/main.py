import os
import argparse
from db_test import runner


def main():
    arg_parser = argparse.ArgumentParser(
                     description='Run test',
                     epilog='Report bugs to <a.chernyakov@comagic.dev>.',
                     conflict_handler='resolve')
    arg_parser.add_argument('-v', '--verbose',
                            action='store_true',
                            help='verbose message')
    arg_parser.add_argument('-d',
                            metavar='db_name:db_dir',
                            dest='db_dirs',
                            action='append',
                            required=True,
                            help='directory with db (made by pg_export)')
    arg_parser.add_argument('-t',
                            metavar='test_dir',
                            dest='test_dir',
                            required=True,
                            help='directory with test definition')
    arg_parser.add_argument('-h', '--host',
                            required=True,
                            help='host of PostgreSQL cluster')
    arg_parser.add_argument('-p', '--port',
                            required=True,
                            help='port of PostgreSQL cluster')
    arg_parser.add_argument('-U', '--username',
                            required=False,
                            help='username for connect to PostgreSQL cluster')
    arg_parser.add_argument('-s', '--save',
                            required=False,
                            action='store_true',
                            help='do not drop database on exit')
    arg_parser.add_argument('-u', '--use-docker',
                            required=False,
                            action='store_true',
                            help='use docker or some other DB')

    args = arg_parser.parse_args()

    for d in args.db_dirs:
        d = d.split(':')[1]
        if not os.path.exists(os.path.expanduser(d)):
            arg_parser.error("can not access to db_dir '%s'" % d)

    if not os.path.exists(os.path.expanduser(args.test_dir)):
        arg_parser.error("can not access to test_dir '%s'" % args.test_dir)

    r = runner.TestRunner(args)
    r.load_tests()
    r.prepare_db()
    r.run_tests()
#   clean_all do automaticaly on exit