# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from itertools import groupby
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    location_src_id = fields.Many2one('stock.location', 'Source Location', help="Source location is action=move")

    def prepare_sale_order_line_package_data(self, order_id, package, package_qty, old_qty=0.0, quant_ids=False):
        res = []
        sequence = 0
        curr_quant_ids = package.quant_ids.filtered(lambda r: quant_ids == False or r.id in quant_ids.ids)
        for product, lines in groupby(curr_quant_ids, lambda l: l.product_id):
            qty = sum([x.quantity for x in lines])
            sequence += 1
            sale_line = self.env['sale.order.line'].new({
                'order_id': order_id,
                'product_id': product.id,
                'product_uom_qty': package_qty*qty + old_qty,
                'product_uom': product.uom_id.id,
                'sequence': sequence,
            })
            sale_line.product_id_change()
            res.append((0, 0, sale_line._convert_to_write(sale_line._cache)))
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        self.ensure_one()
        values.update({
            'location_src_id': self.order_id.location_src_id,
        })
        return values
