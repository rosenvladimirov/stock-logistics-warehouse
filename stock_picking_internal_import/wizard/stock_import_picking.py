# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class StockPickingInternalImport(models.TransientModel):
    _name = 'stock.picking.internal.import'
    _rec_name = 'import_picking_id'
    _description = 'Put picking in package'
    _inherit = ['barcodes.barcode_events_mixin']

    import_picking_name = fields.Char('From picking', required=True)
    import_picking_id = fields.Many2one('stock.picking', 'From picking', ondelete='restrict', compute_sudo=True)
    package_id = fields.Many2one('stock.quant.package', 'Package', help='The package containing this quant', compute_sudo=True)

    def on_barcode_scanned(self, barcode):
        self.import_picking_name = barcode

    @api.multi
    def import_picking(self):
        """ Add package, multiplied by quantity in piking line """
        packing_id = self._context['active_id']
        import_picking = self.sudo().env['stock.picking'].search([('name', '=', self.import_picking_name)])
        if not packing_id:
            return
        picking = self.env['stock.picking'].browse(packing_id)
        if picking:
            is_locked = picking.is_locked
            if picking.is_locked:
                picking.action_toggle_is_locked()
                picking.move_lines = picking.with_context(dict(self._context, force_validate=False)).prepare_stock_move_line_picking_data(picking.id, import_picking, self.package_id)
            if is_locked:
                picking.action_toggle_is_locked()
        else:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.package.picking',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': self._context['active_id'],
                'target': 'new',
                }
