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

How to start
------------

Optionally prepare virtualenv for isolated test environment or install
dependencies to root system.

.. code-block:: bash

    sudo apt-get install virtualenv
    vistualenv test_db
    source test_db/bin/activate

Install dependencies and db_test:

.. code-block:: bash

    git clone git@git.dev.uiscom.ru:tools/pg_import.git
    cd pg_import
    # Manually Apply diff from https://git.dev.uiscom.ru/tools/pg_import/merge_requests/1
    pip install -e .
    cd ..
    git clone git@git.dev.uiscom.ru:tools/db_test.git
    cd db_test
    pip install -r requirements
    pip install -e .

Check that tools were installed. Execute follow commands:

.. code-block:: bash

    db_test --help
    pg_import --help

After installation, tests can be run from examples directory on local machine
by using Postgress cluster installed in Docker or on some remote Postgress
cluster. The section below describes preparation steps for creating and running
docker container locally. In case if using some other Posgres cluster, it can
be skipped.

Local testing with Docker
-------------------------

**db_test** repository contains files for building Docker image with postgress
cluster. These files are available in directory scripts/docker_postgres.
To run it just execute the following commands from **db_test** directory:

.. code-block:: bash

    # Install docker local
    # sudo apt-get install docker.io docker
    # Build docker image
    docker build scripts/docker_postgres
    docker run -d -p 5432:5432 <image_id from output of previous command>

Then run examples from **db_test** repository with command:

.. code-block:: bash

   db_test -u -t examples/ -d comagic:../comagic_db -h localhost -p 5432

Where:

- **comagic** is a name of DB for testing
- **../comagic_db** is a path to repository with DB files (data, schema, etc.)
- **localhost:5432** is a host an port of local Postrgress cluster in docker
  container
- **-u** option enables special hooks for installation DB in container

CLI commands
------------

The block below demostrates output of CLI "help" command.

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

By default script expects host and port from external postgress cluster.
To use postgress runed in local docker container add flag **-u**.

By default a temporary DB created for running tests will be deleted after
a testing. To change behavior and don't remove DB at the end, add flag **-s**.

Test Case Definition
--------------------

Test directory (which you specify via "-t" option) should contain the following
subdirectories:
* data
* tests

Where "data" contains subdirectories with name equals `db_name` specified via
"-d" option. These subdirectories have files with sql commands for creating
data in DB for testing. It can be some examples of real data or copy from
production DB.

"tests" contains python files with definitions of test cases in JSON format.
Test cases have to be defined via variable **tests**.

Following example demonstrates how test definition can look:

.. code-block:: python

    tests = [
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

**NOTE: all sql commands support several selects one by one, but only result of
the last will be fetched and tested.**

More examples are available in repository in directory: "examples".

Tests have schema of definition, which is described below.

db_tests
~~~~~~~~

required keys:

- sql
   Defines 'sql' request for testing.

- method
   *Used for tests from Python code.*
   String with full path for accesing method of class to work with DB. It has
   format: "<path_to_module_with_db_class>.<db_class>.<method_name>". For
   example: "comagic_asi.sync_worker.model.model.Model.get_ym_call_data"

**NOTE: There are to special requirements for keys mentioned above:**
  1. **sql** can be used in the same time with **method**. In this case two
     tests (with `db-` and `python-` prefixes) will be run.
  2. **params** will be used for both runned tests. So if python method gets
     some other parameters, then will be better to split test on two different
     definitions.

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

Test case extras
----------------

Some tests may require some specific data types on input. For example it can be
datetime or JSON object.
Such issues should be solved by using python libriraies. Snippet below
demostrates it:


.. code-block:: python

    import json
    import datetime

    db_tests = [
        'test_name1': {
            'db': "test_db",
            'sql': "select * from tt where start_date = %(p1)s and val = %(p2)s",
            'params': {
                'p1': datetime.datetime(1, 2, 3),
                'p2': 321,
            },
            'result': [1,2,3],
        },
        'test_name2': {
            'db': "test_db",
            'sql': "select tt.load_values(%(p1)s)",
            'check_sql': "select num from tt",
            'params': {
                'p1': json.dumps([{'num': 789}]),
            },
            'result': [789],
        }
    ]
