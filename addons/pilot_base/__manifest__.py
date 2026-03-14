{
    'name': 'Pilot Base',
    'version': '17.0.1.0.0',
    'summary': 'Módulo base de OdooCodePilot',
    'category': 'Custom',
    'author': 'Nayeli',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/pilot_registro_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}