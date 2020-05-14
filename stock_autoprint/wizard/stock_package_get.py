# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
import odoo.addons.decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class StockPackageGet(models.TransientModel):
    _name = 'stock.package.get'
    _rec_name = 'package_id'
    _description = "Wizard model to get from package into a quotation"

    package_id = fields.Many2one('stock.quant.package', 'Package', help='The package containing this quant', readonly=True)
    location_id = fields.Many2one('stock.location', "Source Location",
        default=lambda self: self._context.get('default_location_id'),
        required=True, readonly=True)
    location_dest_id = fields.Many2one('stock.location', "Destination Location",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_dest_id,
        required=True)
    package_dest_id = fields.Many2one('stock.quant.package', 'Destination Package', help='The containing to this package')
    owner_id = fields.Many2one(
        'res.partner', 'Owner',
        help="Default Owner")
    curr_quant_ids = fields.One2many('stock.quant', related="package_id.quant_ids", string='Bulk Content')
    quant_ids = fields.Many2many('stock.quant', compute_sudo=True)

    @api.multi
    def _compute_quant_ids(self):
        for get in self:
            package = get.package_id
            if len(package.child_ids.ids) > 0:
                get.quant_ids = package.quant_ids
                for child in package.child_ids:
                    get.quant_ids = self.quant_ids | child.quant_ids
            else:
                get.quant_ids = package.quant_ids

    @api.onchange('location_id')
    @api.depends('owner_id')
    def onchange_location_id(self):
        for get in self:
            if get.location_id.partner_id:
                get.owner_id = get.location_id.partner_id

    @api.onchange('location_dest_id')
    @api.depends('package_dest_id')
    def onchange_location_dest_id(self):
        for get in self:
            if get.location_dest_id:
                get.package_dest_id = False
                location_id = get.location_dest_id
                return {'domain': {'package_dest_id': [('location_id', '=', location_id.id)]}}
            else:
                return {'domain': {'package_dest_id': []}}

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
            'owner_id': self.owner_id.id,
            #'result_package_id': self.package_dest_id.id,
            #'package_id': self.package_id.id,
        }

    @api.multi
    def get_from_package(self):
        """ Get from package, multiplied by quantity in piking line """
        stock_package_move_id = self._context['active_id']
        if not stock_package_move_id:
            return
        package_id = self.package_id
        picking_ids = []
        quant_ids = self.quant_ids and self.quant_ids or self.curr_quant_ids
        package_ids = quant_ids.mapped('package_id')
        product_ids = quant_ids.mapped('product_id')
        lot_ids = quant_ids.mapped('lot_id')
        #_logger.info("PACKAGE %s:%s:%s:%s:%s:%s" % (self._context, package_ids, quant_ids.ids, product_ids, lot_ids, package_id))
        if package_id and package_ids:
            if package_id.move_line_ids.filtered(lambda r: r.lot_id and r.lot_id.id in lot_ids.ids or True and r.product_id.id in product_ids.ids and r.result_package_id.id in package_ids.ids):
                picking = self.env['stock.picking'].create(self._get_default_picking_value())
                picking.move_lines = picking.with_context(
                    dict(self._context, force_validate=False)).prepare_stock_move_line_package_data(picking.id,
                                                                                                    package_id,
                                                                                                    location_id=self.location_id,
                                                                                                    location_dest_id=self.location_dest_id,
                                                                                                    quant_ids=quant_ids,
                                                                                                    owner_id=self.owner_id and self.owner_id.id or False)
                picking.action_confirm()
                for move_line in picking.move_lines:
                    move_line.move_line_ids.write({'package_id': package_id.id,
                                                   'result_package_id': self.package_dest_id and self.package_dest_id.id or False})
                picking_id = picking.id
                picking_ids.append(picking.id)
                return self.package_id.with_context(
                    dict(default_id=picking_id, default_ids=picking_ids)).action_move_pack()
        return {
            "type": "ir.actions.do_nothing",
            }
