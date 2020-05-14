# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class StockPackageMove(models.TransientModel):
    _name = 'stock.package.picking'
    _rec_name = 'picking_id'
    _description = 'Put picking in package'

    picking_id = fields.Many2one('stock.picking', 'From picking', ondelete='restrict', required=True)
    package_id = fields.Many2one('stock.quant.package', 'Package', help='The package containing this quant')

    @api.multi
    def add_package(self):
        """ Add package, multiplied by quantity in piking line """
        picking = self.picking_id
        if not picking:
            return
        if picking:
            #_logger.info("PICKING %s" % picking)
            is_locked = picking.is_locked
            if picking.is_locked:
                picking.action_toggle_is_locked()
            lines_ids = picking.move_line_ids
            lines_ids.write({'result_package_id': self.package_id.id})
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
