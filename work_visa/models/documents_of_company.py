from odoo import fields, models, api, _
from datetime import date, timedelta

class DocumentsOfCompany(models.Model):
    _name = "documents.of.company"
    _description = "Documents Of Company"
    _rec_name = "dc_company_name"
    
    # Documents of Company fields
    dc_company_name = fields.Char("Company Name")
    dc_document_no = fields.Char("Document No")
    dc_document_name = fields.Char("Document Name")
    dc_document_issue_date = fields.Date("Document Issue Date")
    dc_document_expiry_date = fields.Date("Document Expiry Date")
    dc_issuing_authority = fields.Char("Issuing Authority")
    dc_site_of_issuing_authority = fields.Char("Site of Issuing Authority")
    dc_expiry_reminder_day = fields.Char("Expiry Reminder Day")
    dc_issuing_fee = fields.Float("Issuing Fee")

    # Data added to the car only
    # Additional information 1 
    dac_document_no= fields.Char("Document No. associated with Original")
    dac_issuing_authority= fields.Char("Issuing Authority (associated with Original)")
    dac_issue_date = fields.Date("Issue Date")
    dac_expiry_date = fields.Date("Expiry Date")   
    dac_expiry_reminder_day = fields.Char("Expiry Reminder Day")
    
    # Additional information 2
    daca_document_no= fields.Char("Document No. associated with Original")
    daca_issuing_authority= fields.Char("Issuing Authority (associated with Original)")
    daca_issue_date = fields.Date("Issue Date")
    daca_expiry_date = fields.Date("Expiry Date")   
    daca_expiry_reminder_day = fields.Char("Expiry Reminder Day")
