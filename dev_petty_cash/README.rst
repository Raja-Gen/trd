==========================
Dev Petty Cash Management
==========================

Enterprise-grade petty cash fund management module for Odoo 17.

|badge1| |badge2| |badge3|

.. |badge1| image:: https://img.shields.io/badge/maturity-Production-green.png
    :target: https://odoo-community.org/page/development-status
    :alt: Production
.. |badge2| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: https://www.gnu.org/licenses/lgpl-3.0.html
    :alt: License: LGPL-3
.. |badge3| image:: https://img.shields.io/badge/Odoo-17.0-purple.png
    :target: https://www.odoo.com
    :alt: Odoo 17.0

**Table of contents**

.. contents::
   :local:

Overview
========

This module provides comprehensive petty cash fund management capabilities for
organizations that need to track small cash expenses. It includes full accounting
integration, approval workflows, and automated replenishment triggers.

Features
========

Fund Management
---------------
* Create and manage multiple petty cash funds
* Assign responsible users (custodians) to each fund
* Set fund float amounts and replenishment thresholds
* Real-time balance tracking with computed available balance
* Block/unblock funds for administrative control

Voucher Workflow
----------------
* Request → Approve → Pay → Reconcile workflow
* Multi-line vouchers with expense categorization
* Attachment support for receipts and documents
* Full audit trail via chatter/mail integration
* PDF report generation for vouchers

Accounting Integration
----------------------
* Automatic journal entry creation on payment
* Proper debit/credit entries for expense accounts
* Replenishment journal entries from bank to petty cash
* Variance handling for cash shortages/overages
* Multi-currency support

Security
--------
* Three-tier security groups: User, Cashier, Manager
* Record-level security rules
* Multi-company isolation
* Company-specific access controls

Automation
----------
* Automatic replenishment request when balance falls below threshold
* Email notifications for approvals and payments
* Scheduled cron job for threshold monitoring

Accounting Dashboard
--------------------
* Real-time KPI cards showing fund totals, pending approvals, and risks
* Fund monitoring table with status indicators (OK/Warning/Critical)
* Drill-down actions to related vouchers and funds
* Automated alerts for unreconciled vouchers and critical funds
* Weekly dashboard summary email (optional)

Installation
============

1. Copy the ``dev_petty_cash`` folder to your Odoo addons directory
2. Update the addons list: Apps → Update Apps List
3. Install the module: Apps → search for "Dev Petty Cash Management" → Install

Dependencies
------------
* ``account`` - Core accounting
* ``account_accountant`` - Accounting features
* ``mail`` - Messaging/chatter
* ``hr`` - Human Resources (for employee linking)

Optional: ``analytic`` for analytic accounting support

Configuration
=============

Step 1: Create Petty Cash GL Account
------------------------------------

1. Go to **Accounting → Configuration → Chart of Accounts**
2. Create a new account:
   - **Name**: Petty Cash
   - **Code**: e.g., 101001 (based on your chart of accounts)
   - **Type**: Current Assets / Cash
   - **Allow Reconciliation**: Yes

Step 2: Create Petty Cash Journal
---------------------------------

1. Go to **Accounting → Configuration → Journals**
2. Click **Create**:
   - **Journal Name**: Petty Cash
   - **Type**: Cash
   - **Short Code**: e.g., PC
   - **Default Account**: Select the Petty Cash account created above

Step 3: Configure Replenishment Source
--------------------------------------

If you want automatic replenishment tracking:

1. Identify your bank journal and account for funding petty cash
2. Create a variance account for cash shortages/overages:
   - **Name**: Cash Over/Short
   - **Type**: Expense

Step 4: Create a Petty Cash Fund
--------------------------------

1. Go to **Accounting → Petty Cash → Funds**
2. Click **Create**:
   - **Fund Name**: e.g., "Main Office Petty Cash"
   - **Petty Cash Journal**: Select the journal created above
   - **Float Amount**: e.g., 1000.00 (maximum amount for this fund)
   - **Responsible Person**: Select the fund custodian
   - **Replenishment Threshold**: e.g., 200.00 (trigger for replenishment)
   - **Replenishment Journal**: Select bank journal
   - **Replenishment Account**: Select bank account
   - **Variance Account**: Select cash over/short account

Step 5: Assign User Groups
--------------------------

1. Go to **Settings → Users & Companies → Users**
2. Edit user profiles and assign appropriate groups:
   - **Petty Cash / User**: Can submit voucher requests
   - **Petty Cash / Cashier**: Can approve and pay vouchers for assigned funds
   - **Petty Cash / Manager**: Full access to all features

Usage
=====

Creating a Voucher Request
--------------------------

1. Go to **Accounting → Petty Cash → Vouchers → My Vouchers**
2. Click **Create**
3. Select the **Fund** and enter the **Purpose**
4. Add line items with:
   - Description
   - Quantity and Unit Price
   - Expense Account
5. Attach receipts if available
6. Click **Submit for Approval**

Approving and Paying Vouchers
-----------------------------

Cashiers/Managers:

1. Go to **Accounting → Petty Cash → Vouchers → To Approve**
2. Review the voucher details and attachments
3. Click **Approve** if valid
4. After approval, click **Mark as Paid** to create the journal entry
5. The physical cash should be disbursed to the requester

Reconciling Vouchers
--------------------

After the requester returns with receipts:

1. Go to **Accounting → Petty Cash → Vouchers → To Reconcile**
2. Open the paid voucher
3. Click **Reconcile**
4. Enter the **Receipt Total** from actual receipts
5. Attach all receipts
6. If there's a variance, the system will create an adjustment entry
7. Click **Reconcile** to complete

Requesting Replenishment
------------------------

When fund balance is low:

1. Go to **Accounting → Petty Cash → Funds**
2. Select the fund
3. Click **Request Replenishment**
4. Enter the amount to replenish
5. Submit for approval

The system also automatically creates replenishment requests when the balance
falls below the configured threshold.

Sample Workflows
================

Basic Expense Workflow
----------------------

.. code-block:: text

    1. Employee creates voucher request for $50 office supplies
    2. Cashier approves the voucher
    3. Cashier pays the voucher (creates journal entry):
       Dr. Office Supplies Expense    $50
       Cr. Petty Cash                 $50
    4. Employee purchases supplies and returns with receipts
    5. Cashier reconciles voucher with receipts
    6. If receipts total $48:
       Dr. Cash Over/Short            $2
       Cr. Petty Cash                 $2

Replenishment Workflow
----------------------

.. code-block:: text

    1. Fund balance falls below threshold (automatic or manual trigger)
    2. Replenishment request created for $500
    3. Manager approves replenishment
    4. Finance creates journal entry:
       Dr. Petty Cash                 $500
       Cr. Bank Account               $500
    5. Mark replenishment as done

Technical Information
=====================

Models
------

* ``dev.petty.fund`` - Petty cash fund configuration
* ``dev.petty.voucher`` - Voucher requests
* ``dev.petty.line`` - Voucher line items
* ``dev.petty.replenish`` - Replenishment requests
* ``dev.petty.dashboard.kpi`` - Dashboard KPI SQL view (read-only)
* ``dev.petty.dashboard.fund`` - Fund monitoring SQL view (read-only)

Security Groups
---------------

* ``dev_petty_cash.group_petty_user`` - Basic user access
* ``dev_petty_cash.group_petty_cashier`` - Cashier access
* ``dev_petty_cash.group_petty_manager`` - Full manager access

Dashboard access also requires:

* ``account.group_account_user`` - Accounting user access
* ``account.group_account_manager`` - Accounting manager access

Cron Jobs
---------

* ``ir_cron_check_replenishment_threshold`` - Daily check for funds below threshold
* ``ir_cron_alert_unreconciled_vouchers`` - Daily alert for unreconciled vouchers > 7 days
* ``ir_cron_dashboard_summary_email`` - Weekly dashboard summary email (disabled by default)

Email Templates
---------------

* ``email_template_voucher_requested`` - Notification when voucher submitted
* ``email_template_voucher_approved`` - Notification when voucher approved
* ``email_template_voucher_paid`` - Notification when voucher paid
* ``email_template_replenish_requested`` - Notification for replenishment request

Accounting Dashboard
====================

The dashboard provides real-time monitoring for finance teams.

Accessing the Dashboard
-----------------------

Navigate to: **Accounting → Petty Cash → Dashboard**

Available to users with:
- Petty Cash Manager group
- Accounting User group
- Accounting Manager group

Dashboard KPIs
--------------

The dashboard displays the following KPI cards:

**Fund Overview:**

* Total Petty Cash Float - Sum of all fund float amounts
* Total Available Balance - Current available cash across all funds
* Pending Approval Amount - Total awaiting approval
* Unreconciled Amount - Total paid but not reconciled

**Risk Indicators:**

* Funds Below Threshold - Count of funds needing replenishment
* Current Month Spend - MTD petty cash disbursements
* Total Variance - Sum of cash shortages/overages
* Missing Receipts - Vouchers without attached receipts

**Replenishment Status:**

* Pending Replenishment Amount - Total requested
* Pending Replenishment Count - Number of requests

Fund Monitoring Table
---------------------

Navigate to: **Accounting → Petty Cash → Fund Monitoring**

The fund monitoring view shows:

+-----------------+--------------------------------------------------+
| Column          | Description                                      |
+=================+==================================================+
| Fund Name       | Name of the petty cash fund                      |
+-----------------+--------------------------------------------------+
| Cashier         | Responsible user (custodian)                     |
+-----------------+--------------------------------------------------+
| Float Amount    | Maximum fund amount                              |
+-----------------+--------------------------------------------------+
| Available       | Current available balance                        |
+-----------------+--------------------------------------------------+
| Utilization %   | Percentage of float utilized                     |
+-----------------+--------------------------------------------------+
| Threshold       | Replenishment trigger level                      |
+-----------------+--------------------------------------------------+
| Last Replen.    | Date of last replenishment                       |
+-----------------+--------------------------------------------------+
| Pending         | Count of vouchers awaiting approval              |
+-----------------+--------------------------------------------------+
| Unrec.          | Count of unreconciled vouchers                   |
+-----------------+--------------------------------------------------+
| MTD Spend       | Month-to-date spending                           |
+-----------------+--------------------------------------------------+
| Status          | OK / Warning / Critical                          |
+-----------------+--------------------------------------------------+

**Status Logic:**

* **Critical** (Red): Available balance ≤ replenishment threshold
* **Warning** (Orange): Available balance < 30% of float amount
* **OK** (Green): Otherwise

Dashboard Alerts
----------------

The system provides automated alerts:

1. **Daily Alerts** (9:00 AM):
   - Funds below threshold
   - Vouchers unreconciled > 7 days
   - Creates activities for petty cash managers and account managers

2. **Weekly Summary** (Monday 8:00 AM, disabled by default):
   - Email summary of all KPIs
   - List of funds requiring attention
   - Enable via: Settings → Technical → Scheduled Actions

Performance Notes
-----------------

The dashboard uses PostgreSQL views for optimal performance:

* All aggregations performed in SQL (no ORM loops)
* Views are multi-company safe with company_id filtering
* Indexes on fund_id, state, and date fields
* COALESCE used for NULL safety

TODO / Customization Notes
==========================

The following items may need customization for your specific implementation:

.. code-block:: text

    # TODO: Configure your specific GL account codes
    # - Petty Cash Account: Replace with your chart of accounts code
    # - Expense Accounts: Set up expense categories per your requirements
    # - Variance Account: Configure cash over/short account

    # TODO: Email template recipients
    # - Update email_to fields in email templates for your organization
    # - Configure finance team notification recipients

    # TODO: Approval workflow
    # - Adjust approval thresholds if needed
    # - Add additional approval levels for high-value vouchers

Known Limitations
=================

* Vouchers can only be linked to one fund
* Partial payments are not supported (full amount or nothing)
* Tax calculations are informational only (not computed into totals)

Bug Tracker
===========

Report issues at: https://github.com/your-org/dev_petty_cash_management/issues

Credits
=======

Authors
-------

* Dev Team

Maintainers
-----------

This module is maintained by Dev Team.

Changelog
=========

17.0.1.0.0 (Initial Release)
----------------------------

* Initial release with core functionality
* Fund management with balance tracking
* Voucher workflow (draft → requested → approved → paid → reconciled)
* Accounting integration with journal entries
* Replenishment management
* PDF voucher reports
* Email notifications
* Scheduled threshold monitoring
* Multi-company support
