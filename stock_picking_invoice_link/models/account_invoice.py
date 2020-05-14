# Copyright 2013-15 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright 2015-2016 AvanzOSC
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2017 Jacques-Etienne Baudoux <je@bcim.be>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, api, _


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    picking_ids = fields.Many2many(
        comodel_name='stock.picking',
        string='Related Pickings',
        readonly=True,
        copy=False,
        help="Related pickings "
             "(only when the invoice has been generated from a sale order).",
    )
    move_lines = fields.Many2many('stock.move.line', string='Detailed operation', compute='_compute_move_lines')
    stock_move_ids = fields.Many2many('stock.move', string='Detailed operation', compute='_compute_stock_move_ids')

    has_picking_ids = fields.Boolean(compute="_compute_has_picking_ids")
    has_move_lines = fields.Boolean(compute="_compute_has_picking_ids")

    @api.one
    @api.depends('picking_ids', 'move_lines')
    def _compute_has_picking_ids(self):
        self.has_picking_ids = len(self.picking_ids.ids) > 0
        self.has_move_lines = len(self.move_lines.ids) > 0

    @api.one
    @api.depends('invoice_line_ids', 'invoice_line_ids.move_line_ids', 'picking_ids')
    def _compute_move_lines(self):
        for line in self.invoice_line_ids:
            for move_line in line.move_line_ids:
                self.move_lines |= move_line.move_line_ids

    @api.one
    @api.depends('invoice_line_ids', 'invoice_line_ids.move_line_ids')
    def _compute_stock_move_ids(self):
        for line in self.invoice_line_ids:
            for move_line in line.move_line_ids:
                self.stock_move_ids |= move_line

    def _prepare_invoice_line_from_po_line(self, line):
        data = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(line)
        if line.order_id.picking_ids:
            picking_ids = line.order_id.mapped("picking_ids").ids
            data['picking_ids'] = [(6, 0, picking_ids)]
            move_ids = line.mapped('move_ids').filtered(
                lambda x: x.state == 'done'
                          and not x.scrapped and (
                                  x.location_dest_id.usage == 'supplier' or
                                  (x.location_id.usage == 'supplier' and
                                   x.to_refund)
                          )).ids
            data['move_line_ids'] = [(6, 0, move_ids)]
        return data


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
