import re
from odoo.exceptions import ValidationError
from odoo import api, fields, models


class MerctransClient(models.Model):

    _name = 'merctrans.clients'

    _rec_name = 'name'

    _description = "Merctrans's Clients"

     # partner_id = fields.Many2one('res.partner', required=True, ondelete='restrict', auto_join=True,
    #                              string='Related Partner', help='Partner-related data of the user')

    payment_term_list = [('30 days', '30D'),
                           ('45 days', '45D'),
                           ('60 days', '60D'),
                           ('90 days', '90D')]

    payment_method_list = [('paypal', 'PayPal'),
                           ('wire transfer', 'Wire Transfer'),
                           ('payoneer', 'Payoneer')]

    name = fields.Char(string='Account Name*')

    client_short_name = fields.Char(string='Account ID*', readonly=True, compute='_get_client_id')

    email = fields.Char(string='Email')

    country = fields.Many2one('res.country', string='Country')

    client_note = fields.Html('Account note')

    phone_number = fields.Char(string='Phone number')

    website = fields.Char(string='Website')

    services = fields.Many2many('merctrans.services', string = 'Services')

    sales_person = fields.Many2one('res.users', string='Salesperson')

    payment_term = fields.Selection(selection=payment_term_list, string='Payment Term')

    payment_method = fields.Selection(selection=payment_method_list, string='Payment Method')

    create_date = fields.Date(string='Create Date', readonly=True)

    write_date = fields.Datetime(string='Last Update', readonly=True)

    project_history = fields.One2many('merctrans.projects',
                                      'client',
                                      readonly=True)

    invoice_history = fields.One2many('merctrans.invoices',
                                      'invoice_client', readonly=True)
                                      # domain=[('invoice_status', '=', 'unpaid')
                                      #         ])
    client_contact_list = fields.One2many('account.contacts','contact_account', readonly=True)

    # client_currency = fields.Many2one('res.currency',
    #                                   string="Currency",)

    @api.constrains('name')
    def check_duplicate_name(self):
        for company_rec in self:
            company_rec = self.env['merctrans.clients'].search([
                ('name', '=', self.name), ('id', '!=', self.id)
            ])
            if company_rec:
                raise ValidationError('Company name cannot be duplicated!')

    @api.constrains('email')
    def validate_email(self):
        for client in self:
            if client.email:
                match = re.match(
                    '^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$',
                    client.email)
            else:
                match = "Not created"
            if match is None:
                raise ValidationError('Not a valid email')

    @api.onchange('name')
    @api.depends('name')
    def _get_client_id(self):
        for client in self:
            if client.name:
                short_name = "".join(client.name.split()).upper()
            else:
                short_name = "DEFA"
            client.client_short_name = f"{short_name[:4]}"

class AccountContact(models.Model):

    _name = 'account.contacts'
    _rec_name = 'contact_name'
    _description = 'MercTrans Account Contact list'


    contact_account = fields.Many2one('merctrans.clients', required=True)
    contact_name = fields.Char(string='Name')
    contact_position = fields.Char(string='Position')
    contact_email = fields.Char(string='Email')
    contact_phone = fields.Char(string='Phone Number')
    contact_note = fields.Text(string='Note')

    @api.constrains('contact_email')
    def validate_email(self):
        if self.contact_email:
            match = re.match(
                '^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$',
                self.contact_email)
        if match is None:
            raise ValidationError('Not a valid email')