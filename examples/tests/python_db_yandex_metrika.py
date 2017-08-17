from db_test import adapter

from comagic_asi.sync_worker.model import model


class Test(adapter.Adapter):
    def init_db(self):
        connection_str = ("postgres://%(user)s@%(host)s:%(port)s/%(db_name)s" %
            {'user': 'postgres',
             'host': self.creds['host'],
             'port': self.creds['port'],
             # choose only first, becuase we create only comagic_* db
             'db_name': self.creds['db_names'][0],
             }
        )
        self.m = model.Model(max_conn=1, connection_string=connection_str)

    def assertRecords(self, expected, actual):
        assert len(expected) == len(actual), ("Length for expected %s is not "
                                              "equal to actual %s" %
                                              (len(expected), len(actual)))
        formatted_actual = [
                {k: getattr(val, k)  for k in val._fields}
                for val in actual
        ]
        assert expected == formatted_actual, ("Expected:\n %s\ndoes not match "
                                              "Actual:\n %s" %
                                              (expected, formatted_actual))

    def test_get_yandex_metrika_clients_no_params(self):
        expected = [
            {'site_id': 2400, 'app_id': 1103, 'access_token': 'auth1',
             'counter_id': 7766, 'counter_ext_id': '36790255'},
            {'site_id': 3479, 'app_id': 1103, 'access_token': 'auth2',
             'counter_id': 6250, 'counter_ext_id': '29393210'},
            {'site_id': 23711, 'app_id': 1103, 'access_token': 'auth3',
             'counter_id': 6785, 'counter_ext_id': '44632042'},
            {'site_id': 2398, 'app_id': 1103, 'access_token': 'auth4',
             'counter_id': 5846, 'counter_ext_id': '29094985'},
            {'site_id': 22169, 'app_id': 1103, 'access_token': 'auth4',
             'counter_id': 5847, 'counter_ext_id': '29094985'},
            {'site_id': 26838, 'app_id': 1103, 'access_token': 'auth5',
             'counter_id': 7525, 'counter_ext_id': '45356724'},
            {'site_id': 4946, 'app_id': 1103, 'access_token': 'auth6',
             'counter_id': 7083, 'counter_ext_id': '43993829'},
            {'site_id': 25187, 'app_id': 1103, 'access_token': 'auth6',
             'counter_id': 7869, 'counter_ext_id': '43993829'}
        ]
        res = self.m.get_ym_clients()
        self.assertRecords(expected, res)

    def test_get_yandex_metrika_clients_with_params1(self):
        expected = [
            {'site_id': 25187, 'app_id': 1103, 'access_token': 'auth6',
             'counter_id': 7869, 'counter_ext_id': '43993829'}
        ]
        params = {
            'app_id': 1103,
            'site_id': 25187
        }
        res = self.m.get_ym_clients(**params)
        self.assertRecords(expected, res)

    def test_get_yandex_metrika_clients_with_params2(self):
        expected = [
            {'site_id': 2400, 'app_id': 1103, 'access_token': 'auth1',
             'counter_id': 7766, 'counter_ext_id': '36790255'}
        ]
        params = {
            'app_id': 1103,
            'site_id': 2400
        }
        res = self.m.get_ym_clients(**params)
        self.assertRecords(expected, res)

    def test_get_yandex_metrika_clients_no_data(self):
        expected = []
        params = {
            'app_id': 777,
            'site_id': 777
        }
        res = self.m.get_ym_clients(**params)
        self.assertEqual(expected, res)
