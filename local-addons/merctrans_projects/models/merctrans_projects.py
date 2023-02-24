# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MercTransServices(models.Model):
    _name = "merctrans.services"
    _rec_name = "services_names"
    _description = "Services offered by MercTrans"

    services_names = fields.Char("Services")
    description = fields.Text("Description")


class MercTransTags(models.Model):
    _name = "merctrans.tags"
    _rec_name = "tag"
    _description = "Project Tags"
    tag = fields.Char(string="Tag", required=True)


class MercTransProjects(models.Model):
    """
    Khởi tạo model
    """

    _name = "merctrans.projects"
    _description = "MercTrans Projects"
    _rec_name = "project_name"
    """
        Static list
    """
    # NOTE: STATIC LIST

    language_list = [
        ("zh-CN", "Chinese (Simplified)"),
        ("zh-TW", "Chinese (Traditional)"),
        ("en-US", "English   (US)"),
        ("en-GB", "English (UK)"),
        ("fr-FR", "French"),
        ("it-IT", "Italian"),
        ("es-ES", "Spanish (Spain)"),
        ("es-AR", "Spanish (Argentina)"),
        ("es-LA", "Spanish (Latin America)"),
        ("th-TH", "Thai"),
        ("tr-TR", "Turkish"),
        ("vi-VN", "Vietnamese"),
        ("ko-KR", "Korean"),
        ("ja-JP", "Japanese"),
        ("ru-RU", "Russian"),
        ("de-DE", "German (Germany)"),
        ("de-AT", "German (Austria)"),
        ("de-CH", "German (Switzerland)"),
    ]

    work_unit_list = [
        ("word", "Word"),
        ("hour", "Hour"),
        ("page", "Page"),
        ("job", "Job"),
    ]

    project_status_list = [
        ("potential", "Potential"),
        ("confirmed", "Confirmed"),
        ("in progress", "In Progress"),
        ("in qa", "In QA"),
        ("delivered", "Delivered"),
        ("canceled", "Canceled"),
    ]

    payment_status_list = [
        ("unpaid", "Unpaid"),
        ("invoiced", "Invoiced"),
        ("partly paid", "Partly Paid"),
        ("paid", "Paid"),
    ]

    # number_id = fields.Integer(string="Stt",
    #                            default=lambda self: self.env['ir.sequence'].
    #                            next_by_code('increment_number_id'))
    # Auto gen number_id
    """
        Field and decorate function, được nhóm chung vào từng section
        để thuận tiện hơn trong chỉnh sửa và debug
    """

    # NOTE: ID AND PROJECT ID, PROJECT NAME, CLIENT, TAGS

    number_id = fields.Integer("No number", index=True, readonly=True, copy=False)

    project_id = fields.Char(
        "Project Id", default="new_project", readonly=True, compute="_get_project_id"
    )

    project_name = fields.Char(
        "Project Name*",
        default=lambda self: f"Project No {self.env['merctrans.projects'].search_count([])}",
    )

    client = fields.Many2one(
        "merctrans.clients",
        string="Client*",
        required=True,
        default=lambda self: self.env["merctrans.clients"].search(
            [("name", "=", "merctrans")], limit=1
        ),
    )

    services_ids = fields.Many2many("merctrans.services", string="Services")

    client_name = fields.Char(
        "Client_", compute="_get_client_name", default="merctrans", readonly=True
    )

    tags = fields.Many2many("merctrans.tags", string="Tags")

    project_manager = fields.Many2one(
        "res.users", string="Project Manager*", required=True,
        domain=lambda self: [('groups_id', 'in', self.env.ref('merctrans_projects.group_merctrans_pm').id)]
    )

    # NOTE: TARGET AND SOURCE LANGUAGE

    source_language = fields.Selection(
        string="Source Languages", selection=language_list
    )

    target_language = fields.Selection(
        string="Target Language", selection=language_list
    )

    # NOTE: TIME, START AND DUE DATE

    current_time = datetime.now().strftime("%Y%m%d-%H%M%s")

    start_date = fields.Date(
        string="Start Date*", required=True, default=fields.Date.today()
    )

    due_date = fields.Date(
        string="Due Date*", required=True, default=fields.Datetime.today()
    )

    # NOTE: SALE, VOLUME, UNIT, RATE, MARGIN

    discount = fields.Integer(string="Discount (%)", default=0)
    # add discount field
    # fixed job

    work_unit = fields.Selection(
        string="Work Unit*", selection=work_unit_list, required=True
    )
    volume = fields.Integer(string="Volume*", required=True, default=0)

    currency_id = fields.Many2one("res.currency", string="Currency*", required=True)
    currency_string = fields.Char(
        string="Currency String", compute="_get_currency_string"
    )

    sale_rate = fields.Float(string="Rate*", required=True, default=0)

    project_value = fields.Float(
        "Project Value",
        compute="_compute_project_value",
        store=True,
        readonly=True,
        default=0,
    )
    project_paid = fields.Float(
        "Amount Paid", compute="_compute_paid", readonly=True, store=True, default=0
    )

    total_po_value = fields.Float(
        "Total PO value",
        compute="_compute_po_value",
        store=True,
        readonly=True,
        default=0,
    )

    project_margin = fields.Float(
        "Project Margin", compute="_compute_margin", store=True, default=0
    )

    margin_status = fields.Integer("Margin Status", compute="_compute_margin_status")

    # NOTE: PROJECT STATUS

    project_instruction = fields.Html("Project Instruction")

    project_status = fields.Selection(
        string="Project Status*",
        selection=project_status_list,
        required=True,
        default="in progress",
    )

    client_po_number = fields.Char(string="Client PO Number")

    payment_status = fields.Selection(
        string="Payment Status*",
        selection=payment_status_list,
        default="unpaid",
        required=True,
        # readonly=True,
        store=True,
        compute="_change_status",
    )

    po_details = fields.One2many(
        "merctrans.pos", "project_id", string="Purchase Orders in this Project"
    )
    so_details = fields.One2many(
        "merctrans.sale", "project_id", string="Sale Orders in this Project"
    )

    # NOTE: FUNCTION AND API DECORATE
    @api.model
    def get_amount_paid(self):
        for project in self:
            project.project_paid = sum(
                sale.value for sale in project.so_details if sale.status == "paid"
            )
        print("Amount paid function executed!")

    @api.model
    def change_status(self):
        for project in self:
            if project.project_paid == 0 and project.project_value:
                project.payment_status = "unpaid"
            elif project.project_paid == 0 and project.project_value != 0:
                project.payment_status = "unpaid"
            elif 0 < project.project_paid < project.project_value:
                project.payment_status = "partly paid"
            elif (
                    project.project_paid == project.project_value
                    and project.project_value != 0
            ):
                project.payment_status = "paid"
            print("Change status executed!")

    @api.model
    def sync_status(self):
        for project in self:
            project.get_amount_paid()
            project.change_status()

        # self.get_amount_paid()
        # self.change_status()
        # print("Sync Status Executed")

    @api.model
    def auto_sync_status(self):
        records = self.env["merctrans.projects"].search([])
        for record in records:
            record.sync_status()

    def _get_client_name(self):
        self.client_name = ""
        for record in self:
            if record.client:
                record.client_name += record.client.name
            else:
                record.client_name = "default bug"

    @api.onchange("currency_id")
    def _get_currency_string(self):
        self.currency_string = ""
        for project in self:
            if project.currency_id:
                project.currency_string += project.currency_id.name

    @api.model
    def create(self, vals):
        print("Project Create Vals ", vals)
        vals["number_id"] = self.env["ir.sequence"].next_by_code(
            "merctrans.project"
        ) or _("New")
        return super(MercTransProjects, self).create(vals)

    @api.model
    def auto_create_sale(self, vals):
        for project in self:
            if not project.so_details:
                res = self.env["merctrans.sale"].create(vals)
                return res

    # @api.model
    # @api.model # đoạn code bên dưới gây bug khi chỉnh sửa project
    # def write(self, vals):
    #     print("Project Write Vals ", vals)
    #     return super(MercTransProjects, self).write(vals)

    # Auto genarate porject_id with client name, datetime and native id

    @api.depends("project_margin")
    def _compute_margin_status(self):
        for project in self:
            if project.project_margin < 0:
                project.margin_status = 0
            else:
                project.margin_status = 1

    @api.onchange("client")
    @api.depends("client")
    def _get_project_id(self):
        create_time = datetime.today().strftime("%y%m%d")
        for project in self:
            if project.client:
                # client is many2many nen can chinh sua lai 1 chut, chi lay ten cua thang dau tien, should be change with project.client
                client_name = (
                    project.client[0].name
                    if len(project.client) > 1
                    else project.client.name
                )
                short_name = "".join(client_name.split()).upper()
                project.project_id = (
                    f"{short_name[:4]}-{create_time}-{project.number_id:05d}"
                )
            else:
                project.project_id = "on change"

    # Volume

    @api.onchange("volume", "sale_rate")
    @api.depends("volume", "sale_rate", "discount")
    def _compute_project_value(self):
        for project in self:
            project.project_value = (
                    (100 - project.discount) / 100 * project.volume * project.sale_rate
            )

    @api.constrains("start_date", "due_date")
    def date_constrains(self):
        for project in self:
            if project.due_date < project.start_date:
                raise ValidationError("Due date must be greater than Start date!")

    @api.depends("po_details")
    def _compute_po_value(self):
        for job in self:
            job.total_po_value = sum(po.po_value for po in job.po_details)

    @api.onchange("project_value", "total_po_value")
    @api.depends("project_value", "total_po_value")
    def _compute_margin(self):
        for project in self:
            if project.project_value > 0:
                project.project_margin = (
                                                 project.project_value - project.total_po_value
                                         ) / project.project_value

    # @api.constrains('currency_id', 'so_details')
    # def currency_constrains(self):
    #     for sale_order in self.so_details:
    #         if sale_order.currency_id != self.currency_id:
    #             raise ValidationError('Currency must be the same!')

    @api.constrains("so_details")
    def total_value_constrains(self):
        total = 0
        for sale_oder in self.so_details:
            total = total + sale_oder.value
            if total > self.project_value:
                raise ValidationError(
                    "Total Sale Order Value must be smaller or equal to Project Value!"
                )

    @api.depends("so_details")
    def _compute_paid(self):
        for project in self:
            project.project_paid = sum(
                sale.value for sale in project.so_details if sale.status == "paid"
            )

    # @api.onchange('project_paid', 'project_value')
    # def change_status(self):
    #     for project in self:
    #         if project.project_paid == 0 and project.project_value:
    #             project.write({'payment_status': 'unpaid'})
    #         elif project.project_paid == 0 and project.project_value != 0:
    #             project.write({'payment_status': 'unpaid'})
    #         elif 0 < project.project_paid < project.project_value:
    #             project.write({'payment_status': 'partly paid'})
    #         elif project.project_paid == project.project_value and project.project_value != 0:
    #             project.write({'payment_status': 'paid'})
    #         else:
    #             project.write({'payment_status': 'unpaid'})

    # @api.onchange('client')
    # def sync_client(self):
    #     for sale_order in self.so_details:
    #         if sale_order:
    #             sale_order.write({'client' : self.client_name},
    #                              {'client_po_number': self.client_po_number},
    #                              {'sale_rate': self.sale_rate})

    def action_send_email(self):
        print("Hello Hoang Long sending email")
        mail_template_id = self.env.ref("merctrans_projects.projects_confirm_email").id
        print("template id", mail_template_id)
        template = self.env["mail.template"].browse(mail_template_id)
        print("template", template)
        for project in self:
            print(project.project_manager.email_formatted)

        template.send_mail(self.id, force_send=True)
