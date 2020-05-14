# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class StockPackageFromSet(models.TransientModel):
    _name = 'stock.package.from.set'
    _rec_name = 'package_id'
    _description = "Wizard model to make package from set"

    warehouse_id = fields.Many2one(
            'stock.warehouse', 'Warehouse', ondelete='cascade',
            default=lambda self: self.env['stock.warehouse'].search([('company_id', '=', self.env.user.company_id.id)], limit=1))
    package_id = fields.Many2one(
        'stock.quant.package',
        'Package',
        readonly=True,
        default=lambda self: self._context.get('default_package_id'),
        help='The package containing this quant')

    product_set_id = fields.Many2one('product.set', string='Product Set', ondelete='restrict', default=lambda self: self._context.get('default_product_set_id'))
    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1)
    set_lines = fields.One2many('stock.package.from.set.line', 'set_id', string="Products", copy=True)

    #location_id = fields.Many2one(
    #    'stock.location', "Source Location",
    #    required=True)
    #location_dest_id = fields.Many2one(
    #    'stock.location', "Destination Location",
    #    required=True)
    owner_id = fields.Many2one(
        'res.partner', 'Owner',
        help="Default Owner")

    #@api.multi
    #@api.onchange('warehouse_id')
    #def onchange_warehouse_id(self):
    #    for rec in self:
    #        self.location_id = rec.warehouse_id.int_type_id.default_location_src_id.id
    #        self.location_dest_id = rec.warehouse_id.int_type_id.default_location_dest_id.id

    @api.multi
    @api.onchange('location_dest_id')
    def onchange_location_dest_id(self):
        for package in self:
            package.owner_id = package.location_dest_id.partner_id.id

    @api.multi
    @api.onchange('product_set_id')
    def onchange_product_set_id(self):
        for rec in self:
            #rec.set_lines.unlink()
            values = []
            for line in rec.product_set_id.set_lines:
                values.append((0, False, {
                    'product_tmpl_id': line.product_tmpl_id.id,
                    'product_id': line.product_id.id,
                    'quantity': line.quantity,
                    'product_set_id': line.product_set_id.id,
                    'sequence': line.sequence,
                    }))
            rec.update({'set_lines': values})

    def _get_default_picking_value(self):
        #warehouse = self.location_id.get_warehouse()
        int_type = self.warehouse_id.int_type_id
        return {
            'origin': self.package_id.complete_name,
            'move_type': 'direct',
            'state': 'draft',
            'location_id': int_type.default_location_src_id.id,
            'location_dest_id': int_type.default_location_dest_id.id,
            'picking_type_id': int_type.id,
            'picking_type_code': 'internal',
            'owner_id': self.owner_id.id,
        }

    @api.multi
    def make_package(self):
        """ Make package, multiplied by quantity in piking line """
        stock_package_make_id = self._context['active_id']
        if not stock_package_make_id:
            return
        int_type = self.warehouse_id.int_type_id
        #package = self.env['stock.quant.package'].create({})
        picking = self.env['stock.picking'].create(self._get_default_picking_value())
        if picking:
            picking.move_lines = picking.with_context(dict(self._context, force_validate=True)).prepare_stock_move_line_pset_data(picking.id, self.set_lines, self.quantity)
            picking.action_confirm()
            picking.action_assign()
            # force replace from locations
            for line in picking.move_line_ids.filtered(lambda r: r.location_id.id != picking.location_id.id):
                line.write({'location_id': picking.location_id.id, 'lot_id': False})
            for line in picking.move_line_ids.filtered(lambda r: r.package_id):
                line.write({'package_id': False, 'lot_id': False})
            for line in picking.move_line_ids:
                line.write({'qty_done': line.product_uom_qty or line.ordered_qty, 'owner_id': self.owner_id.id})
            picking._put_in_pack()
            #picking.action_assign_owner()
            return self.package_id.with_context(dict(default_id=picking.id)).action_move_pack()
        else:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.package.move',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': self._context['active_id'],
                'target': 'new',
                }


class StockPackageFromSetLine(models.TransientModel):
    _name = 'stock.package.from.set.line'
    _description = 'Product set line'
    _rec_name = 'product_id'
    _order = 'sequence'


    set_id = fields.Many2one('stock.package.from.set', string='Product Set', ondelete="cascade")
    product_tmpl_id = fields.Many2one(comodel_name='product.template', string='Product template', readonly=True)
    product_id = fields.Many2one(comodel_name='product.product', string='Product')
    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1)
    product_uom = fields.Many2one('product.uom', related="product_id.uom_id", string='Unit of Measure', readonly=True)

    product_set_id = fields.Many2one('product.set', string='Product Set', ondelete="restrict")
    sequence = fields.Integer(string='Sequence', required=True, default=0,)
    type = fields.Selection("product.set", related='product_set_id.type', string="Type", readonly=True)
