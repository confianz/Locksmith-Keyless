# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
import json
import requests
from dateutil import parser


class TransactionLogger(models.Model):
    _name = "transaction.log"
    _description = "Transaction Log Details"
    _order = 'id desc'

    name = fields.Char(string='Name')
    message = fields.Text(string='Error Message')
    attachment_id = fields.Many2one('ir.attachment', 'File')
    sale_id = fields.Many2one('sale.order', 'Sale Order')
    def convert_date_time(self, date_str):
        try:

            date_str1 = parser.parse(date_str)
            res = date_str1.strftime('%m/%d/%Y %H:%M:%S')
            return res

        except:
            raise UserError("Date format is invalid %s" % date_str)


    def _get_values(self, node):

        res = {}
        ship_info = {}
        bill_info = {}
        if node.get('ID'):
            res.update({'order_no': node.get('ID')})
        if node.get('SiteName') :
            res.update({'SiteName': node.get('SiteName')})
        if  not res.get('lines'):
            res.update({'lines': {}})
        if node.get('SiteOrderID'):
            res.update({'mkt_order_no': node.get('SiteOrderID')})
        if node.get('CreatedDateUtc'):
            create_date = self.convert_date_time(node.get('CreatedDateUtc'))
            res.update({'date_order ': create_date})
        if node.get('ShippingAddressLine1'):
            ship_info.update({
                'address1':node.get('ShippingAddressLine1'),
            })
        if node.get('ShippingAddressLine2'):
            ship_info.update({
                'address2': node.get('ShippingAddressLine2'),
            })
        if node.get('ShippingCity'):
            ship_info.update({
                'City': node.get('ShippingCity'),
            })
        if node.get('ShippingStateOrProvinceName'):
            ship_info.update({
                'RegionDescription': node.get('ShippingStateOrProvinceName'),
            })
        if node.get('ShippingPostalCode'):
            ship_info.update({
                'PostalCode': node.get('ShippingPostalCode'),
            })
        if node.get('ShippingCountry'):
            ship_info.update({
                'CountryCode': node.get('ShippingCountry'),
            })
        if node.get('ShippingFirstName'):
            ship_info.update({
                'FirstName': node.get('ShippingFirstName'),
            })
        if node.get('ShippingLastName'):
            ship_info.update({
                'LastName': node.get('ShippingLastName'),
            })
        if node.get('ShippingDaytimePhone'):
            ship_info.update({
                'PhoneNumberDay': node.get('ShippingDaytimePhone'),
            })
        res.update({'ship_info': ship_info})

        if node.get('BillingAddressLine1'):
            bill_info.update({
                'address1': node.get('BillingAddressLine1'),
            })
        if node.get('BillingAddressLine2'):
            bill_info.update({
                'address2': node.get('BillingAddressLine2'),
            })
        if node.get('BillingCity'):
            bill_info.update({
                'City': node.get('BillingCity'),
            })
        if node.get('BillingStateOrProvinceName'):
            bill_info.update({
                'RegionDescription': node.get('BillingStateOrProvinceName'),
            })
        if node.get('BillingPostalCode'):
            bill_info.update({
                'PostalCode': node.get('BillingPostalCode'),
            })
        if node.get('BillingCountry'):
            bill_info.update({
                'CountryCode': node.get('BillingCountry'),
            })
        if node.get('BillingFirstName'):
            bill_info.update({
                'FirstName': node.get('BillingFirstName'),
            })
        if node.get('BillingLastName'):
            bill_info.update({
                'LastName': node.get('BillingLastName'),
            })
        if node.get('BillingDaytimePhone'):
            bill_info.update({
                'PhoneNumberDay': node.get('BillingDaytimePhone'),
            })
        res.update({'bill_info':bill_info})
        if node.get('TotalShippingPrice'):
            res.update({
                'TotalShippingPrice': node.get('TotalShippingPrice'),
            })
        if node.get('TotalPrice'):
            res.update({
                'TotalPrice': node.get('TotalPrice'),
            })
        if node.get('SpecialInstructions'):
            res.update({
                'SpecialInstructions': node.get('SpecialInstructions'),
            })
        if node.get('PrivateNotes'):
            res.update({
                'PrivateNotes': node.get('PrivateNotes'),
            })
        if node.get('Items'):
            for line_item in node.get('Items'):
                if line_item.get('ID'):
                    LineItemID = line_item.get('ID')
                    res['lines'].update({LineItemID: {}})
                    res['lines'][LineItemID].update({'UnitPrice': float(line_item.get('UnitPrice') or 0.0)})
                    res['lines'][LineItemID].update({'Quantity': float(line_item.get('Quantity') or 0)})
                    res['lines'][LineItemID].update({'SKU': line_item.get('Sku') or ''})
                    res['lines'][LineItemID].update({'Title': line_item.get('Title') or ''})

        return res

    def find_or_create_address(self, customer, address, address_type='delivery'):
        """
        FInd or create partner address
        :param address: dict, dictionary containg addres information
        :param address_type: string 'delivery' or 'invoice'
        :return: Partner Address recordset
        """

        street  = address.get('address1', '')
        street1  = address.get('address2', '')
        state = address.get('RegionDescription', '')
        city = address.get('City', '')
        zip_code = address.get('PostalCode', '')
        domain = [('type', '=', address_type), ('parent_id', '=', customer.id), ('active', '=', True), ('city', '=ilike', city),
                  ('zip', '=', zip_code), ]
        # if 'Contacts' in address:
        #     domain.append(('name', '=', address.get('Contacts', {}).get('ContactName', '')))
        # else:
        #     domain.append(('name', '=', address.get('AddressName', {})))
        # contact = customer.search(domain)
        # if not contact:

        if street:
            domain.append(('street', '=ilike', street))
        if street1:
            domain.append(('street2', '=ilike', street1))
        if state:
            domain.append(('state_id.name', '=', state))
        del_addr = self.env['res.partner'].search(domain, limit=1)
        if not del_addr:
            if  address.get('CountryCode', ''):
                Country = self.env['res.country'].search([('code', '=', address.get('CountryCode', ''))])
                State = False
                if Country:
                    State = self.env['res.country.state'].search(
                        [('name', '=', address.get('RegionDescription', '')), ('country_id', '=', Country.id)])

            vals = {
                'name':  address.get('FirstName', '') +  '' + address.get('LastName', '') or '',
                'phone': address.get('PhoneNumberDay', '') or '',
                'street': street or '',
                'street2': street1 or '',
                'zip': address.get('PostalCode', '') or '',
                'city': address.get('City', '') or '',
                'state_id': State and State.id or False,
                'country_id': Country and Country.id or False,
                'type': address_type,
                'parent_id': customer.id
            }

            del_addr = customer.create(vals)
        return del_addr
    def process_line_item(self, line, customer):
        """
        Process line item and return dict of values to create sale line
        :param line: dict
        :return: dict
        """
        # Product = self.env['customer.product.values'].search([
        #     ('product_id.active', '=', True),
        #     ('partner_id', '=', customer.id),
        #     ('customer_sku', '=', line.get('SKU')),
        # ], limit=1)
        # if  Product:
        #     product = self.env['product.product'].search([('product_tmpl_id', '=', Product.id)])
        #
        # else:
        vals ={}
        product = self.env['product.product'].search([('default_code', '=', line.get('SKU')), ('ca_product_id', '=', True)])
        if not product:
            # product = self.env['product.product'].search(
            #     [('default_code', '=', 'TEST001')])
            raise UserError('Product %s not in Product Master' % line.get('Title'))
        if line.get('UnitPrice', '') != product.lst_price:
            vals.update({"is_review":True})
        else:
            vals.update({"is_review": False})
        vals = {

            'product_id': product.id,
            'product_uom_qty': line.get('Quantity', 0),
            'name': line.get('Title', 0) or product.name,
            # 'tax_id': [[6, 0, taxes]],
            'price_unit': line.get('UnitPrice', ''),
            'purchase_price':product.standard_price

        }
        return vals


    def create_order(self, data):
        """
        Create SaleOrder from EDI data
        :param data: dict
        :return: Order recordset
        """
        delivery_address = False
        invoice_address = False
        is_review_lst =[]
        is_review = False
        if data.get('SiteName'):
            site = data.get('SiteName')
            Customer = self.env['res.partner'].search(
                [('name', '=ilike', site)])
            if not Customer:
                Customer = self.env['res.partner'].search(
                    [('name', '=ilike', 'Checkout Direct')])
                # raise UserError('Customer Not Found')
        if data.get('bill_info', '') :
            address = data.get('bill_info', '')
            invoice_address = self.find_or_create_address(Customer, address, 'invoice')
        if data.get('ship_info', '') :
            address = data.get('ship_info', '')
            delivery_address = self.find_or_create_address(Customer, address, 'delivery')
        vals = {
            'partner_id':Customer.id,
            'is_edi_order': True,
            'chnl_adv_order_id': data.get('order_no'),
            'client_order_ref':  data.get('mkt_order_no'),
            'partner_shipping_id': delivery_address and delivery_address.id or Customer.id,  # 59,#
            'partner_invoice_id': invoice_address and invoice_address.id or Customer.id,  # 60,#
            'special_instruction': data.get('SpecialInstructions'),
            'private_note': data.get('PrivateNotes'),
            'total_price': data.get('TotalPrice'),
            #     # 'carrier_id': carrier and carrier.id or False,
            #     # 'note': notes,
        }

        line_vals = []
        for line in data.get('lines'):
            get_lines = self.process_line_item(data.get('lines').get(line), Customer)
            is_review_lst.append(get_lines.pop('is_review', False))
            line_vals.append((0, 0, get_lines))
        pdt = self.env.user.company_id.shipping_cost_product_id
        if pdt :
            line_vals.append((0, 0, {'product_id': pdt.id,'price_unit': data.get('TotalShippingPrice', ''),'name':pdt.name}))

        is_review = any(is_review_lst)
        vals.update({'order_line':line_vals,'is_review':is_review})
        SaleOrder = self.env ['sale.order']
        saleorder = SaleOrder.search(
            [('partner_id', '=', Customer.id), ('client_order_ref', '=', data.get('mkt_order_no')),('state', 'in', ['draft','sent'])])
        if saleorder:
            saleorder.write(vals)
        else:
            saleorder = SaleOrder.create(vals)
            if Customer.name != 'Checkout Direct':
                saleorder.action_confirm()
        return saleorder


    def _import_orders(self):
        cr = self.env.cr
        connector =self.env['ca.connector'].search([],limit=1)
        date_filter = False
        if connector.orders_imported_date:
            date_filter = "CreatedDateUtc ge %s" %connector.orders_imported_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        res = connector.call('import_orders', filter=date_filter)
        for values in res.get('value', []):
            try:
                vals = self._get_values(values)
                TransactionLog = self.create({
                    'name': "Import Order",
                })
                error_message = ''
                try:
                    SaleOrder = TransactionLog.create_order(vals)
                except Exception as e:
                    error_message = e
                    SaleOrder = False
                if SaleOrder:
                    TransactionLog.write(
                        {'message': 'Order created succesfully', 'sale_id': SaleOrder.id, 'name': SaleOrder.name})
                else:
                    if error_message:
                        TransactionLog.write({'message': error_message,'name': "Error in Order Import"})
                cr.commit()
            except Exception as e:
                cr.rollback()
        if res.get('@odata.nextLink') and connector:
            connector.order_import_nextlink =res.get('@odata.nextLink', '').split('$skip=')[1]
            connector.action_import_orders()
        else:
            connector.write({
                'orders_import_nextlink': '',
                'orders_imported_date': datetime.now(),
            })


        return True




