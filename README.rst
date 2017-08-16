=========================
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

required keys
~~~~~~~~~~~~~

- sql
   Defines 'sql' request for testing.

- result
   Result of execution of "sql" or "sql_check" in JSON format

- db
   Name of DB for testing, which was specified via "-d" CLI option

optional keys
~~~~~~~~~~~~~

- check_sql
   Defines 'sql' request for checking request specified in section `sql`.

- params
   List of paramaters which will be inserted in the "sql" request.

- parent
   In case, when some test has the same sql request but with different
   parameters this section can be used for minimization copy-paste. Using this
   option will create new test with copy of parameters from parent test case.
   **NOTE**: `parent` now supports several levels of inheritance. See details
   in **Inheritance** section.

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

    tests = [
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

Inheritance
-----------

Using **parent** option allows to `copy-paste` some options from test specified
in this option. `db_test` allows to have deep inheritance, when A is a parent
of B, B is a parent of C, etc. In such case test's options will be overwritten
in the following order:
- Options of the B test case will overwrite options of the A test case.
- Options of the C test case will overwrite options of the B test case.
- The last will be applied options of the current test case.

.. code-block:: python

    tests = [
        'test_name1': {
            'db': "test_db",
            'sql': "select * from tt where start_date = %(p1)s and val = %(p2)s",
            'params': {
                'p1': 'val1',
                'p2': 321,
            },
            'result': [1,2,3],
        },
        'test_name2': {
            'parent': 'test_name1',
            'params': {
                'p1': 789,
                'p2': 321,
            },
            'result': [789],
        },
        'test_name3': {
            'parent': 'test_name2',
            'sql': "select * from dd where key1 = %(p1)s and key2 = %(p2)s",
            'result': [111],
        },
        'test_name4': {
            'parent': 'test_name1',
        }
    ]


According example above:

- **test_name4** will run totally the same test as **test_name1**.
- **test_name3** will use `params` from **test_name2**.
- **test_name2** will use `sql` from **test_name1**.
- All tests except **test_name1** will use `db` mentioned in **test_name1**.

Run tests from python
---------------------

Different services have different approaches to work with DB:

- Use different paramaters for initialization
- Use synchronous and asynchronous methods
- May requires different way for initialization

In light of issues mentioned above common implementation of tests is not
possible. So the alternative solution is implementation plug-in approach, which
is described below.
