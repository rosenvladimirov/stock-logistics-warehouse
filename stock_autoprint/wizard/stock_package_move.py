# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class StockPackageMove(models.TransientModel):
    _name = 'stock.package.move'
    _rec_name = 'package_id'
    _description = "Wizard model to move package into a quotation"

    package_id = fields.Many2one(
        'stock.quant.package',
        'Package',
        readonly=True,
        default=lambda self: self._context.get('default_package_id'),
        help='The package containing this quant')

    location_id = fields.Many2one(
        'stock.location', "Source Location",
        default=lambda self: self._context.get('default_location_id'),
        required=True, readonly=True)
    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_dest_id,
        required=True)
    owner_id = fields.Many2one(
        'res.partner', 'Owner',
        help="Default Owner")

    @api.multi
    @api.onchange('location_dest_id')
    def onchange_location_dest_id(self):
        for package in self:
            package.owner_id = package.location_dest_id.partner_id.id

    def _get_default_picking_value(self):
        warehouse = self.location_id.get_warehouse()
        return {
            'origin': self.package_id.child_ids and '(%s) %s' % (self.package_id.complete_name, '-'.join([x.name for x in self.package_id.child_ids])) or self.package_id.complete_name,
            'move_type': 'direct',
            'state': 'draft',
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'picking_type_id': warehouse.int_type_id.id,
            'picking_type_code': 'internal',
            'owner_id': self.owner_id and self.owner_id.id or self.location_id.partner_id and self.location_id.partner_id.id or False,
        }

    @api.multi
    def move_package(self):
        """ Move package, multiplied by quantity in piking line """
        stock_package_move_id = self._context['active_id']
        if not stock_package_move_id:
            return
        package_id = self.package_id
        picking_id = False
        picking_ids = []
        old_lines_ids = {}
        if package_id:
            if package_id.move_line_ids:
                picking = self.env['stock.picking'].create(self._get_default_picking_value())
                product_excluse_ids = package_id.removed_move_line_ids.mapped("product_id").ids
                lot_excluse_ids = package_id.removed_move_line_ids.mapped("lot_id").ids
                old_lines_ids[picking] = package_id.move_line_ids.filtered(lambda r: r.product_id.id not in product_excluse_ids and r.lot_id not in lot_excluse_ids)
                picking.move_lines = picking.with_context(
                    dict(self._context, force_validate=False, force_package=True)).prepare_stock_move_line_package_data(picking.id,
                                                                                                    package_id,
                                                                                                    location_id=self.location_id,
                                                                                                    location_dest_id=self.location_dest_id,
                                                                                                    result_package_id=package_id.id,
                                                                                                    quant_ids=False)
                picking.action_confirm()
                for move_line in picking.move_lines:
                    move_line.move_line_ids.write({'package_id': False, 'result_package_id': package_id.id})
                picking_id = picking.id
                picking_ids.append(picking.id)
            if len(package_id.child_ids.ids) > 0:
                for package_id in self.package_id.child_ids:
                    picking = self.env['stock.picking'].create(self._get_default_picking_value())
                    product_excluse_ids = package_id.removed_move_line_ids.mapped("product_id").ids
                    lot_excluse_ids = package_id.removed_move_line_ids.mapped("lot_id").ids
                    old_lines_ids[picking] = package_id.move_line_ids.filtered(lambda r: r.product_id.id not in product_excluse_ids and r.lot_id not in lot_excluse_ids)
                    picking.move_lines = picking.with_context(
                        dict(self._context, force_validate=False, force_package=True)).prepare_stock_move_line_package_data(picking.id,
                                                                                                        package_id,
                                                                                                        location_id=self.location_id,
                                                                                                        location_dest_id=self.location_dest_id,
                                                                                                        result_package_id=package_id.id,
                                                                                                        quant_ids=False)
                    picking.action_confirm()
                    for move_line in picking.move_lines:
                        move_line.move_line_ids.write({'package_id': False, 'result_package_id': package_id.id})
                    picking_ids.append(picking.id)
            for picking, move_lines in old_lines_ids.items():
                if picking.move_line_ids:
                    move_lines.write({'result_package_id': False})
            return self.package_id.with_context(dict(default_id=picking_id, default_ids=picking_ids)).action_move_pack()
        else:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.package.move',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': self._context['active_id'],
                'target': 'new',
                }
