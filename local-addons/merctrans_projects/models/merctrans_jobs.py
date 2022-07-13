from odoo.exceptions import ValidationError

from odoo import api, fields, models


class MerctransJobs(models.Model):
    _name = 'merctrans.jobs'
    _description = "Jobs by Projects"
    _rec_name = "title"
    job_status_list = [('in progress', 'In Progress'),
                       ('completed', 'Completed'), ('canceled', 'Canceled')]

    work_unit_list = [('word', 'Word'), ('hour', 'Hour'), ('page', 'Page'),
                      ('job', 'Job')]

    payment_status_list = [('unpaid', 'Unpaid'), ('invoiced', 'Invoiced'),
                           ('paid', 'Paid')]
    # Detail Job

    title = fields.Char('Job Title', default='Job Title')
    pic = fields.Many2one('res.users', 'PIC', required=True)
    address = fields.Char('Address',
                          store=True,
                          readonly=True,
                          compute='_get_street_pic')
    pic_id = fields.Char('Id',
                         store=True,
                         readonly=True,
                         compute='_get_id_pic')
    pic_email = fields.Char('Email',
                            store=True,
                            readonly=True,
                            compute='_get_email_pic')
    source_language = fields.Char('Source Language',
                                  default="English",
                                  store=True,
                                  compute='_get_project_source',
                                  readonly=True)
    target_language = fields.Char('Target Language',
                                  default="Vietnamess",
                                  readonly=True,
                                  compute='_get_project_target')
    currency_id = fields.Many2one('res.currency', string='Currency')
    work_unit = fields.Selection(string='Work Unit*',
                                 selection=work_unit_list,
                                 required=True)
    volume = fields.Integer(string='Volume*', required=True, default=0)

    sale_rate_per_work_unit = fields.Float(string='Sale rate per Work Unit',
                                           required=True,
                                           default=0)
    payment_status = fields.Selection(string='Payment Status',
                                      selection=payment_status_list,
                                      default='Payment Status')

    job_value = fields.Float("Project Value",
                             compute="_compute_job_value",
                             store=True,
                             readonly=True,
                             default=0)
    valid_date = fields.Char('Valid Date',
                             default="Choose Project",
                             readonly=True,
                             compute='_get_project_valid_date')
    start_date = fields.Date(string='Start Date',
                             default="_get_default_start_date")
    due_date = fields.Date(string='Due Date', default="_get_default_due_date")

    #  TODO: code = auto gen code unique

    # From Projects?
    project_id = fields.Many2one('merctrans.projects',
                                 string="Project",
                                 required=True)
    job_status = fields.Selection(string='JOB STATUS',
                                  selection=job_status_list)
    service = fields.Many2one('merctrans.services', string='Service')

    # Currency - get from partner Currency

    #  TODO: - Cần thêm fields currency cho res.partner

    # TODO: - Cần thêm fields rate cho model -> but? Tính kiểu ?

    # get Source default

    # TODO: Sau khi có currency change street = currency EZ???

    # Get pic address
    @api.onchange('pic')
    @api.depends('pic')
    def _get_street_pic(self):
        self.ensure_one()
        print(self.pic.street)
        self.address = self.pic.street

    # Get api email
    @api.onchange('pic')
    @api.depends('pic')
    def _get_email_pic(self):
        for project in self:
            print(project.pic.email)
            project.pic_email = project.pic.email

    @api.onchange('pic')
    @api.depends('pic')
    def _get_id_pic(self):
        for project in self:
            print(project.pic.id)
            project.pic_id = project.pic.id

    @api.onchange('project_id')
    @api.depends('project_id')
    def _get_project_source(self):
        self.source_language = self.project_id.source_language

    @api.onchange('project_id')
    @api.depends('project_id')
    def _get_project_valid_date(self):
        for project in self:
            if project.project_id.start_date:
                project.valid_date = f"{project.project_id.start_date} >> {project.project_id.due_date}"
            else:
                project.valid_date = "Choose Project"

    @api.onchange('project_id')
    @api.depends('project_id')
    def _get_default_start_date(self):
        for project in self:
            return project.project_id.start_date

    @api.onchange('project_id')
    @api.depends('project_id')
    def _get_default_due_date(self):
        for project in self:
            return project.project_id.due_date

    @api.onchange('project_id')
    @api.depends('project_id')
    def _get_project_target(self):
        for project in self:
            project.target_language = project.project_id.target_language

    # Job start date must greater than project start date
    @api.depends('project_id')
    @api.constrains('start_date', 'project_id')
    def _start_date_contrains(self):
        for project in self:
            print(project.start_date, project.project_id.start_date)
            if project.start_date < project.project_id.start_date:
                raise ValidationError(
                    f'Start date must be greater than project start date: {project.project_id.start_date}'
                )

    # Job due date must lesser project due date
    @api.depends('project_id')
    @api.constrains('due_date', 'project_id')
    def _due_date_contrains(self):
        for project in self:
            print(project.due_date, project.project_id.due_date)
            if project.due_date > project.project_id.due_date:
                raise ValidationError(
                    f'Start date must be lesser than project start date: {project.project_id.due_date}'
                )

    @api.constrains('start_date', 'due_date')
    def _constraint_date(self):
        for project in self:
            if project.start_date > project.due_date:
                raise ValidationError(
                    'Due date must be greater than Start date!')

    # workunit
    @api.onchange('volume', 'rate_per_work_unit')
    @api.depends('volume', 'sale_rate_per_work_unit')
    def _compute_job_value(self):
        for project in self:
            project.job_value = (
                100 -
                0) / 100 * project.volume * project.sale_rate_per_work_unit
