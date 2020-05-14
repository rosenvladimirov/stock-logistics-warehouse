# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import os

from odoo import api, fields, models, tools, _
from lxml import etree


class Company(models.Model):
    _inherit = "res.company"

    type_package_female = fields.Float('Max weight')
    type_package_male = fields.Float('Max weight')

    def __init__(self, pool, cr):
        cr.execute("SELECT column_name FROM information_schema.columns "
                   "WHERE table_name = 'res_company' AND column_name = 'type_package_female'")
        if not cr.fetchone():
            cr.execute('ALTER TABLE res_company '
                       'ADD COLUMN type_package_female float;')
        cr.execute("SELECT column_name FROM information_schema.columns "
                   "WHERE table_name = 'res_company' AND column_name = 'type_package_male'")
        if not cr.fetchone():
            cr.execute('ALTER TABLE res_company '
                       'ADD COLUMN type_package_male float;')
        return super(Company, self).__init__(pool, cr)
