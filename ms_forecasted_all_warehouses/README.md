# Forecasted Report: All Warehouses

Adds an **All Warehouses** entry to the warehouse dropdown on the Forecasted
Report, which reports the combined figures for every warehouse the user can
currently see instead of one at a time.

---

## What the user sees

The dropdown that read

    Warehouse: Saif Zone

gains one entry at the top:

    All Warehouses          <- new
    Saif Zone
    Sajja Warehouse
    KARO INTERNATIONAL GENERAL TRADING SOLE PROPRIETORSHIP L.L.C
    AMAZON SAUDI VENDOR
    Noon FBN

Picking it reloads the report with On Hand, Incoming, Outgoing, Forecasted, the
forecast graph and the detail lines covering all of them. Picking a named
warehouse again returns to the standard single-warehouse report.

The entry only appears when there is more than one warehouse to combine, because
Odoo hides the whole filter otherwise.

## How it works

`_get_report_data` runs the **standard report once per warehouse** and folds the
results together. It does not reimplement Odoo's forecasting; each pass is the
ordinary report with `warehouse_id` set, so everything other modules contribute -
`sale_stock`'s draft sale orders, `purchase_stock`'s draft purchase orders,
`stock_account`'s valuation, `product_expiry`'s expiry lines, `mrp` - is
included exactly as it is normally. None of those modules override
`_get_report_data` itself, which is what makes this safe.

Merging rules: quantities are summed (so a quantity added by a module this one
has never heard of is still summed), booleans are OR-ed, document lists are
concatenated and de-duplicated by id, the lead time keeps the **soonest**
arrival, and the unit of measure is kept as-is. Report lines are concatenated
and then re-sorted per product, because the details table starts a new product
heading whenever the product changes from one row to the next.

**Value On Hand** is recomputed rather than summed, because the per-warehouse
figures are already formatted strings. It is presented exactly as Odoo presents
it - a single figure in the user's company currency. Where a warehouse belongs to
a company on another currency, its amount goes through Odoo's own currency
converter before being added, rather than being added as though it were the same
money.

## Multi-company

This matters here - the database has 15 companies and 17 warehouses.

**The aggregate covers exactly the companies ticked in the company switcher**,
which is the same set the dropdown itself lists. Switch companies and the
aggregate follows.

Two deliberate choices:

- The server decides the scope itself, from `self.env.companies`. It does **not**
  accept a list of warehouses from the browser, so a crafted request cannot widen
  the figures it gets back.
- The scope is filtered **explicitly** on `company_id`, not left to record rules.
  Rules would normally narrow a bare `search([])` the same way, but they are
  bypassed for the superuser - so a cron, an `odoo-bin shell` session or a
  `sudo()` call would otherwise silently total up all fifteen companies.

## What it does not change

The report still opens on a single warehouse and behaves exactly as before until
the new entry is picked; the context flag is absent in that case and
`_get_report_data` hands straight back to Odoo. Nothing else about stock,
forecasting or replenishment is touched.

One consequence worth knowing: a transfer **between** two of the warehouses is an
outgoing move for the source and an incoming move for the destination, so it
appears in both the Incoming and the Outgoing totals. On Hand and Forecasted are
unaffected, since the two cancel out.

The **Replenish** button still replenishes into the single warehouse that was
last selected - it has to pick one, and inventing a choice there would be worse
than keeping the last one.

## Tests

    python3 odoo-bin -c <conf> -d <db> -u ms_forecasted_all_warehouses \
        --test-enable --test-tags /ms_forecasted_all_warehouses --stop-after-init

Fourteen tests. The aggregation, the multi-company scoping and the merge rules
are covered by `TransactionCase`s; the dropdown entry itself is OWL, which no
server-side check can prove works, so `test_all_warehouses_tour.py` drives a real
browser through opening the report, picking **All Warehouses**, checking the
total is the sum of two warehouses, and switching back to a single one.
