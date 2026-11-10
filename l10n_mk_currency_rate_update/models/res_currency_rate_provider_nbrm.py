# Copyright 2015 HacBee UAB (Darko Nikolovski)
# Copyright 2018 Lambda IS DOOEL (Kiril Vangelovski)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from collections import defaultdict

import requests

from odoo import fields, models
from odoo.exceptions import UserError

NBRM_URL = "https://www.nbrm.mk/KLServiceNOV/GetExchangeRate"


class ResCurrencyRateProviderNBRM(models.Model):
    _inherit = "res.currency.rate.provider"

    service = fields.Selection(
        selection_add=[("NBRM", "National Bank of the Republic of North Macedonia")],
        ondelete={"NBRM": "set default"},
    )

    def _get_supported_currencies(self):
        self.ensure_one()
        if self.service != "NBRM":
            return super()._get_supported_currencies()  # pragma: no cover

        # List of currencies obtained from the NBRM exchange rate list:
        # https://www.nbrm.mk/kursna_lista.nspx
        return [
            "EUR",
            "USD",
            "GBP",
            "CHF",
            "SEK",
            "NOK",
            "JPY",
            "DKK",
            "CAD",
            "AUD",
            "CZK",
            "HUF",
            "PLN",
            "RON",
            "TRY",
            "RUB",
            "BRL",
            "CNY",
            "HKD",
            "IDR",
            "ILS",
            "INR",
            "KRW",
            "MXN",
            "MYR",
            "NZD",
            "PHP",
            "SGD",
            "THB",
            "ZAR",
            "RSD",
            "MKD",
        ]

    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service != "NBRM":
            return super()._obtain_rates(
                base_currency, currencies, date_from, date_to
            )  # pragma: no cover

        response = requests.get(
            NBRM_URL,
            params={
                "StartDate": date_from.strftime("%d.%m.%Y"),
                "EndDate": date_to.strftime("%d.%m.%Y"),
                "format": "json",
            },
            timeout=10,
        )
        response.raise_for_status()
        rows = response.json()

        # MKD per one unit of each currency, by the date the list applies to
        mkd_rates = defaultdict(dict)
        for row in rows:
            rate_date = fields.Date.to_date(row["datum"][:10])
            mkd_rates[rate_date.isoformat()][row["oznaka"]] = row["sreden"] / (
                row["nomin"] or 1
            )

        content = {}
        for rate_date, day_rates in mkd_rates.items():
            day_rates["MKD"] = 1.0
            if base_currency not in day_rates:
                raise UserError(
                    self.env._(
                        "The National Bank of the Republic of North Macedonia has"
                        " no rate for %(currency)s on %(date)s.",
                        currency=base_currency,
                        date=rate_date,
                    )
                )
            base_rate = day_rates[base_currency]
            content[rate_date] = {
                currency: base_rate / day_rates[currency]
                for currency in currencies
                if currency != base_currency and currency in day_rates
            }
        return content
