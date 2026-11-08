===========================
Currency Rate Update - NBRM
===========================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge2| image:: https://img.shields.io/badge/github-OCA%2Fl10n--macedonia-lightgray.png?logo=github
    :target: https://github.com/OCA/l10n-macedonia/tree/20.0/l10n_mk_currency_rate_update
    :alt: OCA/l10n-macedonia

|badge1| |badge2|

This module adds the National Bank of the Republic of North Macedonia
(NBRM) as a provider for *Currency Rate Update*. It imports the middle
exchange rates of the NBRM exchange rate list (Курсна листа).

NBRM publishes a list for every calendar day. Each rate is stored on the
date the list applies to, not on the date it was formed.

**Table of contents**

.. contents::
   :local:

Configuration
=============

To configure the NBRM provider:

1. Go to *Invoicing > Configuration > Currency Rates Providers* and
   create a provider with *National Bank of the Republic of North
   Macedonia* as provider.
2. Choose the currencies to update. The company currency does not have
   to be MKD: rates are converted through the MKD rates NBRM publishes.
3. Enable automatic currency rates updates in the accounting settings.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-macedonia/issues>`_.
In case of trouble, please check there if your issue has already been reported.

Credits
=======

Authors
-------

* Lambda IS

Contributors
------------

- Darko Nikolovski <darko@versada.eu>
- Kiril Vangelovski <kiril@lambda-is.com>

Maintainers
-----------

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

This module is part of the `OCA/l10n-macedonia <https://github.com/OCA/l10n-macedonia/tree/20.0/l10n_mk_currency_rate_update>`_ project on GitHub.

You are welcome to contribute. To learn how please visit https://odoo-community.org/page/Contribute.
