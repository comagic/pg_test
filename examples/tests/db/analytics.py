import json


tests = [
    ('test_get_events', {
        'db': 'comagic',
        'sql': '''select *
                    from analytics.get_events(%(app_id)s,
                                              %(site_id)s,
                                              %(engine)s)''',
        'params': {
            'app_id': 1103,
            'site_id': 25187,
            'engine': 'yandex.metrika'
        },
        'result': None
    }),
    ('test_get_events_google', {
        'parent': 'test_get_events',
        'params': {
            'app_id': 1103,
            'site_id': 25187,
            'engine': 'google.analytics'
        },
        'result': None
    }),
    # TODO Fix this test to push and check correct data!!
    ('test_load_event_stat', {
        'db': 'comagic',
        'sql': '''select ppc.load_event_stat(%(app_id)s,
                                             %(site_id)s,
                                             %(engine)s,
                                              %(data)s)''',
        'params': {
            'app_id': 1103,
            'site_id': 25187,
            'engine': 'yandex.direct',
            'data': json.dumps([{'TEST': 111}])
        },
        'check_sql': 'select * from analytics.event_log',
        'result': None
    }),
]
