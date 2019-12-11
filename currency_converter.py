#!/usr/bin/env python3

from abc import ABC, abstractmethod
import requests
import redis
import time
import json

connection = redis.Redis(host='localhost', port=6379, decode_responses=True)


def main():
    currency_converter = FixerIOCurrencyConverter(connection, 100, "EUR", "USD")
    currency_converter.download_data()
    result = currency_converter.calculate()

    a = json.dumps(result, indent=4)
    print(a)


class ApiException(Exception):
    pass


class CurrencyConverterAbstract(ABC):
    def __init__(self, cache, amount, from_currency, to_currency=None):
        self.base = None
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.rates = {}
        self.amount = amount
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
        pass

    def convert_amount(self, to_currency):
        if self.base == self.from_currency:
            return self.amount * float(self.rates[to_currency])
        elif self.base == self.to_currency:
            return self.amount / float(self.rates[to_currency])
        else:
            in_base_currency = self.amount / float(self.rates[self.from_currency])
            return in_base_currency * float(self.rates[to_currency])

    def calculate(self):
        if self.to_currency is None:
            for key in self.rates.keys():
                self.result['output'][key] = self.convert_amount(key)
        else:
            self.result['output'][self.to_currency] = self.convert_amount(self.to_currency)

        return self.result


class FixerIOCurrencyConverter(CurrencyConverterAbstract):
    def download_data(self):
        if self.cache.get('timestamp') is not None:
            if time.time() - float(self.cache.get('timestamp')) > 3600:
                self.__download_data_from_server()
            else:
                self.__download_data_from_redis()
        else:
            self.__download_data_from_server()

    def __download_data_from_redis(self):
        self.base = self.cache.get('base')
        self.rates = self.cache.hgetall('rates')

    def __download_data_from_server(self):
        url = 'http://data.fixer.io/api/latest'
        api_key = '5a2147cfaf5454e62ee55a605c947ae0'
        params = {'access_key': api_key}
        response = requests.get(url, params)
        if response.status_code != 200:
            raise ApiException()
        data = response.json()
        if data['success']:
            self.cache.set('timestamp', data['timestamp'])
            self.base = data['base']
            self.cache.set('base', self.base)
            self.rates = data['rates'].copy()
            self.cache.hmset('rates', self.rates)
        else:
            raise ApiException()


if __name__ == '__main__':
    main()