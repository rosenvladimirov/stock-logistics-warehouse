# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from itertools import *
from operator import itemgetter

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class QuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    @api.one
    def _get_serial_ranges(self):
        ret_ranges = []
        sn_ranges = []
        sn_names = {}
        ref_names = {}
        for move in self.quant_ids:
            if move.product_tmpl_id.tracking == 'serialrange' and move.lot_id and move.lot_id.name:
                sn = ''.join(re.findall(r'\d+', move.lot_id.name))
                sn = sn.lstrip("0")
                sn_ref = move.lot_id.ref and ''.join(re.findall(r'\d+', move.lot_id.ref)) or False
                sn_ref = sn_ref and sn_ref.lstrip("0") or False
                sn_ranges.append({'move_line': move, 'sn': int(sn), 'ref_sn': sn_ref and int(sn_ref) or False})
                sn_names[int(sn)] = move.lot_id.name
                if move.lot_id.ref:
                    ref_names[int(sn)] = move.lot_id.ref
        if sn_ranges:
            _logger.info("Move line %s" % (sn_ranges))
            sn_final_ranges = [x['sn'] for x in sn_ranges]
            sn_final_ranges.sort()
            groups = [list(map(itemgetter(1), g)) for k, g in groupby(enumerate(sn_final_ranges), lambda x: x[0]-x[1])]
            for group in groups:
                _logger.info("Group %s:%s" % (sn_names[min(group)], sn_names[max(group)]))
                ret_ranges.append((sn_names[min(group)], sn_names[max(group)]))
        return ret_ranges
