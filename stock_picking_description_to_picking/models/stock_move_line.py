# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    ref_description = fields.Text(string='Ref Description', compute="_compute_ref_description")

    @api.depends('move_id.purchase_line_id')
    def _compute_ref_description(self):
        for record in self:
            record.ref_description = record.move_id.purchase_line_id.name
