import asyncio
import json
import logging
import os
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
try:
    import pyppeteer
except ImportError:
    logger.error('Could not import pyppeteer')
    logger.info('installing pyppeteer')
    os.system('pip install pyppeteer')

from datetime import datetime, timedelta

from pyppeteer import launch
from pyppeteer.errors import ElementHandleError


async def fetch_exchange_rate() -> str:
    browser = await launch()
    page = await browser.newPage()
    await page.goto('https://www.google.com/finance/quote/USD-VND')
    try:
        exchange_rate_element = await page.querySelector('div.YMlKec.fxKbKc')
        exchange_rate = await page.evaluate('(element) => element.textContent', exchange_rate_element)
        await browser.close()
        return exchange_rate
    except ElementHandleError as e:
        logger.error('Error: %s', e)
        await browser.close()


def update_exchange_rate():
    try:
        with open('./exchange_rate.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        last_update = datetime.strptime(data['last_update'], '%Y-%m-%d %H:%M:%S.%f')
        now = datetime.now()
        time_difference = now - last_update
        if time_difference > timedelta(hours=5):
            logger.info("The data is too old and needs updating.")
            exchange_rate = float(asyncio.run(fetch_exchange_rate()).replace(",", ""))
        else:
            exchange_rate = data['exchange_rate']
    except FileNotFoundError:
        logger.info("This is the first launch.")
        exchange_rate = float(asyncio.run(fetch_exchange_rate()).replace(",", ""))
        with open('./exchange_rate.json', 'w', encoding='utf-8') as f:
            json.dump({
                'exchange_rate': exchange_rate,
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            }, f, indent=4)
    except Exception as e:
        logger.error('An error occurred while updating the exchange rate: %s', e)
        return None

    return exchange_rate

def convert_currency():
    exchange_rate = update_exchange_rate()
    logger.info('USD to VND exchange rate: {:,.2f}'.format(exchange_rate) )
    if exchange_rate is None:
        return

    try:
        usd = float(input('Input USD: '))
        vnd = usd * exchange_rate
        print('{:,.2f} USD = {:,.2f} VND'.format(usd, vnd))
    except ValueError:
        logger.error('Invalid input. Please enter a valid number.')

if __name__ == '__main__':
    convert_currency()
