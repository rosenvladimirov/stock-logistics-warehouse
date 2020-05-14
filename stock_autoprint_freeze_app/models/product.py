# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    freeze = fields.Boolean("Is static")
