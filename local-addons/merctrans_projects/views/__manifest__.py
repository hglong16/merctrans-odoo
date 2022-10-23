# -*- coding: utf-8 -*-
{
    'name':
    "merctrans_projects",
    'summary':
    """
        To manage MercTrans Localization Projects""",
    'description':
    """
        To manage MercTrans Localization Projects 
    """,
    'sequence':
    -100,
    'author':
    "The Merc",
    'website':
    "https://merctrans.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category':
    'Uncategorized',
    'version':
    '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/projects_menus.xml',
        'views/templates.xml',
        'views/sale.xml',
        'views/po.xml',
        'data/automation.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
