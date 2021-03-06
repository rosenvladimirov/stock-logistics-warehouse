# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    sourced_move_ids = fields.One2many('stock.move', 'origin_sourced_move_id', 'All fallowed moves', help='Optional: all fallowed moves created from source move')
    origin_sourced_move_id = fields.Many2one('stock.move', 'Origin fallow move', copy=False, help='Move that created the fallow move')

    def write(self, vals):
        res = super(StockMove, self).write(vals)
        #_logger.info("Write qty and put in package %s:%s" % (vals, self.product_id.product_tmpl_id.auto_packing))
        if 'move_line_ids' in vals:
            ctx = self._context.copy() or {}
            ctx.update(dict(force_package_create=True))
            self.picking_id.with_context(ctx)._put_in_pack()
        return res

    #def _action_done(self):
    #    moves_todo = super(StockMove, self)._action_done()
    #    for line in moves_todo.mapped('move_line_ids').filtered(lambda r: r.package_id):
    #        line.mapped('package_id').mapped('quant_ids').filtered(lambda r: r.product_id.id == line.product_id.id).write({'package_id': False})
    #    return moves_todo

    def _split_move_line(self):
        ctx = self.env.context.copy()
        ctx.update(dict(force_split=True))
        operation_ids = False
        for pick in self.picking_id.filtered(lambda p: p.state not in ('done', 'cancel')):
            operations = pick.move_line_ids.filtered(lambda o: o.product_uom_qty > 0.0 and o.qty_done > 0 and not o.split_line)
            operation_ids = self.env['stock.move.line']
            if operations:
                for operation in operations:
                    lot_id = False
                    result_package_id = False
                    owner_id = False
                    done_to_keep = False
                    current_qty_done = 0.0
                    total_qty_done = operation.product_uom_qty
                    for line in range(0, operation.package_qty):
                        current_qty_done += operation.qty_done
                        quantity_left_todo = float_round(
                            operation.product_uom_qty - operation.qty_done,
                            precision_rounding=operation.product_uom_id.rounding,
                            rounding_method='UP')
                        if operation.product_id.product_tmpl_id.auto_packing and not operation.result_package_id:
                            package = self.env['stock.quant.package'].create({})
                            result_package_id = package.id
                        else:
                            package = False
                            result_package_id = False
                        if float_compare(operation.qty_done, operation.product_uom_qty, precision_rounding=operation.product_uom_id.rounding) >= 0:
                            operation_ids |= operation
                            # Write rest
                            if float_compare(current_qty_done, total_qty_done, precision_rounding=operation.product_uom_id.rounding) == 0:
                                done_to_keep = done_to_keep or operation.qty_done
                                operation.write({'product_uom_qty': done_to_keep, 'qty_done': done_to_keep, 'package_qty': 1.0,
                                                 'sequence': line + 1,
                                                 'split_lot_id': False, 'split_line': True})
                                break
                            elif float_compare(current_qty_done, total_qty_done, precision_rounding=operation.product_uom_id.rounding) > 0:
                                operation.write({'product_uom_qty': operation.qty_done - (current_qty_done-total_qty_done),
                                                 'qty_done': operation.qty_done - (current_qty_done-total_qty_done), 'package_qty': 0,
                                                 'sequence': line + 1,
                                                 'lot_id': lot_id and lot_id.id or False, 'result_package_id': result_package_id, 'split_lot_id': False})
                                break
                        else:
                            lot_id = lot_id or operation.split_lot_id
                            result_package_id = result_package_id or operation.result_package_id.id
                            owner_id = owner_id or operation.owner_id
                            done_to_keep = done_to_keep or operation.qty_done

                            # Force Update before to write
                            new_operation = operation.with_context(ctx).copy(
                                default={'product_uom_qty': 0, 'qty_done': operation.qty_done, 'split_line': True, 'split_lot_id': False, 'sequence': operation.sequence})
                            # Now write the last separated quantity and remove all data for lots and packages
                            operation.write({'qty_done': operation.qty_done if line+1 < operation.package_qty else 0.0,
                                             'package_qty': operation.package_qty if line+1 < operation.package_qty else 0.0,
                                             'sequence': line + 1,
                                             'lot_id': False, 'result_package_id': False, 'split_lot_id': False})
                            operation.write({'product_uom_qty': quantity_left_todo})
                            new_operation.write({'product_uom_qty': done_to_keep, 'lot_id': lot_id and lot_id.id or False, 'package_qty': 1.0,
                                                 'result_package_id': result_package_id,
                                                 'sequence': line+1,
                                                 'owner_id': owner_id and owner_id.id or False})
                            operation_ids |= new_operation
            else:
                raise UserError(_('Please process reserve some quantity!'))
        return operation_ids

    def action_split_row(self):
        res = self._split_move_line()
        return {
                "type": "ir.actions.do_nothing",
                }


class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):
        result = super(ProcurementRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, origin, values, group_id)
        if values.get('location_src_id', False):
            result['location_id'] = values['location_src_id']
        return result
