# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from itertools import groupby
from operator import itemgetter

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

import logging
_logger = logging.getLogger(__name__)

from odoo import fields, models, api
from odoo.addons.stock.models.stock_move import StockMove as stock_initial_demand


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.depends('state', 'picking_id')
    def _compute_is_initial_demand_editable(self):
        for move in self:
            if self._context.get('planned_picking'):
                move.is_initial_demand_editable = True
            elif move.picking_id.is_initial_demand_editable:
                move.is_initial_demand_editable = True
            elif not move.picking_id.is_locked and move.state != 'done' and move.picking_id:
                move.is_initial_demand_editable = True
            else:
                move.is_initial_demand_editable = False

stock_initial_demand._compute_is_initial_demand_editable = StockMove._compute_is_initial_demand_editable
