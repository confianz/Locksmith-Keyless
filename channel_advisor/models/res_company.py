# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = "res.company"


    shipping_cost_product_id = fields.Many2one('product.product', string="Shipping Cost Product")
    tax_product_id = fields.Many2one('product.product', string="Tax Product")
    gift_product_id = fields.Many2one('product.product', string="Gift Product")



ResCompany()
