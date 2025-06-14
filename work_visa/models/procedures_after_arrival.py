from odoo import fields, models, api, _
from datetime import date, timedelta

class ProceduresAfterArrival(models.Model):
    _name = "procedures.after.arrival"
    _description = "Procedures After Arrival"
    _rec_name = "paa_civil_no"
    
    # Procedures After Arrival
    paa_file_no = fields.Char("File No.")
    paa_date_of_entry = fields.Date("Date of Entry")
    paa_grace_period_expiry_date = fields.Date("Grace Period Expiry Date")
    paa_temporary_residence = fields.Char("Temporary residence")
    paa_civil_no = fields.Char("Civil No.")
    paa_fingerprint = fields.Char("Fingerprint")
    paa_medical_examination = fields.Char("Medical Examination")
    paa_medical_examination_rsult = fields.Char("Medical Examination Rsult")
    paa_pcc_authentication = fields.Char("PCC Authentication")
    paa_pcc_translation = fields.Char("PCC Translation")
    paa_license_authentication = fields.Char("License Authentication")
    paa_work_permit_issue_date = fields.Date("Work Permit Issue Date")
    paa_health_insurance = fields.Char("Health Insurance")
    paa_residency_issue_date = fields.Date("Residency Issue Date")
    paa_submit_civil_id = fields.Char("Submit Civil ID")
    paa_civil_issuance_status = fields.Char("Civil Issuance Status")
    paa_traffic_form = fields.Char("Traffic Form")
    paa_trail_date = fields.Date("Trail Date")
    paa_trail_result = fields.Char("Trail Result")
    paa_meta_account = fields.Char("Meta Account")
    paa_health_card = fields.Char("Health Card")
    paa_comments = fields.Char("Comments")
    paa_civil_id_expiry_date = fields.Date("Civil ID Expiry Date")