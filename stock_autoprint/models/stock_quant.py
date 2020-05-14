# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from itertools import *
from operator import itemgetter
from odoo.exceptions import ValidationError
from odoo.addons.stock.models.stock_quant import QuantPackage as quantpackage

from odoo import api, fields, models, tools, _

import logging
_logger = logging.getLogger(__name__)


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    product_image_medium = fields.Binary(
        related="product_id.image_medium",
        string="Image", store=True)


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    product_image_medium = fields.Binary(
        related="product_id.image_medium",
        string="Image", store=True)


class PackageCategory(models.Model):
    _description = 'Packages Tags'
    _name = 'stock.quant.package.category'
    _order = 'parent_left, name'
    _parent_store = True
    _parent_order = 'name'

    name = fields.Char(string='Tag Name', required=True, translate=True)
    color = fields.Integer(string='Color Index')
    parent_id = fields.Many2one('stock.quant.package.category', string='Parent Category', index=True, ondelete='cascade')
    child_ids = fields.One2many('stock.quant.package.category', 'parent_id', string='Child Tags')
    active = fields.Boolean(default=True, help="The active field allows you to hide the category without removing it.")
    parent_left = fields.Integer(string='Left parent', index=True)
    parent_right = fields.Integer(string='Right parent', index=True)
    package_ids = fields.Many2many('stock.quant.package', column1='category_id', column2='package_id', string='Packages')

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('Error ! You can not create recursive tags.'))

    @api.multi
    def name_get(self):
        """ Return the categories' display name, including their direct
            parent by default.
            If ``context['package_category_display']`` is ``'short'``, the short
            version of the category name (without the direct parent) is used.
            The default is the long version.
        """
        if self._context.get('package_category_display') == 'short':
            return super(PackageCategory, self).name_get()

        res = []
        for category in self:
            names = []
            current = category
            while current:
                names.append(current.name)
                current = current.parent_id
            res.append((category.id, ' / '.join(reversed(names))))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            # Be sure name_search is symetric to name_get
            name = name.split(' / ')[-1]
            args = [('name', operator, name)] + args
        return self.search(args, limit=limit).name_get()


class QuantPackage(models.Model):
    _inherit = 'stock.quant.package'
    _order = 'parent_left, name'
    _parent_store = True
    _parent_order = 'name'

    def _default_category(self):
        return self.env['stock.quant.package.category'].browse(self._context.get('category_id'))

    @api.multi
    def _get_has_childs(self):
        for package in self:
            package.has_childs = len(package.child_ids.ids) > 0

    @api.multi
    def _get_has_saved(self):
        for package in self:
            package.has_saved = len(package.freeze_product_ids.ids) > 0

    removed_move_line_ids = fields.One2many('stock.move.line', 'package_id')

    name = fields.Char(translate=True)
    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name',
        store=True)
    location_name = fields.Char('Location', related="location_id.name")
    lot_owner_id = fields.Many2one('res.partner', 'Location Owner', related="location_id.partner_id")
    parent_id = fields.Many2one('stock.quant.package', 'Parent Package', index=True, ondelete='cascade')
    child_ids = fields.One2many('stock.quant.package', 'parent_id', 'Included Packages')
    parent_left = fields.Integer(string='Left parent', index=True)
    parent_right = fields.Integer(string='Right parent', index=True)
    has_childs = fields.Boolean(compute=_get_has_childs)

    type = fields.Selection([
                        ('package', _('Normal package')),
                        ('bag', _('Big bag')),
                        ('palete', _('Palete')),
                        ('view', _('Virtual package'))
                        ], string="Type", default='package')

    state = fields.Selection([
        ('storage', 'In internal storage'),
        ('packing', 'In packaging storage'),
        ('way', 'On Way'),
        ('delivered', 'Delivered')], string='Status',
        copy=False, default='storage', index=True, readonly=True,
        help="* Local: When the package stay in local storages.\n"
             "* Packaging: This state can be seen when a package stay in packagin center.\n"
             "* On Way: This state is reached when the package is departing/arriving from/to company...\n"
             "* Delivered: When package is delivered in end customer/supplier destination.")
    color = fields.Integer(string='Color Index')
    red_weight_female = fields.Boolean(compute="_red_weight_female")
    red_weight_male = fields.Boolean(compute="_red_weight_female")

    # image: all image fields are base64 encoded and PIL-supported
    image = fields.Binary(
        "Image", attachment=True,
        help="This field holds the image used as image for the product, limited to 1024x1024px.")
    image_medium = fields.Binary(
        "Medium-sized image", attachment=True,
        help="Medium-sized image of the product. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved, "
             "only when the image exceeds one of those sizes. Use this field in form views or some kanban views.")
    image_small = fields.Binary(
        "Small-sized image", attachment=True,
        help="Small-sized image of the product. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")
    category_id = fields.Many2many('stock.quant.package.category', column1='package_id',
                                   column2='category_id', string='Tags', default=_default_category)
    save_move_line_ids = fields.One2many('stock.move.line', 'result_package_id')
    child_quant_ids = fields.One2many('stock.quant', compute="_compute_child_quant_ids")
    product_ids = fields.One2many('product.product', compute="_compute_product_ids")
    freeze_product_ids = fields.Many2many('product.product', string="Last saved package products")
    freeze_date = fields.Date('Last saved date')
    has_saved = fields.Boolean(compute=_get_has_saved)

    @api.depends('quant_ids.package_id', 'quant_ids.location_id', 'quant_ids.company_id', 'quant_ids.owner_id')
    def _compute_package_info(self):
        for package in self:
            values = {'location_id': False, 'company_id': self.env.user.company_id.id, 'owner_id': False}
            if package.quant_ids:
                location_id = package.quant_ids.filtered(lambda r: r.quantity > 0.0)
                if len(location_id) > 0:
                    values['location_id'] = location_id[0].location_id
            package.location_id = values['location_id']
            package.company_id = values['company_id']
            package.owner_id = values['owner_id']

    def _compute_child_quant_ids(self):
        for package in self:
            if len(package.child_ids.ids) > 0:
                package.child_quant_ids = package.quant_ids
                for child in package.child_ids:
                    package.child_quant_ids = package.child_quant_ids | child.quant_ids
            else:
                package.child_quant_ids = False

    def _compute_product_ids(self):
        for package in self:
            if len(package.child_ids.ids) > 0:
                package.product_ids = False
                for child in package.child_ids:
                    package.product_ids = child.quant_ids.mapped('product_id') | package.product_ids
                    #package.freeze_product_ids = package.product_ids
            else:
                package.product_ids = package.quant_ids.mapped('product_id')
                #package.freeze_product_ids = package.product_ids

#    @api.depends('quant_ids.package_id', 'quant_ids.location_id', 'quant_ids.company_id', 'quant_ids.owner_id', 'child_quant_ids')
#    def _compute_package_info(self):
#        for package in self:
#            values = {'location_id': False, 'company_id': self.env.user.company_id.id, 'owner_id': False}
#            if len(package.child_ids.ids) > 0:
#                owner_ids = set()
#                company_ids = set()
#                location_ids = set()
#                for child in package.child_ids:
#                    location_ids.update(child.quant_ids.filtered(lambda r: r.quantity > 0.0).mapped('location_id'))
#                    company_ids.update(child.quant_ids.filtered(lambda r: r.quantity > 0.0).mapped('company_id'))
#                    owner_ids.update(child.quant_ids.filtered(lambda r: r.quantity > 0.0).mapped('owner_id'))
#                location_ids = list(location_ids)
#                company_ids = list(company_ids)
#                owner_ids = list(owner_ids)
#                package.location_id = location_ids and location_ids[0] or False
#                package.company_id = company_ids and company_ids[0] or False
#                package.owner_id = owner_ids and owner_ids[0] or False
#            else:
#                if package.quant_ids:
#                    values['location_id'] = package.quant_ids.filtered(lambda r: r.quantity > 0.0)[0].location_id
#                package.location_id = values['location_id']
#                package.company_id = values['company_id']
#                package.owner_id = values['owner_id']

    @api.multi
    def _red_weight_female(self):
        for package in self:
            package.red_weight_female = (package.company_id.type_package_female != 0.0 and package.weight > package.company_id.type_package_female)

    @api.multi
    def _red_weight_male(self):
        for package in self:
            package.red_weight_male = (package.company_id.type_package_male != 0.0 and package.weight > package.company_id.type_package_male)

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for package in self:
            package.complete_name = package.name
            if package.parent_id:
                package.complete_name = '%s / %s' % (package.parent_id.complete_name, package.name)

    @api.constrains('parent_id')
    def _check_packages_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('Error ! You cannot create recursive included packages.'))
        return True

    @api.model
    def name_create(self, name):
        return self.create({'name': name}).name_get()[0]

    @api.multi
    def name_get(self):
        result = []
        for package in self:
            result.append((package.id, package.complete_name))
        return result

    @api.model
    def create(self, vals):
        tools.image_resize_images(vals)
        return super(QuantPackage, self).create(vals)       

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

    def _get_add_in_pack_context(self):
        #_logger.info("LOCATIONS (%s:%s:%s)" % (self.current_source_location_id, self.current_destination_location_id, self.location_id.id))
        #[warehouse.int_type_id.id],
        warehouse = self.location_id.get_warehouse()
        #warehouse = self.env['stock.warehouse'].search([('lot_stock_id', '=', self.location_id.id)], limit=1)
        return "{'default_picking_type_id': %d, " \
               "'default_owner_id': %d, " \
               "'default_company_id': %d, " \
               "'default_location_id': %d, " \
               "'default_location_dest_id': %d, " \
               "'default_result_package_id': %d, " \
               "'default_state': '%s'}" % \
            (warehouse.int_type_id.id,
             self.owner_id and self.owner_id.id or self.location_id.partner_id and self.location_id.partner_id.id or False,
             self.company_id.id,
             self.location_id.id,
             warehouse.lot_stock_id.id,
             self.id,
             'draft')

    @api.multi
    def action_add_in_pack(self):
        for package in self:
            domain = ['|', ('result_package_id', 'in', self.ids), ('package_id', 'in', self.ids)]
            pickings = self.env['stock.move.line'].search(domain).mapped('picking_id')
            domain = [('id', 'in', pickings.ids)]
            picking_view = self.env.ref('stock.view_picking_form')
            picking_view_tree = self.env.ref('stock.view_picking_internal_search')
            return {
                'name': _('All Package Transfers'),
                'domain': domain,
                'res_model': 'stock.picking',
                'res_id': False,
                'type': 'ir.actions.act_window',
                'view_id': picking_view.id,
                'views': [(picking_view.id, 'form')],
                'view_mode': 'form,tree',
                'view_type': 'form',
                'search_view_id': picking_view_tree.id,
                'help': _('''<p class="oe_view_nocontent_create">
                            Click here to create a new transfer.
                        </p><p>
                            You can either do it immediately or mark it as Todo for future processing. Use your scanner to validate the transferred quantity quicker.
                        </p>'''),
                'limit': 80,
                'context': package._get_add_in_pack_context()
            }
        return False

    def _get_move_pack_context(self):
        #_logger.info("LOCATIONS (%s:%s:%s)" % (self.current_source_location_id, self.current_destination_location_id, self.location_id.id))
        #[warehouse.int_type_id.id],
        warehouse = self.env['stock.warehouse'].search([('lot_stock_id', '=', self.location_id.id)], limit=1)
        return "{'default_picking_type_id': %d, " \
               "'default_package_id': %d, " \
               "'default_owner_id': %d, " \
               "'default_company_id': %d, " \
               "'default_location_id': %d, " \
               "'default_location_dest_id': %d, " \
               "'default_state': '%s'}" % \
            (warehouse.int_type_id.id,
             self._context.get('default_package_id') or self.id,
             self.owner_id.id,
             self.company_id.id,
             self._context.get('default_location_id') or self.location_id.id,
             self._context.get('default_location_dest_id') or self.current_destination_location_id.id,
             'draft')

    @api.multi
    def action_move_pack(self):
        for package in self:
            ret = self.env.ref('stock.action_picking_tree_all').read()[0]
            if self._context.get('default_id', False):
                picking_view = self.env.ref('stock.view_picking_form')
                ret['res_id'] = self._context.get('default_id')
                ret['views'] = [[picking_view.id, "form"]]
                ret['view_id'] = picking_view.id
            if self._context.get('default_ids', False):
                ret['domain'] = [('id', 'in', self._context.get('default_ids'))]
            return ret
        return False

    def action_view_source_picking(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        domain = ['|', ('result_package_id', 'in', self.ids), ('package_id', 'in', self.ids)]
        pickings = self.env['stock.picking'].search(domain)
        action['domain'] = [('id', 'in', pickings.ids)]
        return action

    def save_product_state(self):
        if len(self.product_ids.ids) > 0:
            self.freeze_product_ids = [(6, 0, self.product_ids.ids)]
            self.freeze_date = fields.Date.today()

quantpackage._gather = QuantPackage._compute_package_info
