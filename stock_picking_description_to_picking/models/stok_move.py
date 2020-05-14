# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockMove(models.Model):
    _inherit = "stock.move"

    ref_description = fields.Text(string='Ref Description', compute="_compute_ref_description")

    @api.depends('purchase_line_id')
    def _compute_ref_description(self):
        for record in self:
            if record.purchase_line_id:
                record.ref_description = record.purchase_line_id.name
            elif record.sale_line_id:
                record.ref_description = record.sale_line_id.name
