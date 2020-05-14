# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import zip_longest
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, Warning
from odoo.tools import float_utils
from odoo.addons.stock.models.stock_inventory import Inventory as inventory
from odoo.addons.stock.models.stock_inventory import InventoryLine as inventoryline

import logging
_logger = logging.getLogger(__name__)

MAX_COUNT_LINES = 9000


class Inventory(models.Model):
    _inherit = "stock.inventory"

    def action_done(self):
        negative = next((line for line in self.mapped('line_ids') if line.product_qty < 0 and line.product_qty != line.theoretical_qty), False)
        if negative:
            raise UserError(_('You cannot set a negative product quantity in an inventory line:\n\t%s - qty: %s') % (negative.product_id.name, negative.product_qty))
        self.action_check()
        self.write({'state': 'done'})
        self.post_inventory()
        return True

    def action_check(self):
        """ Checks the inventory and computes the stock move to do """
        # tde todo: clean after _generate_moves
        for inventory in self.filtered(lambda x: x.state not in ('done','cancel')):
            # first remove the existing stock moves linked to this inventory
            inventory.with_context(prefetch_fields=False).mapped('move_ids').unlink()
            if len(inventory.line_ids.ids) > 100000:
                action = self.env.ref('stock_inventory_server_action.stock_inventory_on_server')
                if action:
                    _logger.info("Execute action for inventory adjustment on server")
                    action.with_context(dict(self._context, inventory_id=self.id)).run()
                else:
                    raise UserError(
                        _('You don\'t have the server side action for that operation.'))
            else:
                _logger.info("Execute action for inventory adjustment on local")
                msg = _("Info for inventory lines local work: %s ") % len(inventory.line_ids.ids)
                inventory.message_post(body=msg)
                inventory.line_ids._generate_moves()

    def action_on_server(self):
        if self._context.get('inventory_id'):
            inventory = self.env['stock.inventory'].browse([self._context['inventory_id']])
            if inventory:
                count = len(inventory.line_ids.ids)
                _logger.info("Start inventory adjustment on server with lines: %s" % count)
                msg = _("Info for inventory lines: %s ") % count
                inventory.message_post(body=msg)
                inventory.line_ids._generate_moves_scheduler()


class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    def _generate_moves_scheduler(self):
        #moves = self.env['stock.move']
        moves = []
        for line in self:
            inventory = line.inventory_id
            if float_utils.float_compare(line.theoretical_qty, line.product_qty, precision_rounding=line.product_id.uom_id.rounding) == 0:
                continue
            diff = line.theoretical_qty - line.product_qty
            if diff < 0:  # found more than expected
                vals = line._get_move_values(abs(diff), line.product_id.property_stock_inventory.id, line.location_id.id, False)
            else:
                vals = line._get_move_values(abs(diff), line.location_id.id, line.product_id.property_stock_inventory.id, True)
            move = self.env['stock.move'].create(vals)
            move._action_done()
            inventory.message_post_with_view('mail.message_origin_link',
                                             values={'self': move, 'origin': inventory},
                                             subtype_id=self.env.ref('mail.mt_note').id)
            moves.append(move.id)
        return self.env['stock.move'].browse(moves)

    def _generate_moves(self):
        moves = []
        #lines = self.filtered(lambda line: float_utils.float_compare(line.theoretical_qty, line.product_qty, precision_rounding=line.product_id.uom_id.rounding) != 0)
        #count = len(lines.ids)
        for line in self:
            if float_utils.float_compare(line.theoretical_qty, line.product_qty, precision_rounding=line.product_id.uom_id.rounding) == 0:
                continue
            diff = line.theoretical_qty - line.product_qty
            if diff < 0:  # found more than expected
                vals = line._get_move_values(abs(diff), line.product_id.property_stock_inventory.id, line.location_id.id, False)
            else:
                vals = line._get_move_values(abs(diff), line.location_id.id, line.product_id.property_stock_inventory.id, True)
            move = self.env['stock.move'].create(vals)
            if move.state != 'done':
                try:
                    move._action_done()
                except:
                    pass
            moves.append(move.id)
        return self.env['stock.move'].browse(moves)

inventory.action_done = Inventory.action_done
inventory.action_done = Inventory.action_check
inventoryline._generate_moves = InventoryLine._generate_moves
