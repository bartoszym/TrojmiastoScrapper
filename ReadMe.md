# Trojmiasto scrapper
Simple scrapper which displays most important informations from announces on trojmiasto.pl

## Packages
* Celery
* some broker (I used Redis and instructions are for it)
* BeatifulSoup
* requests
* logging
* click

## Setup
Install required packages with `pip install -r requirements.txt`

## Starting
1. Start broker with ```redis-server```  
2. Open second terminal and type ```celery worker -A celery_troj -l info -c 10```  
3. Open another window of terminal and type ```python celery_troj.py```  
4. Go with instructions from script
