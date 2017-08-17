class Adapter:
    def __init__(self, credentials, *args, **kwargs):
        self.creds = credentials
        self.init_db()

    def init_db(self):
        assert False, ('init_db method have to be overwritten for %s' %
                       self.__class__)

    def assertEqual(self, expected, actual):
        assert expected == actual, ("Expected:\n %s \n\n does not match "
                                    "Actual:\n %s" % (expected, actual))
