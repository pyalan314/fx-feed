import csv
from datetime import datetime
from typing import NamedTuple

import requests
from icecream import ic
from loguru import logger
from requests.exceptions import HTTPError, RequestException
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_random, after_log

import exchange_rate


class Pair(NamedTuple):
    currency_from: str
    currency_to: str
    rate: float
    last_update: datetime


class FxConverter:

    def __init__(self, feeder_func):
        self._pairs: list[Pair] = []
        try:
            self._pairs = feeder_func()
        except Exception as e:
            logger.error(e)
        ic(self._pairs)
        self._rates = compute.compute_all_rates([(x.currency_from, x.currency_to, x.rate) for x in self._pairs])

    def query(self, currency_from, currency_to):
        try:
            return self._rates[currency_from][currency_to]
        except KeyError:
            return None


# noinspection PyTypeChecker
custom_after_log = after_log(logger, "ERROR")


@retry(retry=retry_if_exception_type(RequestException), stop=stop_after_attempt(3), wait=wait_random(2, 5), after=custom_after_log)
def zcom_feed() -> list[Pair]:
    url = 'https://forex.z.com/hk/price/latestPrice.csv'
    resp = requests.get(url, timeout=5)
    if resp.status_code != 200:
        raise HTTPError(f'status code = {resp.status_code}')
    lines = resp.text.split('\n')

    def parse(data):
        bid = data[1]
        ask = data[2]
        dp = len(bid.split('.')[-1])
        rate = round((float(bid) + float(ask))/2, dp)
        return Pair(
            currency_from=data[0][:3],
            currency_to=data[0][3:],
            rate=rate,
            last_update=datetime.strptime(data[-1], '%Y/%m/%d %H:%M:%S')
        )

    pairs = [parse(row) for row in csv.reader(lines) if row]
    return pairs


def get_converter() -> FxConverter:
    return FxConverter(zcom_feed)


if __name__ == '__main__':
    fx = get_converter()
    ic(fx.query('EUR', "USD"))
    ic(fx.query('USD', "EUR"))
    ic(fx.query('HKD', "AUD"))
    ic(fx.query('AUD', "HKD"))
