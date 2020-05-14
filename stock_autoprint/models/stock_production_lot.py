# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from itertools import *
from operator import itemgetter

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductionLot(models.Model):
    _inherit = "stock.production.lot"

    split_lot_id = fields.Many2one('stock.production.lot', 'Holded Lot for split')
    range_start = fields.Integer("First range number")
    range_qty = fields.Integer("Quantity per range")
    tracking = fields.Selection(related='product_id.tracking', string='Product Tracking type')

    @api.onchange('ref')
    def onchange_ref(self):
        if self.tracking == 'serialrange':
            sn = ''.join(re.findall(r'\d+', self.ref))
            sn = sn.lstrip("0")
            self.range_start = int(sn)

    @api.multi
    def write(self, vals):
        res = super(ProductionLot, self).write(vals)
        self.ensure_one()
        if not self._context.get('block_ranges', False) and 'range_qty' in vals and self.tracking == 'serialrange':
            ctx = self._context.copy()
            ctx.update(dict(block_ranges=True))
            for x in range(1, vals['range_qty']):
                next_lot = self.default_get(['name'])
                next_lot.update({'product_id': self.product_id.id, 'product_uom_id': self.product_uom_id.id, 
                                 'range_start': self.range_start, 'range_qty': self.range_qty, 'split_lot_id': self.split_lot_id and self.split_lot_id.id or self.id})
                self.with_context(ctx).create(next_lot)
        return res
