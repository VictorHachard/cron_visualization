# -*- coding: utf-8 -*-
{
    'name': "Cron Visualization",
    'summary': "Enhances the cron view.",
    'description': """Cron Visualization is a module that allows you to visualize the cron jobs that are running in your Odoo instance.""",
    'category': 'Technical',
    'version': '0.0.1',
    'author': "Victor",
    'license': 'OPL-1',
    'price': 0,
    'currency': 'EUR',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',

        'views/cv_ir_cron_history.xml',
        'views/ir_cron.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'cron_visualization/static/src/*/*.scss',
            'cron_visualization/static/src/*/*.xml',
            'cron_visualization/static/src/*/*.js',
        ]
    },
    'installable': True,
    'application': False,
}
