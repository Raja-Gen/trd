/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillUnmount } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { usePopover } from "@web/core/popover/popover_hook";
import { useFileViewer } from "@web/core/file_viewer/file_viewer_hook";
import { FileModel } from "@web/core/file_viewer/file_model";

/**
 * Popover body: an interactive list of the voucher's attachments. Each row is
 * clickable and opens that specific document in the FileViewer. The popover
 * keeps itself open while the pointer is over it so the user can reach a row.
 */
export class AttachmentPreviewPopover extends Component {
    static template = "dev_petty_cash.AttachmentPreviewPopover";
    static props = {
        attachments: { type: Array },
        onSelect: { type: Function },
        onKeepOpen: { type: Function },
        onScheduleClose: { type: Function },
        close: { type: Function, optional: true },
    };

    isImage(att) {
        return att.mimetype && att.mimetype.startsWith("image/");
    }
    isPdf(att) {
        return att.mimetype === "application/pdf";
    }
    imageUrl(att) {
        return `/web/image/${att.id}/200x200`;
    }
}

/**
 * List/kanban field widget for a many2many of ir.attachment.
 *
 * - The cell shows a paperclip + attachment count.
 * - Hovering opens a popover listing every attachment.
 * - Clicking a row in the popover opens that exact document in Odoo's native
 *   FileViewer (arrows still let you slide to the others). Non-viewable files
 *   (e.g. Office documents) fall back to a download.
 * - Clicking the cell itself opens the single attachment directly, or - when
 *   there are several - opens the list so a specific one can be chosen.
 */
export class PettyAttachmentPreviewField extends Component {
    static template = "dev_petty_cash.PettyAttachmentPreviewField";
    static props = { ...standardFieldProps };

    setup() {
        this.popover = usePopover(AttachmentPreviewPopover, {
            position: "bottom",
            popoverClass: "o_petty_attachment_popover",
        });
        this.fileViewer = useFileViewer();
        this.closeTimer = null;
        onWillUnmount(() => this._clearCloseTimer());
    }

    get attachments() {
        const value = this.props.record.data[this.props.name];
        if (!value || !value.records) {
            return [];
        }
        return value.records.map((rec) => ({
            id: rec.resId,
            name: rec.data.name,
            mimetype: rec.data.mimetype,
        }));
    }

    /** Build FileModel objects the native FileViewer understands. */
    get files() {
        return this.attachments.map((att) => {
            const file = new FileModel();
            file.id = att.id;
            file.name = att.name;
            file.mimetype = att.mimetype;
            file.type = "binary";
            return file;
        });
    }

    get popoverProps() {
        return {
            attachments: this.attachments,
            onSelect: (att) => this.openViewer(att),
            onKeepOpen: () => this._clearCloseTimer(),
            onScheduleClose: () => this._scheduleClose(),
        };
    }

    _clearCloseTimer() {
        if (this.closeTimer) {
            browser.clearTimeout(this.closeTimer);
            this.closeTimer = null;
        }
    }
    _scheduleClose() {
        this._clearCloseTimer();
        this.closeTimer = browser.setTimeout(() => this.popover.close(), 250);
    }

    /** Open a specific attachment, keeping the full set for arrow navigation. */
    openViewer(att) {
        this._clearCloseTimer();
        this.popover.close();
        const files = this.files;
        const target = files.find((f) => f.id === att.id);
        if (target && target.isViewable) {
            this.fileViewer.open(target, files);
        } else {
            window.open(`/web/content/${att.id}?download=true`, "_blank");
        }
    }

    onMouseenter(ev) {
        this._clearCloseTimer();
        if (this.attachments.length && !this.popover.isOpen) {
            this.popover.open(ev.currentTarget, this.popoverProps);
        }
    }
    onMouseleave() {
        this._scheduleClose();
    }

    onClick(ev) {
        const atts = this.attachments;
        if (atts.length === 1) {
            this.openViewer(atts[0]);
        } else if (atts.length > 1) {
            // Show the list so the user can pick a specific document.
            this._clearCloseTimer();
            if (!this.popover.isOpen) {
                this.popover.open(ev.currentTarget, this.popoverProps);
            }
        }
    }
}

export const pettyAttachmentPreviewField = {
    component: PettyAttachmentPreviewField,
    displayName: "Attachment Preview",
    supportedTypes: ["many2many"],
    relatedFields: () => [
        { name: "name", type: "char" },
        { name: "mimetype", type: "char" },
    ],
};

registry.category("fields").add("petty_attachment_preview", pettyAttachmentPreviewField);
