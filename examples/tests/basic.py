db_tests = [
    ('test_country_code', {
        'db': 'comagic',
        'sql': "select * from public.country where id=%(_id)s",
        'params': {
            '_id': 'AR'
        },
        'result': [
            {'iso': '032', 'full_name': 'Аргентинская Республика', 'name': 'Аргентина', 'en_name': 'Argentina', 'id': 'AR', 'alpha3': 'ARG'}
        ]
    }),
    ('test_country_code2', {
        'parent': 'test_country_code',
        'params': {
            '_id': 'AZ'
        },
        'result': [
            {'iso': '031', 'id': 'AZ', 'en_name': 'Azerbaijan', 'alpha3': 'AZE', 'full_name': 'Республика Азербайджан', 'name': 'Азербайджан'}
        ]
    }),
    ('test_ac_parameter', {
        'db': 'comagic',
        'sql': "select * from analytics.ac_parameter where id='city'",
        'result': [
            {'name': 'Город', 'ac_parameter_group_id': 3, 'help_text': None, 'type': None, 'id': 'city', 'weight': 5}
        ]
    })
]
