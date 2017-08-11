Tool for testing db stuff
=========================

db_test is a tool for testing DB, DB methods and DB methods from python code.

Introduction
------------

db_test CLI tool allows to run test against some db.

How it works:
- loads files with test scenarios and validate them
- create DB from repository with DB files
- run tests against created DB

CLI commands
------------

The follow block demostrate output of CLI "help" command.

.. code-block::

    db_test [--help] [-v] -d db_name:db_dir -t test_dir -h HOST -p PORT
                   [-s] [-u]

    Run test

    optional arguments:
      --help                show this help message and exit
      -v, --verbose         verbose message
      -d db_name:db_dir     directory with db (made by pg_export)
      -t test_dir           directory with test definition
      -h HOST, --host HOST  host for connect db
      -p PORT, --port PORT  port for connect db
      -s, --save            do not drop database on exit
      -u, --use-docker      use docker or some other DB

NOTE: by default option "-u" is True, so it means, that script expects host and
port from postgress cluster which was run in docker.

Execution can be run by follow command from db_test repository:

.. code-block::

   db_test -t examples/ -d comagic:../comagic_db  -h localhost -p 5432

`examples` - directory contains list of tests and test data.
`comagic` - is a name of db for testing
`../comagic_db` - directory with repository of DB files


Test Case Definition
--------------------

Test directory (which you specify via "-t" option) should contains following
subdirectories:
* data
* tests

Where "data" contains subdirectories with name equals `db_name` specified via
"-d" option. These subdirectories have files with sql commands for creating
data in DB for testing. It can be some examples of real data or copy from
production DB.

"tests" contains python files with definitions of test cases in JSON format.
Test cases have to be defined as one of two allowed options:
* db_tests
* python_tests

Following example demonstrates how test definition can look:

.. code-block::

    db_tests = [
        'test_name1': {
            'db': "test_db",
            'sql': "select * from tt where id = %(p1)s and val = %(p2)s",
            'params': {
                'p1': 123,
                'p2': 321,
            },
            'result': [1,2,3],
        },
        'test_name2': {
            'parent': 'test_name1',
            'params': {
                'p1': 789,
                'p2': 111,
            },
            'result': [4,5,6],
        }
        'test_name3': {
            'db': "test_db",
            'sql': 'insert table tt v1 = %(p1)s',
            'check_sql': "select * from tt"
        }
    ]

*NOTE*: all sql commands support several selects one by one, but only result of
the last will be fetched and tested.

More examples are available in repository in directory: "examples".

Each type of test has his own schema of definition.

db_tests
~~~~~~~~

required keys:
- sql
   Defines 'sql' request for testing.

- result
   Result of execution of "sql" or "sql_check" in JSON format

- db
  Name of DB for testing, which was specified via "-d" CLI option

optional keys:
- check_sql
   Defines 'sql' request for checking request specified in section `sql`.
- params
   List of paramaters which will be inserted in the "sql" request.
- parent
   In case, when some test has the same sql request but with different
   parameters this section can be used for minimization copy-paste. Using this
   option will create new test with copy of parameters from paretn test case.
- cleanup
   Option for 'sql' request which remove data created by execution first 'sql'
   query.


python_tests
~~~~~~~~~~~~

Does not supported for now.

Local testing with Docker
-------------------------

db_test repository contains files for building Docker image with postgress
cluster. These files are available in directory scripts/docker_postgres.
To run it just execute follow commands:

.. code-block::

    docker build scripts/docker_postgres
    docker run -d -p 5432:5432 <image_id from output of previous command>

Then run examples with command:

.. code-block::

    db_test -t examples/ -d <db_name>:<directory with DB repository> -h localhost -p 5432
