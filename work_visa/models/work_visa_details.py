from odoo import fields, models, api, _
from datetime import date, timedelta

class WorkVisaDetails(models.Model):
    _name = "work.visa.details"
    _description = "Work Visa Details"
    _rec_name = "wvd_visa_fee"
    
    # Work Visa Details
    wvd_file_no = fields.Char("File No.")
    wvd_visa_fee = fields.Float("Visa fee")
    wvd_visa_fee_payment_date = fields.Date("Visa fee payment date")
    wvd_visa_no = fields.Char("Visa No.")
    wvd_moi_ref_no = fields.Char("Moi Ref. No.")
    wvd_visa_issue_date = fields.Date("Visa Issue Date")
    wvd_visa_expiry_date = fields.Date("Visa Expiry Date")
    wvd_visa_status = fields.Char("Visa Status")
    wvd_visa_cancellation_date = fields.Date("Visa Cancellation Date")
    wvd_reason_of_visa_cancellation = fields.Char("Reason of Visa Cancellation")
    wvd_expected_date_of_arrival = fields.Char("Expected Date of Arrival")
    wvd_date_of_arrival_ticket = fields.Date("Date of Arrival Ticket")