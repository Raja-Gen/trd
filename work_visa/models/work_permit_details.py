from odoo import fields, models, api, _
from datetime import date, timedelta

class WorkPermitDetails(models.Model):
    _name = "work.permit.details"
    _description = "Work Permit Details"
    _rec_name = "wpd_company_name"
    
    # Work Permit Details
    wpd_company_name = fields.Char("Company Name")
    wpd_occupation = fields.Char("Occupation")
    wpd_salary = fields.Float("Salary")
    wpd_apply_entry_permit = fields.Char("Apply Entry Permit")
    wpd_requesting_no = fields.Char("Requesting No.")
    wpd_requesting_status = fields.Char("Requesting Status")
    wpd_date_of_issue_permit = fields.Date("Date of Issue Permit")
    wpd_reason_of_rejection = fields.Char("Reason of Rejection")
    wpd_date_of_cancellation_permit = fields.Date("Date of Cancellation  Permit")
    wpd_file_no = fields.Char("File No.")