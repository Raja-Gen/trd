# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import UserError


class HRContract(models.Model):
    _inherit = "hr.contract"

    termination_type = fields.Selection(
        [
            ("employer", "Employer-Initiated"),
            ("resignation", "Employee-Initiated"),
        ],
        string="Termination Type",
        required=True,
    )
    indemnity_amount = fields.Float(string="Indemnity Amount")
    tenure_years = fields.Float(string="Tenure Years")

    def action_terminate(self):
        """
        Terminates a contract by setting the termination type to 'employer'
        and the end date to today if it is not already terminated.
        """
        for contract in self:
            if not contract.date_end:
                contract.write(
                    {
                        "termination_type": "employer",
                        "date_end": fields.Date.today(),
                    }
                )
            else:
                raise UserError("The contract is already terminated.")

    def action_resign(self):
        """
        Resigns a employee by updating its termination type and end date,
        or raises an error if the employee is already resigned.
        """
        for contract in self:
            print(contract.date_end)
            if not contract.date_end:
                contract.write(
                    {
                        "termination_type": "resignation",
                        "date_end": fields.Date.today(),
                    }
                )
            else:
                raise UserError("The contract is already resigned.")

    def action_release_indemnity(self):
        """
        Returns an action for opening a wizard with default values set in the context.

        :return: An action object is being returned with a context dictionary containing default values
        for contract_id, termination_type, and currency_id.
        """
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "hr_indemnity.action_hr_indemnity_wizard"
        )
        action["context"] = {
            "default_serive_start_date": self.date_start,
            "default_serive_end_date": self.date_end,
            "default_contract_id": self.id,
            "default_termination_type": self.termination_type,
            "default_currency_id": self.currency_id,
        }
        return action
