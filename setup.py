import sys

from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand

PACKAGE_TYPE = 'pg-tools'
PACKAGE_NAME = 'db-test'
PACKAGE_DESC = 'simple test framework for postgresql'
PACKAGE_LONG_DESC = 'Test framework for postgresql database (pg-export format)'


class PyTest(TestCommand):

    user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]

    def initialize_options(self):
        super().initialize_options()
        # default list of options for testing
        # https://docs.pytest.org/en/latest/logging.html
        self.pytest_args = (
            '--flake8 {0} tests examples '
            '--junitxml=.reports/{0}_junit.xml '
            '--cov={0} --cov=tests '
            '-p no:logging'.format(PACKAGE_NAME.replace('-', '_'))
        )

    def run_tests(self):
        import shlex
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


# Что нужно для запуска python setup.py <any_cmd>
# Используем ручной запуск с помощью класса PyTest
setup_requires = []


# Что нужно для установки
install_requires = [
    # Локальный pypi
    'pg-import>=2.0.0',
    'psycopg2',
    'datadiff'
]


# Что нужно для запуска python setup.py test
tests_require = [
    'flake8>=4,<5',
    'pytest',
    'pytest-cov',
    'pytest-flake8',
    'pytest-asyncio',
    'pytest-sugar',
    'asynctest',
]


# Скрипты
console_scripts = [
    'db_test=db_test.main:main'
]


setup(
    name=PACKAGE_NAME,
    version='0.0.0',
    description=PACKAGE_DESC,
    long_description=PACKAGE_LONG_DESC,
    url='https://git.dev.uiscom.ru/{}/{}'.format(PACKAGE_TYPE, PACKAGE_NAME),
    author="Andrey Chernyakov",
    author_email="a.chernyakov@comagic.dev",
    license="Nodefined",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Framework :: Pytest',
        'Intended Audience :: Customer Service',
        'Intended Audience :: Information Technology',
        'License :: Other/Proprietary License',
        'License :: UIS License',
        'Natural Language :: Russian',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: UIS:: Microservices',
    ],
    zip_safe=False,
    packages=find_packages(exclude=['tests', 'examples', '.reports']),
    entry_points={'console_scripts': console_scripts},
    python_requires='>=3.5',
    setup_requires=setup_requires,
    install_requires=install_requires,
    tests_require=tests_require,
    cmdclass={'test': PyTest},
)
