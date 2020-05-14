# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"

    user_id = fields.Many2one('res.users', string='Warehouseperson', index=True, track_visibility='onchange')

    @api.model
    def create(self, vals):
        if 'user_id' not in vals:
            vals['user_id'] = self.env.user
            location = self.env['stock.location'].search([('id', '=', vals['location_id'])])
            if location and location.warehouse_worker_id:
                users_id = location._get_warehouse_worker()
                vals['user_id'] = users_id and users_id[0].id or self.env.user
        res = super(Picking, self).create(vals)
        mail_channel_obj = self.env['mail.channel']
        channel = mail_channel_obj.sudo().channel_get_extend([res.user_id.partner_id.id, res.company_id.partner_id.id])
        mail_channel = mail_channel_obj.sudo().browse(channel['id'])
        if mail_channel:
            message_content = _('Picking: %s were created') % res.name
            mail_channel.with_context(mail_create_nosubscribe=True).message_post(author_id=res.company_id.partner_id.id, email_from=False, body=message_content, message_type='comment', subtype='mail.mt_comment', content_subtype='plaintext')
        return res
