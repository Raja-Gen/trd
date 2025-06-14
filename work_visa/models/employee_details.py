from odoo import fields, models, api, _
from datetime import date, timedelta

class EmployeeDetails(models.Model):
    _name = "employee.details"
    _description = "Employee Details"
    _rec_name = "ed_file_no"
    
    # Employee Details fields
    ed_file_no = fields.Char("File No.")
    ed_arabic_name = fields.Char("Arabic Name")
    ed_english_name = fields.Char("English Name")
    ed_passport_no = fields.Char("Passport No.")
    ed_passport_issue_date = fields.Date("Passport Issue Date")
    ed_passport_expiry_date = fields.Date("Passport Expiry Date")
    ed_national_id_no = fields.Char("National ID No.")
    ed_nationality = fields.Char("Nationality")
    ed_date_of_birth = fields.Date("Date of Birth")
    ed_gender = fields.Selection([('male', 'Male'),
                              ('female', 'Female'),
                              ('other', 'Other'),], defualt="male")
    ed_national_license_type = fields.Char("National License Type")
    ed_national_license_issue = fields.Date("National License Issue")
    ed_national_license_expiry = fields.Date("National License Expiry")
    ed_eduction = fields.Char("Eduction")
    ed_contact_no = fields.Char("Contact No.")
    ed_email = fields.Char("E-Mail Address")
    ed_supplier_name = fields.Char("Supplier Name")
    ed_supplier_mobile_no = fields.Char("Supplier Mobile No.")
    ed_aproval_date = fields.Date("Aproval Date")
    
    

