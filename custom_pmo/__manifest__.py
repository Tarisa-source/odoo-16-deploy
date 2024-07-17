{
    'name': 'Divisi PMO',
    'version': '1.0',
    'depends': ['base', 'project', 'hr'],
    'author': 'Dian dan Tarisa',
    'data': [
        'security/pmo_security.xml',
        # views
        'views/karyawan.xml',
        'views/challenge.xml',
        'views/resigned.xml',
        'views/project_report_views.xml',
        'views/menu_item.xml',
        # security
        'security/ir.model.access.csv',
        # data
        'data/project_report_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
