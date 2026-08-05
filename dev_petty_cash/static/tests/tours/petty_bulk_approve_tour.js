/** @odoo-module **/

import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("petty_bulk_approve_tour", {
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
            content: "Wait for the list",
            trigger: ".o_list_view .o_data_row",
        },
        {
            content: "Select all rows",
            trigger: ".o_list_view thead .o_list_record_selector input[type=checkbox]",
            run: "click",
        },
        {
            content: "The bulk Approve button appears once rows are selected",
            trigger: "button[name=action_approve_selected]",
            run: "click",
        },
        {
            content: "Confirm the approval dialog",
            trigger: ".modal-dialog .modal-footer button.btn-primary",
            run: "click",
        },
        {
            content: "After approval the list shows an Approved status badge",
            trigger: ".o_data_row .o_field_badge:contains(Approved)",
        },
    ],
});
