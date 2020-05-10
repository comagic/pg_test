import os

from distutils.core import setup

def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()

def get_packages(dirs):
    packages = []
    for dir in dirs:
        for dirpath, dirnames, filenames in os.walk(dir):
            if '__init__.py' in filenames:
                packages.append(dirpath)
    return packages

setup(name = "db_test",
      description="tool for testing DB",
      license="""uiscom license""",
      version = "3.0",
      maintainer = "Dima Beloborodov",
      maintainer_email = "d.beloborodov@ulab.ru",
      url = "http://uiscom.ru",
      scripts = ['bin/db_test'],
      packages = get_packages(['db_test']))
