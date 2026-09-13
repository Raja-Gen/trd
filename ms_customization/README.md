# MS Customization

In-house customizations for MicroSolutions / Raja. Several independent
features shipped in one module.

---

## 1. Purchase Read Only

### A "Read Only" level on the Purchase privilege

`ms_customization.group_purchase_readonly` sits in the standard **Purchase**
privilege alongside *User* and *Administrator*, at a lower sequence, so in
Settings > Users the Purchase dropdown reads:

    Purchase:  ( ) Read Only   ( ) User   ( ) Administrator

Picking *User* or *Administrator* replaces *Read Only* rather than stacking with
it, so the read-only level cannot be silently widened by also ticking User.

The group carries `perm_read` only — no write, create or unlink — on 22 models:

| Area       | Models |
|------------|--------|
| Purchase   | `purchase.order`, `purchase.order.line`, `purchase.report`, `purchase.bill.union`, `vendor.delay.report` |
| Products   | `product.product`, `product.template`, `product.supplierinfo` |
| Partners   | `res.partner` |
| Accounting | `account.tax`, `account.account.tag`, `account.fiscal.position`, `account.journal`, `account.account`, `account.move`, `account.move.line`, `account.analytic.line` |
| Inventory  | `stock.location`, `stock.warehouse`, `stock.picking`, `stock.move`, `stock.warehouse.orderpoint` |

Two record rules mirror `purchase.purchase_user_account_move_rule` so the Bills
smart button only ever exposes vendor bills (`in_invoice`, `in_refund`,
`in_receipt`) — never customer invoices or journal entries.

The Purchase root menu and the Reporting menus are opened to the group.
**Configuration stays restricted to Purchase Administrator.**

Odoo 19 forbids `group_ids` on an inherited view record, so the read-only UI is
expressed with `groups` attributes inside the arch instead: every workflow button
in the purchase order header (Send RFQ, Send PO, Confirm, Acknowledge, Set to
Draft, Cancel, Lock, and the file uploader widget) is reserved to
`purchase.group_purchase_user`. The read-only group does not imply that group, so
a read-only user sees only the status bar and the Print buttons — nothing that
would raise an `AccessError` on click. Approve and Unlock already carry
`group_purchase_manager`, and Print already carries `base.group_user`.

Create / Edit / Delete / Duplicate need no override: the web client drops those
affordances by itself once the ACLs deny write and create.

### Assigning a user

Settings > Users & Companies > Users > *the user* > **Access Rights** tab, set
the **Purchase** privilege to **Read Only**, then save.

This governs the Purchase app only. A user who also holds Inventory
Administrator or Sales Administrator keeps full write access in those apps —
check the rest of the Access Rights tab if read-only is meant to be broader.

---

## 2. CRM Quotation & Won Stage Automation

1. A quotation created for an opportunity moves that opportunity to the
   **Quotation** stage of its own sales team.
2. Confirming that quotation into a sales order moves the opportunity to the
   **Won** stage of its own sales team.

### Why a flag rather than the stage name

This database runs two pipelines whose stages share names but not sequences:

| Team       | Quotation stage | Won stage     |
|------------|-----------------|---------------|
| Sales MSK  | seq 1 (id 2)    | seq 5 (id 4)  |
| Sales RIGT | seq 5 (id 19)   | seq 7 (id 21) |

Matching on the name `Quotation` at runtime would be ambiguous, so the module
adds an **Is Quotation Stage?** boolean to `crm.stage`, next to Odoo's own
**Is Won Stage?**, and resolves the target through `crm.lead._stage_find()` —
which scopes to the lead's team and falls back to stages shared with all teams.

The `post_init_hook` ticks the flag on every stage named `Quotation` that is not
a won stage, so the automation is live the moment it is installed. On this
database that is exactly stages **2 (Sales MSK)** and **19 (Sales RIGT)**. If no
such stage exists the hook logs a warning and does nothing.

The Won side calls Odoo's own `action_set_won()`, which already resolves the
correct won stage per team and sets probability to 100%.

### Behaviour

**Triggers**
- `sale.order.create()` with an `opportunity_id`, while the order is a quotation
  (`draft` / `sent`)
- `sale.order.write()` that sets `opportunity_id`, i.e. linking an existing
  quotation to an opportunity after the fact
- `sale.order.action_confirm()` → won

**Deliberately does nothing when**
- the record is a lead (`type = 'lead'`), not an opportunity
- the quotation has no `opportunity_id` — quotations raised directly in Sales
  never touch the pipeline
- the opportunity is **already at or past** the Quotation stage. Movement is
  forward-only, so raising a further quotation while in Negotiation or Won does
  not drag the pipeline backwards.
- the opportunity is already in a won stage

**Worth knowing:** an opportunity with several quotations reaches Won as soon as
*any one* of them is confirmed. That follows the rule as specified; if Won should
instead wait until every quotation is resolved, that needs a different rule.

Stage changes are written with `sudo()`. Moving the pipeline is a side effect of
the sales flow, and must not fail because the person raising or confirming the
quotation is not the salesperson who owns the opportunity. The change is still
tracked in the opportunity's chatter under the acting user, since `stage_id` is a
tracked field.

After install, verify under **CRM > Configuration > Stages** that exactly one
stage per team carries **Is Quotation Stage?**.

---

## 3. CRM: Own Leads Only

Restricts chosen users to the CRM leads and opportunities they are the
salesperson of. Unassigned leads are hidden too. **Sales Orders, Invoices and
the rest of the Sales app are deliberately left untouched.**

### Why this could not be done with Odoo's built-in groups

Odoo ships a "User: Own Documents Only" level, but it does not fit here:

1. Its rule is `['|',('user_id','=',user.id),('user_id','=',False)]` — it
   **deliberately shows unassigned leads** so salespeople can pick work up. In
   this database 2,258 of 2,728 leads (83%) have no salesperson, so that level
   would have restricted almost nothing.
2. The Sales privilege is a single ladder. Dropping a user to that level also
   scopes their Sales Orders, customer Invoices, sales reporting and commissions
   to their own records — far beyond "their own leads in CRM".

### How it works

Record rules attached to groups are **OR-ed**, so a stricter rule added to a
group can never narrow what another group already grants. These users are Sales
Administrators, which carries `sales_team`'s *All Leads* rule with domain
`[(1,'=',1)]` — any rule added beside it would simply be OR-ed away.

Global rules are **AND-ed** with the OR-ed group rules, so a global rule can
narrow. To keep it inert for everyone else, the domain is evaluated per user:

    [('user_id', '=', user.id)] if user.has_group('ms_customization.group_crm_own_leads_only') else [(1, '=', 1)]

`ir.rule._compute_domain` is cached on `env.uid`, so the per-user result caches
correctly. The same rule is applied to `crm.activity.report`, which is a
reporting view over the same leads and would otherwise expose every row.

`perm_create` is left off the rule so these users can still log a new lead;
note that a lead they create **without** a salesperson will immediately drop out
of their own view.

### Assigning a user

Settings > Users & Companies > Users > *the user* > **Access Rights** tab, tick
**CRM: Own Leads Only**, then save. Leave their Sales privilege as it is — the
restriction works alongside Sales Administrator.

Intended for `ebdm@rajacompany.com` (user 27) and `sc2@rajacompany.com`
(user 29). Assignment is done in the UI, not hardcoded in this module.


---

## 4. Inventory Items on CRM Leads

Adds an **Inventory Items** tab to the lead/opportunity form, so stock can be
judged while qualifying the deal.

    Product         Qty   UoM     On Hand  Forecast  Free   Availability
    Safety Helmet    50   Units      12       42      12    Partial
    Gloves L        200   Units     350      350     180    In Stock
    Hi-Vis Vest      25   Units       0       60       0    Out of Stock

New model `crm.lead.product.line`, one row per item, holding the product, the
quantity required and its UoM. **On Hand**, **Forecasted**, **Free To Use** and
**Availability** are computed, never stored, so they always read live stock.

Only storable products are selectable — consumables and services carry no stock.

### Which stock is shown

By default the figures cover **every warehouse of the lead's company**. An
optional **Warehouse** field on the tab narrows them to one warehouse, which
matters for companies running several: RAJA INTERNATIONAL GENERAL TRADING (LLC)
has Sajja, AMAZON SAUDI VENDOR and Noon FBN.

Scoping is done with context (`allowed_company_ids`, and `warehouse_id` when
set) rather than by summing quants by hand, so it follows Odoo's own definition
of on-hand and forecast. Lines are batched per (company, warehouse) so a lead
with many items still reads stock in one pass per scope.

Quantities are read with `sudo()`, because computing them walks `stock.quant`,
which a salesperson need not have access to. The scope is fixed by the context,
so this cannot widen which company's stock is shown.

**Availability** compares *Free To Use* against the quantity required,
converting the line's UoM to the product's own UoM first: `In Stock` when free
stock covers it, `Partial` when some is free but not enough, `Out of Stock` when
none is free.

### Carrying into the quotation

When a quotation is raised against the opportunity, its items pre-fill the
quotation lines — product, quantity and UoM, priced by the normal pricelist
logic. This happens on the `opportunity_id` onchange, so lines appear in the
form immediately, and again in `create()` for quotations built in code where no
onchange runs.

**A quotation that already has lines is never overwritten.** Only an empty
quotation is filled, so anything keyed in by hand survives.

### Access

`crm.lead.product.line` is readable and writable by Sales users and
Administrators. The items also follow the **CRM: Own Leads Only** restriction
from section 3 — without that, a restricted user could read the items of a
colleague's lead directly, bypassing the restriction on the lead itself.


---

## 5. Customer Type (Trader / End User)

A **Customer Type** option on the contact, so a customer can be recorded as a
**Trader** (buys to resell) or an **End User** (buys for their own use).

`res.partner.ms_customer_type` is a selection of `trader` / `end_user`. It is
optional: every contact that predates the module, and every one nobody has
classified, reads blank rather than being forced into one of the two.

### Where it appears

| Where | View | Notes |
|---|---|---|
| Contact form | `base.view_partner_form` | Under **Tags**, in the same column as VAT and Website — visible while the customer is being created, not behind a tab. |
| Quick-create form | `base.view_partner_simple_form` | The dialog that opens from *Create and edit…* on a customer field, e.g. from a quotation. Without it the type could only ever be set after the fact. |
| Contact list | `base.view_partner_tree` | Optional column, hidden by default — switch it on from the column picker. |
| Contact search | `base.view_res_partner_filter` | Filters **Traders**, **End Users** and **Customer Type Not Set**, plus a **Customer Type** Group By. |

The field is on `res.partner`, which every customer, vendor and child contact
shares, so it is offered on vendors and contacts as well. It is left blank there
and nothing reads it, so this is cosmetic rather than a constraint — it is the
same trade-off Odoo makes with VAT and Tags.

Changes are **tracked**: setting or changing the type posts to the contact's
chatter, so a reclassification can be traced back to who made it.

### Not done, deliberately

- Nothing keys off the type yet — it does not drive pricelists, taxes or
  reports. It is a classification to file and filter on. Say the word if a
  pricelist or a report should read it.
- Child contacts do not inherit the type from their parent company. Each record
  carries its own value; the type is not in `_commercial_fields()`.

---

## Install

The module lives in an addons path already configured in `odoo19.conf`.

    Apps > Update Apps List > search "MS Customization" > Activate

or from the command line:

    python3 odoo-bin -c odoo19.conf -d <database> -i ms_customization --stop-after-init

Note the features ship together: the manifest depends on both the purchase /
stock chain and on crm / sale_crm, and they install and uninstall as one unit.
