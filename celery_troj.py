from celery import Celery, group, chain, chord
from bs4 import BeautifulSoup
import requests
import logging
import sys
import click


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt="%d-%m-%Y %H:%M:%S")

BROKER_URL = 'redis://localhost:6379/0'
BACKEND_URL = 'redis://localhost:6379/1'
app = Celery('celery_troj', broker=BROKER_URL, backend=BACKEND_URL)


@app.task
def fetch_url(url):
	try:
		resp = requests.get(url)
	except requests.exceptions.MissingSchema:
		return "Wrong URL, maybe missed 'http://'"
	
	try:
		resp.raise_for_status()
	except requests.HTTPError as err:
		if 400 <= err.response.status_code < 500:
			return 'Client error'
		if 500 <= err.response.status_code < 600:
			return 'Server error'

	return resp.text

@app.task
def parse_url(resptext):

	soup = BeautifulSoup(resptext, 'html.parser')
	toret = []
	for link in soup.findAll("a", {"class": "list__item__content__title__name link"}):
		toret.append(link['href'])

	if len(toret) == 0:
		return 0
	else:
		return toret

@app.task
def parse_product(resptext):
	titles = []
	photos = []
	prices = []

	for sth in resptext:
		soup = BeautifulSoup(sth, 'html.parser')

		title = (soup.find("h1", {"class": "title"})).text[1:]
		titles.append(title)

		photo = soup.find("a", {"data-fancybox": "photo"})
		if photo is not None:
			photo = photo['href']
		else:
			photo = 'brak zdjęcia'
		photos.append(photo)

		price = soup.find("span", {"class": "oglDetailsMoney"})
		if price is None:
			price = soup.find("span", {"class": "oglField__value"})
		price = price.text
		prices.append(price)

	return titles, photos, prices

@app.task
def fetch_products(urls):
	res = chord(fetch_url.s(url) for url in urls)( parse_product.s()).get(disable_sync_subtasks=False)
	return res

@click.command()
@click.option('--url', default='https://ogloszenia.trojmiasto.pl/elektronika/',
			  prompt='Page to request', help='Link to page.')
@click.option('--amount', default=1, prompt='Enter amount of pages '
											  'to load', help='Number of pages to load.')
def func(url, amount):
	logging.info('build chainning')
	chains =[chain(fetch_url.s(url+'?strona='+str(i)), parse_url.s(), fetch_products.s()) for i in range(int(amount))]
	g = group(*chains)
	logging.info('group created')
	result = g.apply_async()
	logging.info('group started')
	real_result = result.get()
	logging.info('done')
	for i, items in enumerate(real_result, 1):
		print('Wyniki z {} strony:'.format(i))
		for xyz in zip(*items):
			print(*xyz)
		print('\n')

if __name__ == "__main__":
	func()
