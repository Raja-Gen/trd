/** @odoo-module **/

import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("petty_attachment_preview_tour", {
    url: "/odoo",
    steps: () => [
        {
            content: "Open the Petty Cash app",
            trigger: '.o_app[data-menu-xmlid="dev_petty_cash.menu_petty_cash_root"]',
            run: "click",
        },
        {
            content: "Open the Vouchers menu",
            trigger: '[data-menu-xmlid="dev_petty_cash.menu_petty_cash_vouchers"]',
            run: "click",
        },
        {
            content: "Open All Vouchers",
            trigger: '[data-menu-xmlid="dev_petty_cash.menu_petty_cash_vouchers_all"]',
            run: "click",
        },
        {
            content: "Wait for the voucher list to load",
            trigger: ".o_data_row",
        },
        {
            content: "The Docs column shows the count of 2 attachments",
            trigger: ".o_data_row .o_petty_attachment_trigger .o_petty_attachment_count:contains(2)",
        },
        {
            content: "Hover the trigger -> the popover lists the documents",
            trigger: ".o_data_row .o_petty_attachment_trigger",
            run: "hover",
        },
        {
            content: "Both documents are listed in the popover",
            trigger: ".o_petty_attachment_popover .o_petty_attachment_item:contains(receipt-A.png)",
        },
        {
            content: "Pick the SECOND document specifically",
            trigger: ".o_petty_attachment_popover .o_petty_attachment_item:contains(receipt-B.png)",
            run: "click",
        },
        {
            content: "FileViewer opens showing exactly the document we picked (receipt-B)",
            trigger: ".o-FileViewer .o-FileViewer-header:contains(receipt-B.png)",
        },
        {
            content: "It is an image view",
            trigger: ".o-FileViewer .o-FileViewer-viewImage",
        },
        {
            content: "Close the viewer",
            trigger: ".o-FileViewer-headerButton[aria-label='Close']",
            run: "click",
        },
        {
            content: "Back on the list, viewer gone",
            trigger: ".o_list_view:not(:has(.o-FileViewer))",
        },
        {
            content: "Hover again to reopen the popover",
            trigger: ".o_data_row .o_petty_attachment_trigger",
            run: "hover",
        },
        {
            content: "Now pick the FIRST document",
            trigger: ".o_petty_attachment_popover .o_petty_attachment_item:contains(receipt-A.png)",
            run: "click",
        },
        {
            content: "FileViewer opens showing the first document (receipt-A)",
            trigger: ".o-FileViewer .o-FileViewer-header:contains(receipt-A.png)",
        },
    ],
});
