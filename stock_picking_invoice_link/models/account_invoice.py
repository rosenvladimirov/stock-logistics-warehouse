# Copyright 2013-15 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright 2015-2016 AvanzOSC
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2017 Jacques-Etienne Baudoux <je@bcim.be>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, api, _


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    picking_ids = fields.Many2many(
        comodel_name='stock.picking',
        string='Related Pickings',
        readonly=True,
        copy=False,
        help="Related pickings "
             "(only when the invoice has been generated from a sale order).",
    )
    move_lines = fields.Many2many('stock.move.line', string='Detailed operation', compute='_compute_move_lines')

    @api.one
    @api.depends('invoice_line_ids', 'invoice_line_ids.move_line_ids', 'picking_ids')
    def _compute_move_lines(self):
        for line in self.invoice_line_ids:
            for move_line in line.move_line_ids:
                self.move_lines |= move_line.move_line_ids

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    move_line_ids = fields.One2many(
        comodel_name='stock.move',
        inverse_name='invoice_line_id',
        string='Related Stock Moves',
        readonly=True,
        copy=False,
        help="Related stock moves "
             "(only when the invoice has been generated from a sale order).",
    )
    move_lines = fields.Many2many('stock.move.line', string='Detailed operation', compute='_compute_move_lines')

    @api.one
    @api.depends('move_line_ids')
    def _compute_move_lines(self):
        for move_line in self.move_line_ids:
            self.move_lines |= move_line.move_line_ids
