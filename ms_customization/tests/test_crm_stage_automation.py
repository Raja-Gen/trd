# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCrmStageAutomation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Customer"})
        cls.team = cls.env["crm.team"].create({"name": "Test Sales Team"})

        cls.stage_new = cls.env["crm.stage"].create({
            "name": "New",
            "sequence": 1,
            "team_ids": [(6, 0, [cls.team.id])],
            "is_won": False,
            "is_quotation_stage": False,
        })
        cls.stage_quotation = cls.env["crm.stage"].create({
            "name": "Quotation",
            "sequence": 2,
            "team_ids": [(6, 0, [cls.team.id])],
            "is_won": False,
            "is_quotation_stage": True,
        })
        cls.stage_won = cls.env["crm.stage"].create({
            "name": "Won",
            "sequence": 3,
            "team_ids": [(6, 0, [cls.team.id])],
            "is_won": True,
            "is_quotation_stage": False,
        })

        cls.lead = cls.env["crm.lead"].create({
            "name": "Test Opportunity",
            "type": "opportunity",
            "team_id": cls.team.id,
            "stage_id": cls.stage_new.id,
            "partner_id": cls.partner.id,
        })

    def test_create_quotation_moves_lead_to_quotation_stage(self):
        """Creating a quotation for an opportunity moves it to the Quotation stage."""
        self.assertEqual(self.lead.stage_id, self.stage_new)
        self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "opportunity_id": self.lead.id,
        })
        self.assertEqual(self.lead.stage_id, self.stage_quotation)

    def test_link_quotation_moves_lead_to_quotation_stage(self):
        """Linking an existing draft quotation to an opportunity moves it to Quotation stage."""
        so = self.env["sale.order"].create({
            "partner_id": self.partner.id,
        })
        self.assertEqual(self.lead.stage_id, self.stage_new)
        so.write({"opportunity_id": self.lead.id})
        self.assertEqual(self.lead.stage_id, self.stage_quotation)

    def test_confirm_quotation_moves_lead_to_won_stage(self):
        """Confirming a quotation moves the linked opportunity to the Won stage."""
        so = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "opportunity_id": self.lead.id,
        })
        self.assertEqual(self.lead.stage_id, self.stage_quotation)
        so.action_confirm()
        self.assertEqual(self.lead.stage_id, self.stage_won)

    def test_won_lead_not_reverted_by_new_quotation(self):
        """An opportunity already in Won stage does not get pulled back by a new quotation."""
        self.lead.write({"stage_id": self.stage_won.id})
        self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "opportunity_id": self.lead.id,
        })
        self.assertEqual(self.lead.stage_id, self.stage_won)
