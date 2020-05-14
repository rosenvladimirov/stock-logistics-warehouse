# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp


class StockMove(models.Model):
    _inherit = "stock.move"

    diff_product_uom_qty = fields.Float('Diff Initial Demand',
        digits=dp.get_precision('Product Unit of Measure'),
        default=0.0, required=True, states={'done': [('readonly', True)]})
