# -*- coding: utf-8 -*-

import base64
import requests
from datetime import datetime, timedelta

from odoo import api, fields, models, _


class CAConnector(models.Model):
    _name = "ca.connector"
    _description = "Channel Advisor Connector"

    name = fields.Char(string="Name")
    description = fields.Char(string="Description")
    application_id = fields.Char(string="Application ID")
    shared_secret = fields.Char(string="Shared Secret")
    refresh_token = fields.Char(string="Refresh Token")
    access_token = fields.Char(string="Access Token")
    client_id = fields.Char(compute="_compute_client_id", store=True)
    expiry_date = fields.Datetime(string="Expire At")
    state = fields.Selection([
        ('draft', 'Inactive'),
        ('active', 'Active'),
    ], string="Status", default="draft")
    auto_import_orders = fields.Boolean(string="Auto Import Orders?", default=True)
    orders_imported_date = fields.Datetime(string="Orders Last Imported Date")
    auto_import_products = fields.Boolean(string="Auto Import Products?", default=True)
    products_imported_date = fields.Datetime(string="Products Last Imported Date")

    @api.depends('application_id', 'shared_secret')
    def _compute_client_id(self):
        for rec in self:
            auth_code = "%s:%s" % (rec.application_id, rec.shared_secret)
            client_id = base64.b64encode(auth_code.encode("utf-8"))
            rec.client_id = client_id.decode("utf-8")

    def _refresh_access_token(self):
        endpoint_url = "https://api.channeladvisor.com/oauth2/token"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        body = {'grant_type': 'refresh_token'}

        for rec in self:
            headers['Authorization'] = "Basic %s" % rec.client_id
            body['refresh_token'] = rec.refresh_token

            res = requests.post(endpoint_url, headers=headers, data=body)

            if 'access_token' in res.json():
                expires_in = res.json().get('expires_in', 3600) - 300
                rec.write({
                    'access_token': res.json().get('access_token'),
                    'expiry_date': datetime.now() + timedelta(seconds=expires_in),
                })

        return True

    def _access_token(self):
        self.ensure_one()
        if not self.access_token or self.expiry_date < datetime.now():
            self._refresh_access_token()

        return self.access_token

    def action_refresh_access_token(self):
        self.ensure_one()
        self._refresh_access_token()

    def action_confirm(self):
        self.ensure_one()
        self._refresh_access_token()
        if self.access_token:
            self.state = 'active'
        return True

    def action_reset(self):
        self.ensure_one()
        self.state = 'draft'

    def action_import_product(self):
        self.ensure_one()
        Product = self.env['product.product'].sudo()
        resource_url = "https://api.channeladvisor.com/v1/Products?access_token=%s" % self._access_token()
        res = requests.get(resource_url)
        for vals in res.json().get('value', []):
            product = Product.search([('default_code', '=', vals.get('Sku'))])
            if product:
                product.write({
                    'name': vals.get('Title'),
                    'height': vals.get('Height'),
                    'width': vals.get('Width'),
                    'depth': vals.get('Length'),
                    'weight': vals.get('Weight'),
                    'standard_price': vals.get('Cost'),
                })
            else:
                Product.create({
                    'name': vals.get('Title'),
                    'default_code': vals.get('Sku'),
                    'ca_product_id': vals.get('ID'),
                    'ca_profile_id': vals.get('ProfileID'),
                    'height': vals.get('Height'),
                    'width': vals.get('Width'),
                    'depth': vals.get('Length'),
                    'weight': vals.get('Weight'),
                    'standard_price': vals.get('Cost'),
                })

        return True


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

