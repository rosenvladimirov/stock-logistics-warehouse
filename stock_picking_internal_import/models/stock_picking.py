# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from itertools import groupby
from operator import itemgetter

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

import logging
_logger = logging.getLogger(__name__)

class Picking(models.Model):
    _inherit = "stock.picking"

    def prepare_stock_move_line_picking_data(self, picking_id, picking, package=False, location_id=False, location_dest_id=False, quant_ids=False, owner_id=False, package_id=False, result_package_id=False):
        res = []
        res_stock_move_line = {}
        if package:
            curr_quant_ids = package.quant_ids.filtered(lambda r: quant_ids == False or r.id in quant_ids.ids)
        else:
            curr_quant_ids = picking.move_line_ids
        if not self._context.get('force_validate'):
            picking_type_lots = (self.picking_type_id.use_create_lots or self.picking_type_id.use_existing_lots)
            for quant in curr_quant_ids:
                if package:
                    qty = quant.quantity > 0.0 and quant.quantity or 0.0
                    package_id = package_id or quant.package_id.id
                else:
                    qty = quant.qty_done
                    package_id = False
                    result_package_id = quant.package_id.id
                stock_move_line = self.env['stock.move.line'].new({
                    'picking_id': picking_id,
                    'product_id': quant.product_id.id,
                    'product_uom_id': quant.product_uom_id.id,
                    'lot_id': quant.lot_id.id,
                    'package_id': package_id,
                    'result_package_id': result_package_id,
                    'location_id': location_id and location_id.id or self.location_id.id,
                    'location_dest_id': location_dest_id and location_dest_id.id or self.location_dest_id.id,
                    'qty_done': (quant.product_id.tracking == 'none' and picking_type_lots) and qty or quant.lot_id and qty or 0.0,
                    'owner_id': owner_id,
                    'ordered_qty': (quant.product_id.tracking == 'none' and picking_type_lots) and qty or quant.lot_id and qty or 0.0,
                    'date': fields.datetime.now(),
                })
                if not res_stock_move_line.get(quant.product_id):
                    res_stock_move_line[quant.product_id] = []
                res_stock_move_line[quant.product_id].append((0, 0, stock_move_line._convert_to_write(stock_move_line._cache)))

        for product, lines in groupby(curr_quant_ids, lambda l: l.product_id):
            if package:
                qty = sum([x.quantity for x in lines])
            else:
                qty = sum([x.qty_done for x in lines])
            move = self.prepare_stock_move_package_data(picking_id, product, qty, picking, package, location_id=location_id, location_dest_id=location_dest_id)
            if res_stock_move_line.get(product, False):
                move['move_line_ids'] = res_stock_move_line[product]
            res.append((0, 0, move._convert_to_write(move._cache)))
        return res

    def prepare_stock_move_package_data(self, picking_id, product, qty, picking, package=False, old_qty=0, location_id=False, location_dest_id=False):
        if package:
            oring = _('PKG/%s' % package.name)
        else:
            oring = _('PICK/%s' % picking.name)

        name = '%s%s/%s>%s' % (
                oring,
                product.code and '/%s: ' % product.code or '/',
                location_id and location_id.name or self.location_id.name, self.location_dest_id.name)
        stock_move = self.env['stock.move'].new({
            'picking_id': picking_id,
            'name': name,
            'origin': oring,
            'location_id': location_id and location_id.id or self.location_id.id,
            'location_dest_id': location_dest_id and location_dest_id.id or self.location_dest_id.id,
            'product_id': product.id,
            'ordered_qty': qty+old_qty,
            'product_uom_qty': qty+old_qty,
            'product_uom': product.product_tmpl_id.uom_id.id,
        })
        return stock_move
