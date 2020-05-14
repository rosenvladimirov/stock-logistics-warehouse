# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = ['res.config.settings']

    type_package_female = fields.Float(related="company_id.type_package_female")
    type_package_male = fields.Float(related="company_id.type_package_male")
