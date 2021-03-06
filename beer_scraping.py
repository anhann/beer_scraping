# Credit: referred to example code from https://thecodeforest.github.io/post/beers_and_text.html
# with modification to include more beer info and user review infor
import logging
from datetime import datetime
import os
import time
from contextlib import contextmanager
import urllib3
from bs4 import BeautifulSoup
import warnings
import re
from itertools import chain
from string import punctuation
import pandas as pd
warnings.filterwarnings('ignore')
HTTP = urllib3.PoolManager()
###
###
def create_dir(dir_name):
    try:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
    except OSError:
        print("Cannot Create Directory: {}".format(dir_name))
###
###
def collect_id(id_url, n_beers):
    pg_range = [str(x) for x in range(0, n_beers, 50)]
    pg_urls = [''.join(x) for x in zip([id_url] * len(pg_range), pg_range)]
    id_list = []
    for url in pg_urls:
        response = BeautifulSoup(HTTP.request('GET', id_url).data, 'lxml')
        for i in str(response.find('table')).split('href='):
            beer_id = i.split('/')[3:5]
            if sum([int(x.isdigit()) for x in beer_id]) == 2:
                id_list.append(beer_id)  
    return ['/'.join(x) + '/' for x in id_list]
###
###
def create_urls(beer_ids, n_reviews):
    profile_url_prefix = 'https://www.beeradvocate.com/beer/profile/'
    profile_url_suffix = '?view=beer&sort=&start='
    review_range = [str(x) for x in range(0, n_reviews, 50)]
    profile_url_p1 = [''.join(x) for x in zip([profile_url_prefix] * len(beer_ids), beer_ids)]
    complete_profile_url = []
    for url in profile_url_p1:
        complete_profile_url.append(
            [''.join(x) for x in zip([url] * len(review_range),
                                     [profile_url_suffix] * len(review_range),
                                     review_range
                                     )]
                                    )
    return list(chain(*complete_profile_url))
###
###
def collect_info(response, indiv_url, info_dir):
    beer_id = '-'.join(indiv_url.split('/')[5:7])
    fname = info_dir + beer_id + '-info.csv'
    try:
        name, brewer = str(response.find('title')).replace('title', '').split(' | ')[:2]
        name = ''.join([x for x in name if x not in punctuation])
        abv = (re.search(r'Alcohol by volume(.*)', str(response.find("div", {"id": "info_box"}))) 
           .group(1)
           .split(' ')[-1]
              )
        page_info_df = pd.DataFrame([beer_id, brewer, name, abv]).T
        page_info_df.columns = ['beer_id', 'brewer', 'beer_name', 'abv']
        page_info_df.to_csv(fname, index = False)
    except Exception as e:
        logging.debug('Unable to collect data for {}'.format(indiv_url))
        logging.debug(e)
###
###
def collect_reviews(response, indiv_url, review_dir, review_index):
    beer_id = '-'.join(indiv_url.split('/')[5:7])
    fname = review_dir + beer_id + '-review-' + str(review_index) + '.csv'
    reviews = [str(x) for x in list(response.find_all('div', {'class': 'user-comment'}))]
    page_reviews = []
    for index, review in enumerate(reviews):
        review_ind = [1 if len(x) > 0 else 0 for x in review.split('<br/>')]
        space_index = [index for index, x in enumerate(review_ind) if x == 0]
        if space_index[:2] == [2, 4]:
            review_txt = ' '.join(review.split('<br/>')[2:4])
            review_rating = re.search(r'\\| overall: (.*)</span>', review)
            page_reviews.append([beer_id,
                             review_txt, 
                             review_rating.group(1).split('<')[0]
                            ]
                           )
    if len(page_reviews) > 0:
        page_reviews_df = pd.DataFrame(page_reviews)
        page_reviews_df.columns = ['beer_id', 'review', 'rating']
        page_reviews_df.to_csv(fname, index = False)
        logging.debug('collected {} reviews for beer {}'.format(page_reviews_df.shape[0], beer_id))
###
###
def main():
    beer_id = '116'
    info_dir = 'beer_info/'
    review_dir = 'beer_reviews/'
    log_dir = 'beer_log/'
    create_dir(info_dir)
    create_dir(review_dir)
    create_dir(log_dir)
    n_beers = 500
    n_reviews = 500
    pause_time = 3
    # configure logging
    logging.basicConfig(filename=log_dir + 'BA.log',
                        level=logging.DEBUG,
                        format = '%(asctime)s - %(message)s'
                       )
    id_url = 'https://www.beeradvocate.com/beer/styles/{}/?sort=revsD&start='.format(beer_id)
    # collect ids for each beer
    beer_ids = collect_id(id_url, n_beers)
    # create urls for each page
    profile_urls = create_urls(beer_ids, n_beers)
    for review_index, indiv_url in enumerate(profile_urls):
        response_i = BeautifulSoup(HTTP.request('GET', indiv_url).data, 'lxml')
        if indiv_url[-1] == '0':
            print('Collecting Data for {}'.format(indiv_url))
            collect_info(response_i, indiv_url, info_dir)
        collect_reviews(response_i, indiv_url, review_dir, review_index)
        time.sleep(pause_time) 
###
###
if  __name__ ==  "__main__":
    main()

