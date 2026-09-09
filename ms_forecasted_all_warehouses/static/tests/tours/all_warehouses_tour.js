import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("ms_forecasted_all_warehouses_tour", {
    steps: () => [
        {
            content: "open the test product",
            trigger: ".o_kanban_record:contains(MS Tour Forecast Product)",
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
            content: "the report opens on a single warehouse",
            trigger: ".o_stock_forecast .o_search_options button:contains(Warehouse:)",
            run: "click",
        },
        {
            content: "the new All Warehouses entry is offered",
            trigger: ".dropdown-item:contains(All Warehouses)",
            run: "click",
        },
        {
            content: "the filter button now reads All Warehouses",
            trigger: ".o_search_options button:contains(All Warehouses)",
        },
        {
            content: "On Hand is the sum of both warehouses: 4 + 7 = 11",
            trigger: ".o_stock_forecast div[name=on_hand] .h3:contains(11)",
        },
        {
            content: "switch back to a single warehouse",
            trigger: ".o_search_options button:contains(All Warehouses)",
            run: "click",
        },
        {
            trigger: ".dropdown-item:contains(MS Tour WH Two)",
            run: "click",
        },
        {
            content: "the standard per-warehouse report is back: 7 units",
            trigger: ".o_stock_forecast div[name=on_hand] .h3:contains(7)",
        },
        {
            content: "and the button names that warehouse again",
            trigger: ".o_search_options button:contains(MS Tour WH Two)",
        },
    ],
});
