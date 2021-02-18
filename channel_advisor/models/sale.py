# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
# from ftplib import FTP
# from StringIO import StringIO
from xml.etree.ElementTree import Element, SubElement
from xml.etree import ElementTree
from xml.dom import minidom
import datetime


class SaleOrder(models.Model):
    _inherit = "sale.order"

    chnl_adv_order_id = fields.Char('CA OrderID')
    is_edi_order = fields.Boolean(string='EDI Sales Order', copy=False)
    is_review = fields.Boolean(string='Review', copy=False)
    margin_percent = fields.Float('Margin%', compute='_product_margin_percent', store=True)
    special_instruction = fields.Html('SpecialInstructions')
    private_note = fields.Html('PrivateNotes')
    total_price = fields.Float('TotalPrice')

    @api.depends('margin', 'amount_untaxed')
    def _product_margin_percent(self):
        for order in self:
            if order.margin and order.amount_untaxed:
                order.margin_percent = order.margin/order.amount_untaxed* 100



SaleOrder()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    margin = fields.Float(compute='_product_margin', digits='Product Price', store=True)
    margin_percent = fields.Float('Margin%', compute='_product_margin_percent', store=True)
    promotion_amt = fields.Float("Promotion")

    @api.depends('product_id', 'purchase_price', 'product_uom_qty', 'price_unit', 'price_subtotal')
    def _product_margin(self):
        for line in self:
            currency = line.order_id.pricelist_id.currency_id
            price = line.purchase_price
            margin = line.price_subtotal - (price * line.product_uom_qty)
            line.margin = currency.round(margin) if currency else margin

    @api.depends('product_id', 'purchase_price', 'product_uom_qty', 'price_unit', 'price_subtotal')
    def _product_margin_percent(self):
        for line in self:
            price = line.purchase_price
            margin = line.price_subtotal - (price * line.product_uom_qty)
            if line.price_subtotal:
                line.margin_percent = margin / line.price_subtotal * 100

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id','promotion_amt')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            if line.promotion_amt:
                price = (line.price_unit+line.promotion_amt)* (1 -(line.discount or 0.0) / 100.0)
            else:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups(
                    'account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

SaleOrderLine()




