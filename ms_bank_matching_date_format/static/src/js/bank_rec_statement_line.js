/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { formatDate } from "@web/core/l10n/dates";
import { BankRecStatementLine } from "@account_accountant/components/bank_reconciliation/statement_line/statement_line";

// Core prints the transaction date as "Apr 14" (month short + 2-digit day), which
// drops the year. formatDate() uses localization.dateFormat, i.e. the date format
// of the user's language (%d/%m/%Y -> 14/04/2026).
patch(BankRecStatementLine.prototype, {
    get formattedDate() {
        return formatDate(this.recordData.date);
    },
});
