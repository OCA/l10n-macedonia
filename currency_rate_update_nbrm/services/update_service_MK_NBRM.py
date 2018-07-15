##############################################################################
#
#    Copyright (c) 2015 HacBee UAB. All rights reserved.
#    @author Darko Nikolovski
#
#    Copyright (c) 2018 Lambda IS DOOEL. All rights reserved.
#    @author Kiril Vangelovski
#
#    Abstract class to fetch rates from the National Bank of the Republic of Macedonia
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo.addons.currency_rate_update.services.currency_getter_interface import CurrencyGetterInterface

from datetime import datetime
from lxml import etree
from odoo import exceptions, _

import logging
import requests
_logger = logging.getLogger(__name__)


class MK_NBRMGetter(CurrencyGetterInterface):
    """Implementation of Currency_getter_factory interface for NBRM service"""

    code = 'MK_NBRM'
    name = 'National Bank of the Republic of Macedonia'
    supported_currency_array = [
        "EUR", "USD", "GBP", "CHF", "SEK", "NOK", "JPY", "DKK", "CAD", "AUD",
        "BGN", "CZK", "HUF", "PLN", "RON", "HRK", "TRY", "RUB", "BRL", "CNY",
        "HKD", "IDR", "ILS", "INR", "KRW", "MXN", "MYR", "NZD", "PHP", "SGD",
        "THB", "ZAR"]

    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days, date=False):
        """implementation of abstract method of Curreny_getter_interface

        Args:
        currency_array: List of currencies rates to fetch, e.g. ['EUR', 'USD'].
        main_currency: The converted currency, e.g. 'MKD'.
        max_delta_days: Max. days difference between the actual rate date
                        and today. Raises an exception if not satisfied.
        date: Rate date. Additional arg that enables to retrieve rate for an
              older date. This can be used in other modules when the wanted
              rate is not available in the db. This can happen for example
              when an invoice in a foreign currency is created with a backdate.
              The kwarg is specific for this service and not present in the
              parent class method signature.
        """

        url = "https://www.nbrm.mk/KLServiceNOV/GetExchangeRate?StartDate={StartDate}&EndDate={EndDate}&format=json"

        # we do not want to update the main currency
        if main_currency in currency_array:
            currency_array.remove(main_currency)

        # Get currencies for current day:
        rate_data_str = date or datetime.now().strftime('%d.%m.%Y')

        _logger.info("NBRM currency rate service : connecting...")
        resp = requests.get(url.format(
            StartDate=rate_data_str, EndDate=rate_data_str))

        if resp.status_code != 200:
            raise exceptions.Warning(
                _('Error occurred during getting currencies from NBRM'))
            _logger.info("The Service NBRM returned error: %s" % resp.text)

        result = resp.json()
        _logger.info("Received currency list from NBRM!")

        rate_date = result[0]["datum_f"]
        rate_date_datetime = datetime.strptime(rate_date.split('T')[0],
                                               "%Y-%m-%d")
        self.check_rate_date(rate_date_datetime, max_delta_days)

        # we dynamically update supported currencies
        self.supported_currency_array = [x['oznaka'] for x in result]

        self.supported_currency_array.append('MKD')
        _logger.info("Supported currencies = %s" %
                      self.supported_currency_array)

        self.validate_cur(main_currency)
        currency_data = {curr['oznaka']: curr for curr in result}
        if main_currency != 'MKD':
            main_curr_data = currency_data[main_currency]

        for curr in currency_array:
            self.validate_cur(curr)
            if curr == 'MKD':
                rate = 1 / main_curr_data['sreden']
            else:
                curr_data = currency_data[curr]
                if main_currency == 'MKD':
                    rate = 1 / curr_data['sreden']
                else:
                    rate = 1 / (
                        curr_data['sreden'] /
                        main_curr_data['sreden']
                    )

            self.updated_currency[curr] = rate
            _logger.debug(
                "Rate retrieved : 1 %s = %s %s" % (main_currency, rate, curr))

        return self.updated_currency, self.log_info
