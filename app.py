from flask import Flask
from currency_converter import FixerIOCurrencyConverter
import redis

app = Flask(__name__)

connection = redis.Redis(host='redis', port=6379, decode_responses=True)


@app.route('/')
def currency_converter():
    cc = FixerIOCurrencyConverter(connection, 100, "EUR", "USD")
    cc.download_data()
    return cc.calculate()


if __name__ == '__main__':
    app.run()
