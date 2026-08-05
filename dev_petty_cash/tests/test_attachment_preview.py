# -*- coding: utf-8 -*-
import base64
import io

from PIL import Image

from odoo.tests import HttpCase, tagged


def _png_bytes(color):
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), color).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue())


@tagged("post_install", "-at_install")
class TestPettyAttachmentPreview(HttpCase):
    """Browser tour: the Docs column in the voucher list opens a hover peek
    and, on click, Odoo's native FileViewer gallery."""

    def test_attachment_preview_tour(self):
        admin = self.env.ref("base.user_admin")
        admin.group_ids |= self.env.ref("dev_petty_cash.group_petty_manager")

        company = admin.company_id
        journal = self.env["account.journal"].search(
            [("type", "in", ("cash", "bank")), ("company_id", "=", company.id)],
            limit=1,
        )
        self.assertTrue(journal, "A cash/bank journal is required for the fund")

        fund = self.env["dev.petty.fund"].create({
            "name": "Test Petty Fund",
            "company_id": company.id,
            "currency_id": company.currency_id.id,
            "journal_id": journal.id,
            "float_amount": 1000.0,
            "responsible_user_id": admin.id,
        })

        voucher = self.env["dev.petty.voucher"].create({
            "fund_id": fund.id,
            "company_id": company.id,
            "requester_id": admin.id,
            "purpose": "Attachment preview test",
        })

        att_a = self.env["ir.attachment"].create({
            "name": "receipt-A.png",
            "mimetype": "image/png",
            "datas": _png_bytes((200, 30, 30)),
        })
        att_b = self.env["ir.attachment"].create({
            "name": "receipt-B.png",
            "mimetype": "image/png",
            "datas": _png_bytes((30, 30, 200)),
        })
        voucher.attachment_ids = [(4, att_a.id), (4, att_b.id)]

        self.start_tour(
            "/odoo",
            "petty_attachment_preview_tour",
            login="admin",
        )
