#!/usr/bin/env python3

from abc import ABC, abstractmethod
import requests
import redis
import time
import json
import argparse
import xml.etree.ElementTree as ET

connection = redis.Redis(host='localhost', port=6379, decode_responses=True)

def translate_currency_symbol_to_ISO(symbol):
    try:
        return currency_symbol_to_ISO[symbol]
    except KeyError:
        return [symbol]

def main():
    parser = argparse.ArgumentParser(description='Converting amount in any currency.')
    parser.add_argument('--amount' , required=True, type=float, help='Amount in certain currency to be converted')
    parser.add_argument('--input_currency', required=True, type=str, help='Currency from which will be result calculated')
    parser.add_argument('--output_currency', type=str, default=None, help='Currency which we will be used for calculation')
    args = parser.parse_args()

    input_currency = translate_currency_symbol_to_ISO(args.input_currency)
    output_currency = None
    if args.output_currency is not None:
        output_currency = translate_currency_symbol_to_ISO(args.output_currency)

    # If there's more than one input currency value we use the first one from the list because it's
    # most preferred. For example for dollar sign $ theres ton of other currencies than just American dollar
    # which we use as input currency. Otherwise in output currencies we use all of them.
    currency_converter = FixerIOCurrencyConverter(connection, args.amount, input_currency[0], output_currency)
    try:
        currency_converter.download_data()
        result = currency_converter.calculate()
    except CurrencyConverterConnectionError:
        cc = EuropeanBankCurrencyConverter(connection, args.amount, input_currency[0], output_currency)
        try:
            cc.download_data()
            result = cc.calculate()
        except CurrencyConverterException as e:
            result = e.output
    except CurrencyConverterInternalError as e:
        result = e.output

    output = json.dumps(result, indent=4)
    print(output)


class CurrencyConverterException(Exception):

    def __init__(self, msg = None ,output_dict = dict()):
        self.msg = msg
        self.output = output_dict
        self.output['output'] = {}
        self.output['output']['error'] = self.msg

# When this exception occurs, application can't further continue.
class CurrencyConverterInternalError(CurrencyConverterException):
    pass

# Otherwise when this exception occurs, you can try to use another class for currency converting.
class CurrencyConverterConnectionError(CurrencyConverterException):
    pass


class CurrencyConverterAbstract(ABC):
    def __init__(self, cache, amount, from_currency, to_currency=None):
        self.base = None # Rates are evaluated to this base currency
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.rates = {} # Here the rates will be stored
        self.amount = amount
        # This is template where all calculated data will be stored.
        self.result = {
            "input": {
                "amount": amount,
                "currency": from_currency,
            },
            "output": {
                # to_currency: result
            }
        }
        self.cache = cache

    @abstractmethod
    def download_data(self):
        pass # downloads data from any server and stores them into rates dictionary

    def convert_amount(self, to_currency):
        try:
            if self.base == self.from_currency:
                return self.amount * float(self.rates[to_currency])
            elif self.base == self.to_currency:
                return self.amount / float(self.rates[self.from_currency])
            else:
                in_base_currency = self.amount / float(self.rates[self.from_currency])
                return in_base_currency * float(self.rates[to_currency])
        except KeyError:
            raise CurrencyConverterInternalError('Invalid currency ISO', self.result)

    def calculate(self):
        if self.to_currency is None:
            for key in self.rates.keys():
                self.result['output'][key] = round(self.convert_amount(key), 2)
        else:
            for currency in self.to_currency:
                self.result['output'][currency] = round(self.convert_amount(currency), 2)

        return self.result

# Class for downloading data from fixer.io api service
class FixerIOCurrencyConverter(CurrencyConverterAbstract):
    def download_data(self):
        try:
            if self.cache.get('timestamp') is not None:
                # We check whether data is older than 1 hour because update on this API is set for 1 hour
                # If so, download data from fixerio server.
                # If not, take the cached data from redis.
                if time.time() - float(self.cache.get('timestamp')) > 3600:
                    self.__download_data_from_server()
                else:
                    self.__download_data_from_redis()
            else: # This is the first time downloading.
                self.__download_data_from_server()
        except redis.exceptions.RedisError:
            raise CurrencyConverterConnectionError

    def __download_data_from_redis(self):
        self.base = self.cache.get('base')
        self.rates = self.cache.hgetall('rates')

    def __download_data_from_server(self):
        url = 'http://data.fixer.io/api/latest'
        api_key = '5a2147cfaf5454e62ee55a605c947ae0'
        params = {'access_key': api_key}
        try:
            response = requests.get(url, params)
        except requests.exceptions.RequestException:
            raise CurrencyConverterConnectionError('Downloading data from host unsuccessful', self.result)
        if response.status_code != 200:
            raise CurrencyConverterConnectionError('Downloading data from host unsuccessful', self.result)
        data = response.json()
        if data['success']:
            self.cache.set('timestamp', data['timestamp'])
            self.base = data['base']
            self.cache.set('base', self.base)
            self.rates = data['rates'].copy()
            self.cache.hmset('rates', self.rates)
        else:
            raise CurrencyConverterConnectionError('Downloading data from host unsuccessful', self.result)

# This class download data from EuropeanBank xml endpoint
class EuropeanBankCurrencyConverter(CurrencyConverterAbstract):
    def download_data(self):
        self.base = 'EUR'
        url = 'https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml'
        try:
            r = requests.get(url)
        except requests.exceptions.RequestException:
            raise  CurrencyConverterConnectionError
        tree = ET.fromstring(r.text)
        for item in tree.findall('./{http://www.ecb.int/vocabulary/2002-08-01/eurofxref}Cube/{http://www.ecb.int/vocabulary/2002-08-01/eurofxref}Cube/'):
            self.rates[item.attrib['currency']] = float(item.attrib['rate'])



# Currency symbols translation from https://www.fxexchangerate.com/currency-symbols.html
currency_symbol_to_ISO = {
    '$': ['USD','AUD', 'ARS','KYD','CLP','COP','MOP', 'MXN', 'NZD'],
    '€': ['EUR'],
    'L': ['ALL', 'HNL', 'RON'],
    'دج': ['DZD'],
    'ƒ': ['AWG'],
    '£': ['GBP', 'FKP','SHP'],
    'B$': ['BSD' , 'BND'],
    '.د.ب': ['BHD'],
    'Tk': ['BDT'],
    'Br': ['BYR', 'ETB'],
    'BZ$': ['BZD'],
    'BD$': ['BMD'],
    'Nu.': ['BTN'],
    'Bs': ['BOB'],
    'P': ['BWP'],
    'R$': ['BRL'],
    'лв': ['BGN'],
    'FBu': ['BIF'],
    'C$': ['CAD', 'NIO'],
    '¥': ['CNY', 'JPY'],
    'Esc': ['CVE'],
    'BCEAO': ['XOF'],
    'BEAC': ['XAF'],
    '₡': ['CRC','SVC'],
    'kn': ['HRK'],
    '$MN': ['CUP'],
    'Kč': ['CZK'],
    'kr': ['DKK', 'ISK', 'NOK', 'SEK'],
    'Fdj': ['DJF'],
    'RD$': ['DOP'],
    'EC$': ['XCD'],
    'ج.م': ['EGP'],
    'FJ$': ['FJD'],
    'D': ['GMD'],
    'Q': ['GTQ'],
    'FG': ['GNF'],
    'GY$': ['GYD'],
    'HK$': ['HKD'],
    'Ft': ['HUF'],
    'Rp': ['IDR'],
    'Rs.': ['INR', 'PKR'],
    'ع.د': ['IQD'],
    '₪': ['ILS'],
    'KSh': ['KES'],
    '₩': ['KRW', 'KPW'],
    'د.ك': ['KWD'],
    'MK': ['MWK'],
    'RM': ['MYR'],
    'Rf': ['MVR'],
    'UM': ['MRO'],
    'Rs': ['MUR', 'NPR'],
    '₮': ['MNT'],
    'د.م.': ['MAD'],
    'K': ['MMK', 'PGK'],
    'N$': ['NAD'],
    'NAƒ': ['ANG'],
    '₦': ['NGN'],
    'ر.ع.': ['OMR'],
    'F': ['XPF'],
    'B': ['PAB'],
    'S/.': ['PEN'],
    '₱': ['PHP'],
    'zł': ['PLN'],
    'ر.ق': ['QAR'],
    'руб': ['RUB'],
    'RF': ['RWF'],
    'WS$': ['WST'],
    'Db': ['STD'],
    'ر.س': ['SAR'],
    'SR': ['SCR'],
    'Le': ['SLL'],
    'S$': ['SGD'],
    'Sk': ['SKK'],
    'SI$': ['SBD'],
    'So.': ['SOS'],
    'R': ['ZAR'],
    'ரூ': ['LKR'],
    '฿': ['THB'],
    'YTL': ['TRY'],
    'NT$': ['TWD'],
    'x': ['TZS'],
    'T$': ['TOP'],
    'د.ت': ['TND'],
    'د.إ': ['AED'],
    'USh': ['UGX'],
    'Vt': ['VUV'],
    '₫': ['VND'],
}


if __name__ == '__main__':
    main()

