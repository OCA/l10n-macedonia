# Copyright 2018 Lambda IS DOOEL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, timedelta
from unittest import mock

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

_module_ns = "odoo.addons.l10n_mk_currency_rate_update"
_file_ns = _module_ns + ".models.res_currency_rate_provider_nbrm"

# Middle rates (MKD per unit) from the NBRM exchange rate list of 08.11.2026
_RATES = {
    "EUR": 61.4996,
    "USD": 55.0825,
    "GBP": 73.7273,
    "CHF": 67.2641,
    "RSD": 0.523,
}


def _parse_nbrm_date(value):
    day, month, year = (int(part) for part in value.split("."))
    return date(year, month, day)


def _fake_get(url, params=None, timeout=None):
    """NBRM-like JSON with a list for every day of the requested range, so that
    the tests do not depend on the NBRM web service."""
    day = _parse_nbrm_date(params["StartDate"])
    last_day = _parse_nbrm_date(params["EndDate"])
    rows = []
    while day <= last_day:
        for code, rate in _RATES.items():
            rows.append(
                {
                    "datum": f"{day.isoformat()}T00:00:00",
                    # Formed on the previous day, applies to "datum"
                    "datum_f": f"{(day - timedelta(days=1)).isoformat()}T00:00:00",
                    "oznaka": code,
                    "nomin": 1,
                    "sreden": rate,
                }
            )
        day += timedelta(days=1)
    response = mock.Mock()
    response.json.return_value = rows
    return response


@tagged("post_install", "-at_install")
class TestCurrencyRateUpdateNBRM(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.startClassPatcher(mock.patch(_file_ns + ".requests.get", _fake_get))

        cls.CurrencyRate = cls.env["res.currency.rate"]
        cls.CurrencyRateProvider = cls.env["res.currency.rate.provider"]

        cls.today = fields.Date.today()
        cls.mkd_currency = cls.env.ref("base.MKD")
        cls.eur_currency = cls.env.ref("base.EUR")
        cls.usd_currency = cls.env.ref("base.USD")
        (cls.mkd_currency | cls.eur_currency | cls.usd_currency).active = True
        cls.company = cls.env["res.company"].create(
            {"name": "Test company", "currency_id": cls.mkd_currency.id}
        )
        cls.env.user.company_ids += cls.company
        cls.env.user.company_id = cls.company
        cls.nbrm_provider = cls.CurrencyRateProvider.create(
            {
                "service": "NBRM",
                "company_id": cls.company.id,
                "currency_ids": [
                    (4, cls.eur_currency.id),
                    (4, cls.usd_currency.id),
                    (4, cls.mkd_currency.id),
                ],
            }
        )
        cls.CurrencyRate.search([]).unlink()

    def _rate(self, currency, rate_date):
        return self.CurrencyRate.search(
            [
                ("company_id", "=", self.company.id),
                ("currency_id", "=", currency.id),
                ("name", "=", rate_date),
            ]
        )

    def test_supported_currencies(self):
        supported = self.nbrm_provider._get_supported_currencies()
        for code in ("MKD", "EUR", "USD", "RSD"):
            self.assertIn(code, supported)
        self.assertIn(self.usd_currency, self.nbrm_provider.available_currency_ids)

    def test_update_mkd_company(self):
        rate_date = date(2026, 11, 8)
        self.nbrm_provider._update(rate_date, rate_date)

        usd_rate = self._rate(self.usd_currency, rate_date)
        self.assertEqual(len(usd_rate), 1)
        self.assertAlmostEqual(usd_rate.rate, 1 / 55.0825)
        self.assertAlmostEqual(
            self._rate(self.eur_currency, rate_date).rate, 1 / 61.4996
        )
        # The rate is stored on the date the list applies to
        self.assertFalse(self._rate(self.usd_currency, rate_date - timedelta(days=1)))
        self.assertFalse(self._rate(self.mkd_currency, rate_date))

    def test_update_eur_company(self):
        self.company.currency_id = self.eur_currency
        rate_date = date(2026, 11, 8)
        self.nbrm_provider._update(rate_date, rate_date)

        self.assertAlmostEqual(
            self._rate(self.usd_currency, rate_date).rate, 61.4996 / 55.0825
        )
        self.assertAlmostEqual(self._rate(self.mkd_currency, rate_date).rate, 61.4996)
        self.assertFalse(self._rate(self.eur_currency, rate_date))

    def test_update_month(self):
        date_from = self.today - relativedelta(months=1)
        self.nbrm_provider._update(date_from, self.today)

        rates = self.CurrencyRate.search(
            [
                ("company_id", "=", self.company.id),
                ("currency_id", "=", self.usd_currency.id),
            ]
        )
        self.assertEqual(len(rates), (self.today - date_from).days + 1)

    def test_update_scheduled(self):
        self.company.currency_rates_autoupdate = True
        self.nbrm_provider.interval_type = "days"
        self.nbrm_provider.interval_number = 1
        self.nbrm_provider.last_successful_run = self.today - relativedelta(days=3)
        self.nbrm_provider._scheduled_update()

        self.assertEqual(self.nbrm_provider.last_successful_run, self.today)
        self.assertTrue(self._rate(self.usd_currency, self.today))

    def test_unsupported_base_currency(self):
        self.company.currency_id = self.env.ref("base.JPY")
        self.env.ref("base.JPY").active = True
        messages = self.nbrm_provider.message_ids
        self.nbrm_provider._update(self.today, self.today)

        self.assertFalse(
            self.CurrencyRate.search([("company_id", "=", self.company.id)])
        )
        self.assertGreater(len(self.nbrm_provider.message_ids), len(messages))
