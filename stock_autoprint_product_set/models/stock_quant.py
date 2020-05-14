# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _

import logging
_logger = logging.getLogger(__name__)


class QuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    type = fields.Selection(selection_add=[('set', _('Virtual set'))])
    product_set_id = fields.Many2one('product.set', string='Product Set', change_default=True, ondelete='restrict', copy=True)
    set_product_ids = fields.One2many('product.product', compute="_compute_set_product_ids")
    has_differens = fields.Boolean('Has differents', compute="_compute_has_differens")
    product_set_lines = fields.One2many('product.set.line', compute="_compute_set_product_ids")

    @api.one
    def _compute_has_differens(self):
        self.has_differens = len(self.product_set_lines.ids) > 0
        #self.update({'bgstatus': '#f72b14'})

    def _compute_set_product_ids(self):
        for package in self:
            if package.product_set_id or any([x.id for x in package.child_ids if x.product_set_id]):
                if len(package.child_ids.ids) > 0:
                    package.set_product_ids = False
                    package.product_set_lines = False
                    for child in package.child_ids:
                        package.set_product_ids = package.set_product_ids | child.product_set_id.mapped('set_lines').mapped('product_id')
                        package.set_product_ids = package.set_product_ids - child.product_ids
                        package.product_set_lines = package.product_set_lines | child.product_set_id.mapped('set_lines').filtered(lambda r: r.product_id.id in child.set_product_ids.ids)
                else:
                    package.set_product_ids = package.product_set_id.mapped('set_lines').mapped('product_id') - package.product_ids
                    package.product_set_lines = package.product_set_id.mapped('set_lines').filtered(lambda r: r.product_id.id in package.set_product_ids.ids)
            else:
                package.set_product_ids = False
                package.product_set_lines = False

    @api.multi
    @api.onchange('product_set_id')
    def onchange_product_set_id(self):
        for package in self:
            if package.product_set_id:
                package.image = package.product_set_id.image
                package.image_medium = package.product_set_id.image_medium
                package.image_small = package.product_set_id.image_small
