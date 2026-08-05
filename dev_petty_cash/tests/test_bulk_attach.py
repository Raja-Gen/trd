# -*- coding: utf-8 -*-
import base64

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPettyBulkAttach(TransactionCase):
    """The bulk-attach wizard links each row's uploaded document(s) to the
    row's voucher."""

    def _make_voucher(self, company, fund):
        return self.env["dev.petty.voucher"].create({
            "fund_id": fund.id,
            "company_id": company.id,
            "requester_id": self.env.ref("base.user_admin").id,
            "purpose": "Bulk attach test",
        })

    def _make_attachment(self, name):
        return self.env["ir.attachment"].create({
            "name": name,
            "mimetype": "text/plain",
            "datas": base64.b64encode(b"dummy content"),
            "res_model": "petty.bulk.attach.line",
            "res_id": 0,
        })

    def test_bulk_attach(self):
        company = self.env.ref("base.user_admin").company_id
        journal = self.env["account.journal"].search(
            [("type", "in", ("cash", "bank")), ("company_id", "=", company.id)], limit=1)
        fund = self.env["dev.petty.fund"].create({
            "name": "Attach Test Fund",
            "company_id": company.id,
            "currency_id": company.currency_id.id,
            "journal_id": journal.id,
            "float_amount": 500.0,
            "responsible_user_id": self.env.ref("base.user_admin").id,
        })
        v1 = self._make_voucher(company, fund)
        v2 = self._make_voucher(company, fund)

        a1 = self._make_attachment("v1_receipt.pdf")
        a2 = self._make_attachment("v1_photo.png")
        a3 = self._make_attachment("v2_invoice.pdf")

        wizard = self.env["petty.bulk.attach.wizard"].create({
            "line_ids": [
                (0, 0, {"voucher_id": v1.id, "attachment_ids": [(6, 0, [a1.id, a2.id])]}),
                (0, 0, {"voucher_id": v2.id, "attachment_ids": [(6, 0, [a3.id])]}),
            ],
        })
        wizard.action_attach()

        # Each voucher got exactly its own documents.
        self.assertEqual(v1.attachment_ids, a1 | a2)
        self.assertEqual(v2.attachment_ids, a3)
        # Attachments were re-homed onto their voucher.
        self.assertEqual(a1.res_model, "dev.petty.voucher")
        self.assertEqual(a1.res_id, v1.id)
        self.assertEqual(a3.res_id, v2.id)
