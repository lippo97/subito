import logging
import os
import requests
import schedule
import time
from bs4 import BeautifulSoup
from announcer import Announcer
from pushbullet import Pushbullet

logging.basicConfig(level=logging.INFO)
BASE_URL='https://www.subito.it/annunci-italia/vendita/informatica/'
NUMBER='970'
SEARCH=f'gtx {NUMBER}'
MIN_PRICE=100
MAX_PRICE=250
QUERY_STRING=f'{BASE_URL}?q={"+".join(SEARCH.split())}&ps={MIN_PRICE}&pe={MAX_PRICE}'

def get_all_ads_page():
    r = requests.get(QUERY_STRING)
    if (r.status_code == 200):
        return r.text
    raise ConnectionError(r.status_code)

def parse_item(item_html):
    link = item_html.find('a')['href']
    data = [i.text for i in item_html.find_all('span', attrs={"aria-hidden": None})]
    name = item_html.find('h2').text
    city = data[0]
    prov = data[1]
    when = data[2]        
    sped = data[3] == 'Spedizione disponibile' if len(data) > 3 else False
    try: 
        price = int(item_html.select_one('p.price').text.split()[0])
    except AttributeError:
        price = 0
    return name, city, prov, link, price, when, sped

def parse_ads(text):
    soup = BeautifulSoup(text, 'html.parser')
    items = soup.select_one('div.items.visible').find_all('div', class_='items__item', id=False)
    return [parse_item(i) for i in items if NUMBER in parse_item(i)[0]]

def main():
    # Setup
    pb = Pushbullet(os.getenv('PUSHBULLET_API_KEY'))
    logging.info('Connected to Pushbullet successfully.')
    def on_new(items):
        for title, city, prov, link, price, when, ships in items:
            message_body = (
                f'{title} at {price}€ in {city} {prov}.',
                'Shipment available.' if ships else '',
                f'Published {when}.',
                link
            )
            pb.push_note('Found new item', '\n'.join([s for s in message_body if s]))
            logging.info('Pushed notification!')

    html = get_all_ads_page()
    items = parse_ads(html)
    
    announcer = Announcer(
        on_new=on_new, 
        initial=items,
    )

    def job():
        logging.debug('Running main job.')
        try:
            logging.debug('Fetching ads...')
            html = get_all_ads_page()
            logging.debug('Fetched ads successfully.')
            items = parse_ads(html)
            announcer.submit(items)
        except ConnectionError:
            logging.warning('Couldn\' fetch ads.')
    
    # Configure scheduler
    logging.debug('Configuring scheduler')
    schedule.every().minute.do(job)
    logging.info('Entering main loop')
    logging.info(f'Looking for {SEARCH}')
    # Loop 
    while(True):
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
