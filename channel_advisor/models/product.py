# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero
from xml.etree.ElementTree import Element, SubElement
from xml.etree import ElementTree
from xml.dom import minidom
import xml.etree.ElementTree as ET
import datetime


class CustomerProduct(models.Model):
    _name ='customer.product.values'
    _description = 'Saves the customer Info of the product'

    product_id = fields.Many2one('product.template', string= 'Product')
    name       = fields.Char(string= 'Name')
    customer_sku = fields.Char(string= 'SKU')
    partner_id  = fields.Many2one('res.partner', string= 'Partner')
    agreed_price = fields.Float(string='Agreed Price')

    _sql_constraints = [
        ('partner_product_uniq', 'unique (partner_id,product_id)', 'The product must be unique per partner !')
    ]


    @api.model
    def get_vendor_sku(self, partner=False, product=False):
        product_record= self.search([('product_id', '=', product.id), ('partner_id', '=', partner.id)], limit=1)
        return product_record and product_record.customer_sku or ''


class ProductTemplate(models.Model):
    _inherit = "product.template"

    customer_product_value_ids = fields.One2many('customer.product.values', 'product_id', string= 'Customer Reference')
    product_customer_sku = fields.Char(related='customer_product_value_ids.customer_sku', string='Customer SKU')
    ca_product_id = fields.Integer()
    ca_profile_id = fields.Integer()


class ProductProduct(models.Model):
    _inherit ='product.product'

    def inventory_update(self):

        xml_string = self.get_pdt_xml()
        date_today  = datetime.datetime.strptime(str(fields.Datetime.now()) , '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
        # save_path_file = "Inventory_%s.xml" % date_today
        save_path_file = "/home/locksmith_keyless_13/odoo13/inventory_updates/" +"Inventory_%s.xml" % date_today
        with open(save_path_file, "w") as f:
            f.write(xml_string)
        return True

    def get_pdt_xml(self):

        xmlns_uris = {'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
                      'web': 'http://api.channeladvisor.com/webservices/'}
        try :
            products = self.search([('type', '=', 'product')])
            root_node = ET.Element("soapenv:Envelope")
            soap_header = SubElement(root_node, 'soapenv:Header')
            api_cred= SubElement(soap_header, 'web:APICredentials')
            SubElement(api_cred, 'web:DeveloperKey').text = 'test'
            SubElement(api_cred, 'web:Password').text = 'test'
            soap_body = SubElement(root_node, 'soapenv:Body')
            item_qty_price = SubElement(soap_body, 'web:UpdateInventoryItemQuantityAndPriceList')
            for product in products:
                qty = product.qty_available - product.outgoing_qty
                update_item_qty_price = SubElement(item_qty_price, 'web:InventoryItemQuantityAndPrice')
                SubElement(update_item_qty_price, 'web:Sku').text = str(product.default_code)
                SubElement(update_item_qty_price, 'web:Quantity').text = str(qty)
                # SubElement(update_item_qty_price, 'web:DistributionCenterCode').text = product.location_id.name
                SubElement(update_item_qty_price, 'web:UpdateType').text = 'UNSHIPPED'
                price_info = SubElement(item_qty_price, 'web:PriceInfo')
                SubElement(price_info, 'web:Cost').text = str(product.standard_price)
                SubElement(price_info, 'web:RetailPrice').text = str(product.lst_price)
                SubElement(price_info, 'web:StorePrice').text = str(product.lst_price)

            self.add_XMLNS_attributes(root_node, xmlns_uris)
            rough_string = ET.tostring(root_node, encoding='UTF-8', method='xml')
            reparsed = minidom.parseString(rough_string)
            return reparsed.toprettyxml(indent="  ")
        except Exception as e:
            raise UserError("Exception in Inventory processing\n %s " % e)


    def add_XMLNS_attributes(self,tree, xmlns_uris_dict):
        if not ET.iselement(tree):
            tree = tree.getroot()
        for prefix, uri in xmlns_uris_dict.items():
            tree.attrib['xmlns:' + prefix] = uri



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
