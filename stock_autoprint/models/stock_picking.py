# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from itertools import *
from operator import itemgetter

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

import logging
_logger = logging.getLogger(__name__)

class Picking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def write(self, vals):
        res = super(Picking, self).write(vals)
        for record in self:
            all_done = len([x.id for x in record.move_line_ids]) > 0 and len([x.id for x in record.move_line_ids if x.qty_done > 0]) == len([x.id for x in record.move_line_ids])
            if record.state == 'assigned' and all_done:
                record.action_package_glabel_print()
        return res

    @api.one
    def _get_serial_ranges(self, sn_now):
        range_first = False
        range_last = False
        sn_now = sn_now and ''.join(re.findall(r'\d+', sn_now))
        sn_now = sn_now and int(sn_now.lstrip("0"))
        sn_ranges = []
        sn_names = {}
        for move in self.move_line_ids:
            #_logger.info("Serial --> %s:%s:%s:%s" % (move.has_tracking, move, move.lot_id and move.lot_id.name or '', self))
            if move.has_tracking == 'serialrange' and move.lot_id and move.lot_id.name:
                sn = ''.join(re.findall(r'\d+', move.lot_id.name))
                sn = sn.lstrip("0")
                sn_ref = move.lot_id.ref and ''.join(re.findall(r'\d+', move.lot_id.ref)) or False
                sn_ref = sn_ref and sn_ref.lstrip("0") or False
                sn_ranges.append({'move_line': move, 'sn': int(sn), 'ref_sn': sn_ref and int(sn_ref) or False})
                sn_names[int(sn)] = move.lot_id.name

        if sn_ranges:
            #_logger.info("Move line %s" % (sn_ranges))
            sn_final_ranges = [x['sn'] for x in sn_ranges]
            sn_final_ranges.sort()
            #_logger.info("SN: %s:%s" % (sn_final_ranges, sn_final_ranges.sort()))
            groups = [list(map(itemgetter(1), g)) for k, g in groupby(enumerate(sn_final_ranges), lambda x: x[0]-x[1])]
            #_logger.info("Separated %s:%s" % (sn_now, groups))
            for group in groups:
                _logger.info("Group %s:%s" % (group, sn_now in group))
                if sn_now in group:
                    range_first = sn_names[min(group)]
                    range_last = sn_names[max(group)]
                    break
        if range_first and range_last:
            return range_first, range_last
        else:
            return False

    def _put_in_pack(self):
        package = False
        if not self._context.get('force_package_create', False):
            package = super(Picking, self)._put_in_pack()
        else:
            for pick in self.filtered(lambda p: p.state not in ('done', 'cancel')):
                operations = pick.move_line_ids.filtered(lambda o: o.product_id.product_tmpl_id.auto_packing and o.qty_done > 0 and not o.result_package_id)
                operation_ids = self.env['stock.move.line']
                if operations:
                    package = self.env['stock.quant.package'].create({})
                    for operation in operations:
                        if float_compare(operation.qty_done, operation.product_uom_qty, precision_rounding=operation.product_uom_id.rounding) >= 0:
                            operation_ids |= operation
                        else:
                            quantity_left_todo = float_round(
                                operation.product_uom_qty - operation.qty_done,
                                precision_rounding=operation.product_uom_id.rounding,
                                rounding_method='UP')
                            done_to_keep = operation.qty_done
                            new_operation = operation.copy(
                                default={'product_uom_qty': 0, 'qty_done': operation.qty_done})
                            operation.write({'product_uom_qty': quantity_left_todo, 'qty_done': 0.0})
                            new_operation.write({'product_uom_qty': done_to_keep})
                            operation_ids |= new_operation

                    operation_ids.write({'result_package_id': package.id})
        return package

    def action_split_row(self):
        if self._context.get('move_line_id', False):
            move = self.env['stock.move.line'].browse(self._context['move_line_id']).mapped('move_id')
            res = move._split_move_line()
        return {
                "type": "ir.actions.do_nothing",
                }