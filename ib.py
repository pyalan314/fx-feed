import time

import pandas as pd
import requests
from loguru import logger
from requests.exceptions import RequestException, HTTPError


class IbRate:

    max_retry = 3

    def __init__(self):
        self._table = self._try_update()

    def _try_update(self):
        for i in range(self.max_retry):
            try:
                return self._update()
            except RequestException as e:
                logger.warning(str(e))
                time.sleep(5)
        return []

    def _update(self):
        # TODO pd warning 'A value is trying to be set on a copy of a slice from a DataFrame.'
        url = 'https://www.interactivebrokers.com/en/accounts/fees/pricing-interest-rates.php'
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            raise HTTPError(f'status code = {resp.status_code}')
        html = pd.read_html(resp.text)
        df = html[1]
        df['Currency'] = df['Currency'].shift(1)
        df = df[df['Currency'].notna()]
        df['Rate'] = df['Rate Paid:  IBKR Pro'].apply(lambda x: x.split(' (')[0])
        df['Rate'] = df['Rate'].apply(lambda x: x.replace(' ', ''))
        df['Currency'] = df['Currency'].apply(lambda x: x.replace('*', ''))
        return df[['Currency', 'Rate']]

    def query(self, currency):
        for index, row in self._table.iterrows():
            if row['Currency'] == currency:
                return row['Rate']
        return 'N/A'


if __name__ == '__main__':
    ib = IbRate()
    print(ib.query('USD'))
    print(ib.query('HKD'))
