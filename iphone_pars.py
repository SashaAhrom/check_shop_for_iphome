import logging
import os
import requests
import sys
import telegram
import time
from bs4 import BeautifulSoup

from dotenv import load_dotenv

from exceptions import BadRequest

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - [%(levelname)s] - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RETRY_TIME = 1200

NAME_SHOPS = {
        '55-040 Wrocław': 'Aleja Bielany',
        '50-159 Wrocław': 'Galeria Dominikańska',
        '54-204 Wrocław': 'Magnolia Park'
    }

url = 'https://ispot.pl/apple-iphone-13-pro-256gb-graphite?from=listing&campaign-id=20&header=iPhone+13%20Pro#CheckAvailibility'
headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    'accept': '*/*'
}

    
def get_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find('ul', class_='list shop-list').find_all('li')
    citys = {}
    for item in items:
        city = item.find('span', class_='city').get_text().strip()
        status = item.find('div', class_='shop-availibility').find_next('span').get_text()
        citys[city] = status
    return citys
    
def parse():
    try:
        html = requests.get(url, headers=headers)
    except Exception as e:
        logger.error(f'Bad parsing: {e}')
    if html.status_code == 200:
        content = get_content(html.text)
        logger.info('сайт спаршен')
        return content
    else:
        raise BadRequest(f'Wrong code response {html.status_code}')
    


def send_message(bot, message):
    """Send message Telegram."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logger.info(f'Бот отправил сообщение {message}')    
                          
            
def main():
    """Baisic function."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    last_message = None
    while True:
        try:           
            last_message = {
                '55-040 Wrocław': 'Niedostępny',
                '50-159 Wrocław': 'Niedostępny',
                '54-204 Wrocław': 'Niedostępny'
                }
            date = parse()
            for city in last_message:
                if last_message[city] != date[city] and date[city] != 'Niedostępny':
                    last_message[city] = date[city]
                    message = f'В {NAME_SHOPS[city]} количество: {date[city]}.'
                    send_message(bot, message)
                elif last_message[city] != date[city] and date[city] == 'Niedostępny':
                    last_message[city] = date[city]
                    logger.info(f'В магазине {NAME_SHOPS[city]} все раскупли.')
                else:
                    logger.info(f'В магазине {NAME_SHOPS[city]} все по прежнему.')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            send_message(bot, message)
        else:
            time.sleep(RETRY_TIME)
            
if __name__ == '__main__':
    main()