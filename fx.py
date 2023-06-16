import csv
import time
from collections import namedtuple
from datetime import datetime

import requests
from icecream import ic
from loguru import logger
from requests.exceptions import HTTPError, RequestException

Pair = namedtuple('Rate', ['currency_from', 'currency_to', 'bid', 'ask', 'last_update'])


class FxConverter:

    max_retry = 3

    def __init__(self):
        self._pairs = self._try_update()

    def _try_update(self):
        for i in range(self.max_retry):
            try:
                return self._update()
            except RequestException as e:
                logger.warning(str(e))
                time.sleep(5)
        return []

    def _update(self):
        url = 'https://forex.z.com/hk/price/latestPrice.csv'
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            raise HTTPError(f'status code = {resp.status_code}')
        ic(resp.text)
        lines = resp.text.split('\n')

        def parse(data):
            return Pair(
                currency_from=data[0][:3],
                currency_to=data[0][3:],
                bid=data[1],
                ask=data[2],
                last_update=datetime.strptime(data[-1], '%Y/%m/%d %H:%M:%S')
            )
        pairs = [parse(row) for row in csv.reader(lines) if row]
        return pairs

    def query(self, currency_from, currency_to):
        # TODO support cross pairs, e.g. compute GBP/JPY from USD/JPY and GBP/USD
        for pair in self._pairs:
            if pair.currency_from == currency_from and pair.currency_to == currency_to:
                dp = len(pair.bid.split('.')[-1])
                return round((float(pair.bid) + float(pair.ask)) / 2, dp)
            elif pair.currency_from == currency_to and pair.currency_to == currency_from:
                dp = len(pair.bid.split('.')[-1])
                return round(2 / (float(pair.bid) + float(pair.ask)), dp)
        return None


if __name__ == '__main__':
    fx = FxConverter()
    ic(fx.query('EUR', "USD"))
    ic(fx.query('USD', "EUR"))
