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
    sender_info = fields.Text(string='Sender Info*')
    invoice_name = fields.Char(string='Invoice #', compute="_get_invoice_name")
    invoice_date = fields.Date(string='Issue Date*', default=datetime.today(), required=True)
    invoice_due_date = fields.Date(string='Due Date*', required=True)
    invoice_client = fields.Many2one('merctrans.clients',
                                     string='Client',
                                     required='True')
    client_name = fields.Char(compute="_get_invoice_client")

    invoice_details_ids = fields.Many2many('merctrans.projects',
                                           string='Invoice Lines')
    currency_id = fields.Many2one('res.currency', string='Currency')
    invoice_value = fields.Float("Sub Total",
                                 compute="_compute_invoice_value")
    invoice_status = fields.Selection(string="Invoice Status",
                                      selection=status_list,
                                      default='unpaid')
    discount = fields.Integer(string='Discount (%)', default=0)
    invoice_total = fields.Float('Total', compute="_compute_invoice_total", store=True, readonly=True, default=0)
    invoice_paid_date = fields.Date(string='Paid Date', default=datetime.today())


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
    def _compute_invoice_value(self):
        for item in self:
            item.invoice_value = sum(line.project_value  # x??? rename plz
                                     for line in item.invoice_details_ids)

    @api.constrains('invoice_details_ids', 'currency_id')
    def currency_constrains(self):
        for job in self:
            for x in job.invoice_details_ids:
                if job.currency_id != x.currency_id:
                    raise ValidationError(
                        'Job currency must be the same as invoice currency!')

    @api.constrains('invoice_details_ids', 'invoice_client')
    def client_constrains(self):
        for inv in self:
            for job in inv.invoice_details_ids:
                if inv.client_name != job.client_name:
                    raise ValidationError('You can only include jobs from the same client!')


    @api.constrains('invoice_paid_date','invoice_date', 'invoice_status')
    def paid_date_constrains(self):
        for inv in self:
            if inv.invoice_paid_date and inv.invoice_paid_date < inv.invoice_date:
                raise ValidationError('Invoice paid date cannot be before invoice due date')
            if inv.invoice_status != 'paid' and inv.invoice_paid_date:
                raise ValidationError('Cannot have paid date when status is not Paid')

    @api.constrains('invoice_details_ids')
    def invoice_detail_constrains(self):
        for inv in self:
            if not inv.invoice_details_ids:
                raise ValidationError('Invoice must have at least one project!')

    @api.constrains('invoice_details_ids', 'invoice_status')
    def invoice_status_constrains(self):
        for inv in self:
            if not inv.invoice_details_ids and inv.invoice_status:
                raise ValidationError('Cannot set invoice status when there is no job!')

    # @api.model
    # def create(self, vals):
    #     print("Invoices Create Vals ", vals)
    #     return super(MercTransInvoices, self).create(vals)
    #
    # def write(self, vals):
    #     print("Invoices Write Vals ", vals)
    #     return super(MercTransInvoices, self).write(vals)

    @api.onchange('invoice_status')
    def sync_status(self):

        for project in self.invoice_details_ids:
            if self.invoice_status == 'paid':
                project.write({'payment_status': 'paid'})
            if self.invoice_status == 'invoiced':
                project.write({'payment_status': 'invoiced'})
            if self.invoice_status == 'unpaid':
                project.write({'payment_status': 'unpaid'})
            if not self.invoice_status:
                project.write({'payment_status': 'unpaid'})

    @api.ondelete(at_uninstall=False)
    def _check_invoice_status(self):
        for rec in self:
            if rec.invoice_status:
                raise ValidationError("You cannot delete an invoice with invoice status set!")