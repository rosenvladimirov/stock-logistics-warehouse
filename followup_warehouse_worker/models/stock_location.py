# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2015 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, _
from openerp.exceptions import Warning


class StockLocation(models.Model):
    _inherit = 'stock.location'

    def _get_default_user_domain(self):
        return [('groups_id', 'in', [self.env.ref('stock.group_stock_user').id, self.env.ref('stock.group_stock_manager').id])]

    warehouse_worker_id = fields.Many2one(
        string='A warehouse officer',
        comodel_name="res.users",
        default=lambda self: self.env.user,
        domain=lambda self: self._get_default_user_domain(),
        help="Please select the person responsible for this storage location if there are multiple sub-locations in this location this worker will serve all")

    def _get_warehouse_worker(self):
        for location in self:
            warehouse_worker_ids = set()
            if location.warehouse_worker_id:
                warehouse_worker_ids.add(location.warehouse_worker_id)
            while location.location_id and location.usage != 'view':
                location = location.location_id
                warehouse_worker_ids.add(location.warehouse_worker_id)
        return list(warehouse_worker_ids)
