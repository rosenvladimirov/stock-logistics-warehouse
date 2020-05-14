# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request

import logging
_logger = logging.getLogger(__name__)


class WebsiteBackend(http.Controller):

    @http.route('/get_lot_data', type="json", auth='public', website=False, csrf=False)
    def get_lot_data(self, ref, sn=False, **kw):
        value = False
        res = False
        if ref:
            ref_ids = request.env['stock.picking'].search([('origin', 'ilike', ref)])
            value.update({"ref": [(x.id, x.name) for x in ref_ids]})
        if sn:
            sn_ids = request.env['stock.production.lot'].search(["|", ('ref', '=', sn), ('name', 'ilike', sn)])
        if sn_ids:
            sn_ids.filtered(lambda r: r.current_picking_move_line_ids.move_id.picking_id.id in ref_ids.mapped('id'))
            if sn_ids:
                value.update({"sn": [(x.id, x.name) for x in picking_ids]})
        return value

    @http.route('/set_lot_data', type="json", auth='user')
    def get_lot_data(self, ref, sn, **kw):
        pass

    @http.route('/del_lot_data', type="json", auth='user')
    def get_lot_data(self, sn, **kw):
        pass

