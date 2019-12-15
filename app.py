from flask import Flask,request
from currency_converter import *
import redis

app = Flask(__name__)

connection = redis.Redis(host='redis', port=6379, decode_responses=True)

@app.route('/')
def currency_converter():
    amount = request.args.get('amount')
    input_currency = request.args.get('input_currency')
    output_currency = request.args.get('output_currency')

    if amount is None or input_currency is None:
        return { 'error': 'Amount and input_currency are both required'}

    try:
        amount = float(amount)
    except ValueError:
        return { 'error': 'Amount must be float value'}

    input_currency = translate_currency_symbol_to_ISO(input_currency)
    if output_currency is not None:
        output_currency = translate_currency_symbol_to_ISO(output_currency)

    cc = FixerIOCurrencyConverter(connection, amount, input_currency[0], output_currency)
    try:
        cc.download_data()
        result = cc.calculate()
    except CurrencyConverterConnectionError:
        cc = EuropeanBankCurrencyConverter(connection, amount, input_currency[0], output_currency)
        try:
            cc.download_data()
            result = cc.calculate()
        except CurrencyConverterException as e:
            result = e.output

    except CurrencyConverterInternalError as e:
        result = e.output

    return result

if __name__ == '__main__':
    app.run()
