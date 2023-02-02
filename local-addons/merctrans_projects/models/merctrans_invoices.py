# -*- coding: utf-8 -*-
from datetime import datetime

from odoo.exceptions import ValidationError

from odoo import api, fields, models




class MercTransInvoices(models.Model):
    _name = 'merctrans.invoices'
    _rec_name = 'invoice_name'
    _description = 'MercTrans Invoices for Project Managers'

    status_list = [('invoiced', 'Invoiced'), ('paid', 'Paid'),
                   ('unpaid', 'Unpaid')]

    invoice_id = fields.Integer('Invoice ID',
                                index=True,
                                store=True,
                                readonly=True,
                                default=lambda self: self.env['ir.sequence'].
                                next_by_code('increment_invoice_id'))

    sender_info = fields.Text(string='Sender Info*',
                              required=True)

    invoice_name = fields.Char(string='Invoice #', compute="_get_invoice_name")

    invoice_date = fields.Date(string='Issue Date*', default=datetime.today(), required=True)

    invoice_due_date = fields.Date(string='Due Date*', required=True)

    invoice_client = fields.Many2one('merctrans.clients',
                                     string='Client',
                                     required='True')

    client_name = fields.Char(compute="_get_invoice_client")

    invoice_details_ids = fields.Many2many('merctrans.sale',
                                           string='Sale Orders', domain="[('client', '=', client_name)]")
    # Currency computed from sale orders (sale order restrains same currency)
    currency_id = fields.Char(string='Currency*',
                              required=True,
                              compute="_get_currency")

    invoice_value = fields.Float("Sub Total",
                                 compute="_compute_invoice_value")

    invoice_status = fields.Selection(string="Invoice Status",
                                      selection=status_list,
                                      default='invoiced')

    discount = fields.Integer(string='Discount (%)', default=0)

    invoice_total = fields.Float('Total', compute="_compute_invoice_total", store=True, readonly=True, default=0)

    invoice_paid_date = fields.Date(string='Paid Date')

    # Functions and Decorators below
    @api.constrains('invoice_details_ids')
    def _constrains_currency(self):
        for rec in self:
            for sale in rec.invoice_details_ids:
                if sale.currency_id != rec.currency_id:
                    raise ValidationError("Sale Order Currencies must be the same")

    @api.onchange('client_name')
    def _onchange_client_name(self):
        for rec in self:
            search = {'domain': {'invoice_details_ids': [('client', '=', rec.client_name)]}}
            return search

    @api.onchange('invoice_total')
    @api.depends('invoice_value', 'invoice_total', 'discount')
    def _compute_invoice_total(self):
        for invoice in self:
            invoice.invoice_total = (100 - invoice.discount) / 100 * invoice.invoice_value

    @api.depends('invoice_client')
    @api.onchange('invoice_client')
    def _get_invoice_client(self):
        self.client_name = ''
        for inv in self:
            if inv.invoice_client:
                inv.client_name += inv.invoice_client.name
            else:
                inv.client_name = 'default'

    @api.depends('invoice_client', 'invoice_id')
    @api.onchange('invoice_client', 'invoice_id')
    def _get_invoice_name(self):
        for inv in self:
            if inv.invoice_client:
                cl_name = "".join(inv.invoice_client.name.split()).upper()
            else:
                cl_name = "CLIE"
            inv.invoice_name = f"INV{inv.invoice_id:05d}-{cl_name[:4]}-{fields.Date.today().strftime('%y%m%d')}"

    @api.depends('invoice_details_ids')
    @api.onchange('invoice_details_ids')
    def _compute_invoice_value(self):
        for item in self:
            item.invoice_value = 0
            for sale in item.invoice_details_ids:
                if item.invoice_details_ids:
                    item.invoice_value += sale.value
                else:
                    item.invoice_value = 0

    @api.constrains('invoice_details_ids', 'invoice_client')
    def client_constrains(self):
        for inv in self:
            for sale_order in inv.invoice_details_ids:
                if inv.client_name != sale_order.client:
                    raise ValidationError('You can only include jobs from the same client!')

    @api.onchange('invoice_details_ids')
    def _get_currency(self):
        for rec in self:
            if rec.invoice_details_ids:
                rec.currency_id = rec.invoice_details_ids[0].currency_id
            else:
                rec.currency_id = "USD"

    @api.constrains('invoice_paid_date', 'invoice_date', 'invoice_status')
    def paid_date_constrains(self):
        for inv in self:
            if inv.invoice_paid_date and inv.invoice_paid_date < inv.invoice_date:
                raise ValidationError('Invoice paid date cannot be before invoice due date')

    @api.constrains('invoice_details_ids')
    def invoice_detail_constrains(self):
        for inv in self:
            if not inv.invoice_details_ids:
                raise ValidationError('Invoice must have at least one project!')

    @api.constrains('invoice_details_ids', 'invoice_status')
    def invoice_status_constrains(self):
        for inv in self:
            if not inv.invoice_details_ids and inv.invoice_status:
                raise ValidationError('Cannot set invoice status when there is no job!')\


    @api.onchange('invoice_status')
    def sync_payment_status(self):

        for sale_order in self.invoice_details_ids:
            if self.invoice_status == 'paid':
                sale_order.write({'status': 'paid'})

            if self.invoice_status == 'invoiced':
                sale_order.write({'status': 'invoiced'})

            if self.invoice_status == 'unpaid':
                sale_order.write({'status': 'unpaid'})

            if not self.invoice_status:
                sale_order.write({'status': 'unpaid'})

    @api.ondelete(at_uninstall=False)
    def _check_status(self):
        for invoice in self:
            if invoice.invoice_status == "paid":
                raise ValidationError("You cannot delete an invoice with status set to Paid!")