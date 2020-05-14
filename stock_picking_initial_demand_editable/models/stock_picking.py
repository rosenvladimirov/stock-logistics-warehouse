# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from itertools import groupby
from operator import itemgetter

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

import logging
_logger = logging.getLogger(__name__)

class Picking(models.Model):
    _inherit = "stock.picking"

    is_initial_demand_editable = fields.Boolean('Force initial at demand')
