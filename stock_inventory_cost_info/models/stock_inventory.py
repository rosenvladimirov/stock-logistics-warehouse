# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class Inventory(models.Model):
    _inherit = "stock.inventory"

    @api.multi
    def refresh_cost_info(self):
        for record in self:
            for line in record.line_ids:
                line._compute_adjustment_cost()


class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    currency_id = fields.Many2one(
        string="Currency",
        related="inventory_id.company_id.currency_id",
        readonly=True,
    )
    adjustment_cost = fields.Monetary(
        string="Adjustment cost",
        compute="_compute_adjustment_cost",
        store=True,
    )

    standard_price = fields.Float(
        'Cost', related="product_id.standard_price",
        store=True,
        digits=dp.get_precision('Product Price'), groups="base.group_user",
        help = "Cost used for stock valuation in standard price and as a first price to set in average/fifo. "
               "Also used as a base price for pricelists. "
               "Expressed in the default unit of measure of the product. ")

    @api.depends("product_qty", "theoretical_qty", "inventory_id.state")
    def _compute_adjustment_cost(self):
        for record in self:
            adjusted_qty = record.product_qty - record.theoretical_qty
            adjustment_cost = adjusted_qty * record.product_id.standard_price
            record.adjustment_cost = adjustment_cost
