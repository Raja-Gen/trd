import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("ms_forecast_links_tour", {
    steps: () => [
        {
            content: "open the test product",
            trigger: ".o_kanban_record:contains(MS Links Tour Product)",
            run: "click",
        },
        {
            content: "the Forecasted button can sit behind More",
            trigger: ".o_form_view",
            run: () => {
                if (!document.querySelector("button[name=action_product_tmpl_forecast_report]")) {
                    const buttons = document.querySelectorAll(".o_control_panel_actions button");
                    const more = Array.from(buttons).find((b) => b.textContent.trim() === "More");
                    more?.click();
                }
            },
        },
        {
            content: "open the Forecasted report",
            trigger: "button[name=action_product_tmpl_forecast_report]",
            run: "click",
        },
        {
            content: "On Hand is clickable already - Odoo's own behaviour",
            trigger: ".o_stock_forecast div[name=on_hand] a",
        },
        {
            content: "Incoming is now a link too, showing the 9 units",
            trigger: ".o_stock_forecast a[name=ms_incoming_link]:contains(9)",
        },
        {
            content: "Outgoing is a link as well, showing the 4 units",
            trigger: ".o_stock_forecast a[name=ms_outgoing_link]:contains(4)",
        },
        {
            content: "click Incoming",
            trigger: ".o_stock_forecast a[name=ms_incoming_link]",
            run: "click",
        },
        {
            content: "it opens the moves behind that figure",
            trigger: ".o_list_view",
        },
        {
            content: "and the breadcrumb names it Incoming",
            trigger: ".o_breadcrumb:contains(Incoming)",
        },
        {
            content: "the list holds the incoming move, not the outgoing one",
            trigger: ".o_list_view .o_data_row",
            run: () => {
                const rows = document.querySelectorAll(".o_list_view .o_data_row");
                if (rows.length !== 2) {
                    throw new Error(`expected the 2 incoming moves, found ${rows.length}`);
                }
            },
        },
    ],
});
