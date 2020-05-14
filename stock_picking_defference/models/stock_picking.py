# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"

    diff_move_ids = fields.One2many('stock.move', compute="_compute_diff_move_ids", string='Operations')

    def _compute_diff_move_ids(self):
        for picking in self:
            if len(picking.move_lines.ids) > 0:
                #diff_move_line_ids = self.env['stock.move'].search([])
                diff_move_line_ids = False
                for move_line in picking.move_lines:
                    qty_done = sum(picking.move_line_ids.filtered(lambda r: r.product_id == move_line.product_id).mapped('qty_done'))
                    #if qty_done != move_line.product_uom_qty:
                    move_line.diff_product_uom_qty = move_line.product_uom_qty - qty_done
                    if not diff_move_line_ids:
                        diff_move_line_ids = move_line
                    diff_move_line_ids |= move_line
                _logger.info("MOVES %s" % diff_move_line_ids)
                picking.diff_move_line_ids = diff_move_line_ids
            else:
                picking.diff_move_line_ids = False
