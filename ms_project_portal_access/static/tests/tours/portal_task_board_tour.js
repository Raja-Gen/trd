import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("ms_portal_task_board", {
    steps: () => [
        {
            content: "The project sharing board opens for a user given one task",
            trigger: ".o_project_sharing .o_kanban_renderer",
        },
        {
            content: "The task given to this user is on the board",
            trigger: ".o_kanban_record:contains(MS Granted Task)",
        },
        {
            content: "A task of the same project given to someone else is not",
            trigger: "body:not(:has(.o_kanban_record:contains(MS Hidden Task)))",
        },
        {
            content: "Open the task",
            trigger: ".o_kanban_record:contains(MS Granted Task)",
            run: "click",
        },
        {
            content: "Rename it",
            trigger: ".o_form_view .o_field_widget[name=name] input, .o_form_view .o_field_widget[name=name] textarea",
            run: "edit MS Renamed Task",
        },
        {
            content: "Change the stage",
            trigger: ".o_statusbar_status button:contains(MS Done Stage)",
            run: "click",
        },
        {
            content: "The stage moved",
            trigger: ".o_statusbar_status button.o_arrow_button_current:contains(MS Done Stage)",
        },
        {
            content: "Back to the board",
            trigger: ".o_back_button, .breadcrumb-item a",
            run: "click",
        },
        {
            content: "The renamed task sits in its new column",
            trigger: ".o_kanban_group:contains(MS Done Stage) .o_kanban_record:contains(MS Renamed Task)",
        },
    ],
});
