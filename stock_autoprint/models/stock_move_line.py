# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    split_line = fields.Boolean('Splited', readonly=True)
    split_lot_id = fields.Many2one('stock.production.lot', 'Holded Lot for split')
    has_tracking = fields.Selection(related='product_id.tracking', string='Product with Tracking')
    package_qty = fields.Integer('Qty packages', default=1, copy=False)
