tests = [
    ('test_country_code', {
        'db': 'comagic',
        'sql': "select * from public.country where id=%(_id)s",
        'params': {
            '_id': 'AR'
        },
        'result': [
            {
                'iso': '032',
                'full_name': 'Аргентинская Республика',
                'name': 'Аргентина',
                'en_name': 'Argentina',
                'id': 'AR',
                'alpha3': 'ARG'
            }
        ]
    }),
    ('test_country_code2', {
        'parent': 'test_country_code',
        'params': {
            '_id': 'AZ'
        },
        'result': [
            {
                'iso': '031',
                'id': 'AZ',
                'en_name': 'Azerbaijan',
                'alpha3': 'AZE',
                'full_name': 'Республика Азербайджан',
                'name': 'Азербайджан'
            }
        ]
    }),
    ('test_ac_parameter', {
        'db': 'comagic',
        'sql': "select * from analytics.ac_parameter where id='city'",
        'result': [
            {
                'name': 'Город',
                'ac_parameter_group_id': 3,
                'help_text': None,
                'type': None,
                'id': 'city',
                'weight': 5
            }
        ]
    }),
    ('test_ppc_region_upload', {
        'db': 'comagic',
        'sql': '''insert into ppc.region (id, ext_id, name)
                    values (42, 4242, 'Test region')''',
        'check_sql': "select * from ppc.region where id = 42",
        'result': [
            {
                'name': 'Test region',
                'parent_ext_id': None,
                'id': 42,
                'type': None,
                'ext_id': 4242
            }
        ],
        'cleanup': "delete from ppc.region where id = 42",
    })
]
