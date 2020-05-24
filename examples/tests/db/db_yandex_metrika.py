from datetime import datetime


tests = [
    ('test_get_yandex_metrika_clients_with_params1', {
        'parent': 'test_get_yandex_metrika_clients_no_params',
        'sql': '''select *
                    from ppc.get_yandex_metrika_clients(%(app_id)s,
                                                        %(site_id)s)''',
        'params': {
            'app_id': 1103,
            'site_id': 25187
        },
        'result': [
            {
                'site_id': 25187,
                'app_id': 1103,
                'access_token': 'auth6',
                'counter_id': 7869,
                'counter_ext_id': '43993829'
            }
        ]
    }),
    ('test_get_yandex_metrika_clients_with_params2', {
        'parent': 'test_get_yandex_metrika_clients_with_params1',
        'params': {
            'app_id': 1103,
            'site_id': 2400
        },
        'result': [
            {
                'site_id': 2400,
                'app_id': 1103,
                'access_token': 'auth1',
                'counter_id': 7766,
                'counter_ext_id': '36790255'
            }
        ]
    }),
    ('test_get_yandex_metrika_clients_no_data', {
        'parent': 'test_get_yandex_metrika_clients_with_params2',
        'params': {
            'app_id': 777,
            'site_id': 777
        },
        'result': None
    }),
    ('test_get_yandex_metrika_clients_no_params', {
        'db': 'comagic',
        'sql': "select * from ppc.get_yandex_metrika_clients()",
        'result': [
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
    }),
    ('test_get_ym_call_data', {
        'db': 'comagic',
        'sql': '''select *
                    from ppc.get_ym_call_data(%(app_id)s,
                                              %(site_id)s,
                                              %(report_dates)s)''',
        'params': {
            'app_id': 1103,
            'site_id': 2400,
            'report_dates': [datetime(2011, 1, 1), datetime(2011, 1, 2)]
        },
        'result': [{'get_ym_call_data': None}]
    }),
    ('test_get_yandex_metrika_session_None', {
        'db': 'comagic',
        'sql': ("select * from ppc.get_yandex_metrika_session("
                "           %(app_id)s, %(site_id)s, %(start_time)s, "
                "           %(url)s, %(screen)s)"),
        'params': {
            'app_id': 1103,
            'site_id': 2400,
            'start_time': datetime(2017, 1, 1),
            'url': "http//test.com",
            'screen': "100x200"
        },
        'result': None
    }),
]
