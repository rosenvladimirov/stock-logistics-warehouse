# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    auto_packing = fields.Boolean("Auto packing label", help="Set up if needed to create package when use in pickings. For example when use the box in BOM the picking movement will be generate new package label.")
    tracking = fields.Selection(selection_add=[('serialrange', 'By Unique Serial Number Ranges')])
