import requests
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from announcer import Announcer
from pushbullet import Pushbullet

BASE_URL='https://www.subito.it/annunci-italia/vendita/informatica/'
SEARCH='gtx 1050 ti'
MIN_PRICE=100
MAX_PRICE=200
QUERY_STRING=f'{BASE_URL}?q={"+".join(SEARCH.split())}&ps={MIN_PRICE}&pe={MAX_PRICE}'

load_dotenv()

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
    return [parse_item(i) for i in items]

def main():
    pb = Pushbullet(os.getenv('PUSHBULLET_API_KEY'))
    def on_new(items):
        for title, city, prov, link, price, when, ships in items:
            message_body = (
                f'{title} at {price}€ in {city} {prov}.',
                'Shipment available.' if ships else '',
                f'Published {when}.',
                link
            )
            pb.push_note('Found new item', '\n'.join([s for s in message_body if s]))

    try:
        html = get_all_ads_page()
        items = parse_ads(html)
        announcer = Announcer(
            on_new=on_new, 
            initial=items[1:],
        )
        announcer.submit(items)
    except ConnectionError as err:
        print('Could\'t fetch ads.')

if __name__ == "__main__":
    main()