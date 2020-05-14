# Copyright 2015 Anybox S.A.S
# Copyright 2016-2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api
import odoo.addons.decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class StockPackageAdd(models.TransientModel):
    _name = 'sale.order.package.add'
    _rec_name = 'package_id'
    _description = "Wizard model to add package into a sale order"

    package_id = fields.Many2one('stock.quant.package', 'Package', help='The package containing this quant')
    package_qty = fields.Integer("Quantity", default=1)

    @api.multi
    def add_package(self):
        """ Add package, multiplied by quantity in piking line """
        order_id = self._context['active_id']
        if not order_id:
            return
        so = self.env['sale.order'].browse(order_id)
        force_validate = self._context.get('force_validate', False)
        if so:
            so.order_line = so.with_context(dict(self._context, force_validate=force_validate)).prepare_sale_order_line_package_data(so.id, self.package_id, self.package_qty)
        else:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order.package.add',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': self._context['active_id'],
                'target': 'new',
                }