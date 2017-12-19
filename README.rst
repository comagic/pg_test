=========================
Tool for testing db stuff
=========================

db_test is a tool for testing DB, DB methods and DB methods from python code.

Sections
--------

- `Introduction`_
- `How to start`_
- `Local testing with Docker`_
- `CLI commands`_
- `Test Case Definition`_
- `Test case extras`_
- `Inheritance`_
- `Run python DB tests`_
- `Known issues`_

Introduction
------------

db_test CLI tool allows to run test against some db.

How it works:

- loads files with test scenarios and validate them
- create DB from repository with DB files
- run tests against created DB

Also please read `Known issues`_ section before the start.

How to start
------------

Optionally prepare *virtualenv* for isolated test environment or install
dependencies to root system.
**NOTE: tool requires installed python3.5 

.. code-block:: bash

    sudo apt-get install virtualenv
    virtualenv test_db --python python3.5
    source test_db/bin/activate

Install dependencies and db_test:

.. code-block:: bash

    git clone git@git.dev.uiscom.ru:tools/pg_import.git
    cd pg_import
    # Use the following workaround for now. It will be merged in master soon.
    # Manually Apply diff from https://git.dev.uiscom.ru/tools/pg_import/merge_requests/1
    # git fetch origin
    # git checkout -b fixes origin/fixes
    pip install -e .
    cd ..
    git clone git@git.dev.uiscom.ru:tools/db_test.git
    cd db_test
    pip install -r requirements.txt
    pip install -e .


Check that necessary tools were installed. Execute the following commands:

.. code-block:: bash

    db_test --help
    pg_import --help

After installation, tests can be run from examples directory on local machine
by using Postgress cluster installed in Docker or on some remote Postgress
cluster. The section below describes preparation steps for creating and running
docker container locally. In case if you plan to use some other Posgres cluster,
it can be skipped.

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


Clone source code of repository with DB to *comagic_db* directory. 
It's necessary for correct work of the following command!

Then run examples from **db_test** repository with command:

.. code-block:: bash

   # DB directory have to be pre-created and placed to *comgic_db* directory as
   # mentioned above
   db_test -u -t examples/ -d comagic:../comagic_db -h localhost -p 5432


**NOTE: running python (service) related tests requires installed service and
its components. For example execution scenarios in file:
*examples/tests/python/python_db_yandex_metrika.py* requires installed
*comagic_asi*. If you want run only pure db tests, then remove or move out
all data from *examples/tests/python/* directory.

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

Where "data" contains subdirectories with name equals *db_name* specified via
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
   Defines 'sql' request for checking request specified in section *sql*.

- params
   List of paramaters which will be inserted in the "sql" request.

- parent
   In case, when some test has the same sql request but with different
   parameters this section can be used for minimization copy-paste. Using this
   option will create new test with copy of parameters from parent test case.
   **NOTE**: *parent* now supports several levels of inheritance. See details
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

Using **parent** option allows to *copy-paste* some options from test specified
in this option. *db_test* allows to have deep inheritance, when A is a parent
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
- **test_name3** will use *params* from **test_name2**.
- **test_name2** will use *sql* from **test_name1**.
- All tests except **test_name1** will use *db* mentioned in **test_name1**.

Run python DB tests
-------------------

Different services have different approaches to work with DB:

- Use different paramaters for initialization
- Use synchronous and asynchronous methods
- May requires different way for initialization

In light of issues mentioned above common implementation of tests is not
possible. So the alternative solution is implementation plug-in approach, which
is described below.

**db_test** runs python tests from the *\*.py* files. These tests have big
differnece with db tests, but similar on classic Python unittests.

Rules for writing python DB tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- *__init__* method can be overwritten only if new will call parent
  *__init__* method. Also new *__init__* have to expects first positional
  parameter for getting dict with *db_credentials* from test runner methods.

- Tests should be groupped in Test class inherited from **Adapter** class,
  which is available in **db_test** repository.

- Test class should contains method **init_db** with logic for initialization
  class DB class, i.e. class with contains methods for communication with DB.

- **Adapter** class contains one attribute: *self.creds*, which have to be
  used for initializationg Db class. It includes the following options:
  * 'host' - host with test DB
  * 'port' - port with test DB
  * 'db_names' - name of test DB
  By default DB has a "user" **postgres** with empty password.

- All real tests have to have prefix **test_**. All other methods without
  prefix**db_test** will be ignored by **test_** as support methods.

- For check purposes all methods have to use **assert** commands with
  description of error, otherwise test will fail without error message.

- All custom checks should contains *asserts* with error messages.

- Adapter also provides build-in checks with defined error message:
  * self.assertEqual(expected, actual), which simply compare values.


Example below demonstrates all rules mentioned before.

.. code-block:: python

    from db_test import adapter
    from comagic_asi.sync_worker.model import model

    class Test(adapter.Adapter):
        def init_db(self):
            connection_str = (
                "postgres://%(user)s@%(host)s:%(port)s/%(db_name)s" %
                {'user': 'postgres',
                 'host': self.creds['host'],
                 'port': self.creds['port'],
                 # choose only first, becuase we create only comagic_* db
                 'db_name': self.creds['db_names'][0],
                 }
            )
            self.m = model.Model(max_conn=1, connection_string=connection_str)

        def assertRecords(self, expected, actual):
            assert len(expected) == len(actual), (
                "Length for expected %s is not equal to actual %s" %
                (len(expected), len(actual)))
            formatted_actual = [
                    {k: getattr(val, k)  for k in val._fields}
                    for val in actual
            ]
            assert expected == formatted_actual, (
                "Expected:\n %s\ndoes not match Actual:\n %s" %
                (expected, formatted_actual))

        def test_get_yandex_metrika_clients_with_params(self):
            expected = [
                {'site_id': 2400, 'app_id': 1103, 'access_token': 'auth1',
                 'counter_id': 7766, 'counter_ext_id': '36790255'}
            ]
            params = {
                'app_id': 1103,
                'site_id': 2400
            }
            res = self.m.get_ym_clients(**params)
            # custom assert method
            self.assertRecords(expected, res)

        def test_get_yandex_metrika_clients_no_data(self):
            expected = []
            params = {
                'app_id': 777,
                'site_id': 777
            }
            res = self.m.get_ym_clients(**params)
            # build-in assert method
            self.assertEqual(expected, res)


Known issues
------------

1. pg_import by default does not have one required patch:
   https://git.dev.uiscom.ru/tools/pg_import/merge_requests/1
   So it have to be installed manually.
2. Some preparation steps are done by docker scripts and have to updated
   according new roles in DB. (It requires re-bulding docker image)
3. pg_import wrongly translate *AS* word in data/public/country.sql file.
   To fix it change it to *as* in your repository.
4. File schema/amocrm/tables/account.sql contains wrong line about unknown
   table *amocrm*. It have to be replaced on:

5. Running python tests, requires installation of corresponding service and
   its dependencies, otherwise it leads to some errors during importing Model
   class and python DB methods.
