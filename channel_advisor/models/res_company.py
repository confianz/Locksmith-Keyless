# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = "res.company"


    shipping_cost_product_id = fields.Many2one('product.product', string="Shipping Cost Product")



ResCompany()
