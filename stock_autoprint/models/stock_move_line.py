# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"
    _order = "result_package_id desc, sequence, id"

    def _default_sequence(self):
        move = self.search([], limit=1, order="sequence DESC")
        return move.sequence or 0

    split_line = fields.Boolean('Splited', readonly=True)
    split_lot_id = fields.Many2one('stock.production.lot', 'Holded Lot for split')
    has_tracking = fields.Selection(related='product_id.tracking', string='Product with Tracking')
    package_qty = fields.Integer('Qty packages', default=1, copy=False)
    sequence = fields.Integer(string='Sequence', required=True, default=_default_sequence)

    def write(self, vals):
        res = super(StockMoveLine, self).write(vals)
        if vals.get('sequence', False) and not self._context.get('force_reorder', False):
            sequence = vals['sequence'] + 1
            self.with_context(dict(self._context, force_reorder=True))._reorder(sequence)
            self.sequence += 1
        return res

    def _reorder(self, sequence):
        for x in self.search([('sequence', '>', sequence)], order="sequence"):
            x.sequence = x.sequence+1
