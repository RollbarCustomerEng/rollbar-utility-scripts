from datetime import datetime as dt
import json
import os
import time
import requests

def get_item_id(project_read_token, counter):
    
    url = 'https://api.rollbar.com/api/1/item_by_counter/{}'.format(counter)
    headers = {'X-Rollbar-Access-Token': project_read_token}
    
    resp = requests.get(url, headers=headers)
    res = json.loads(resp.text)['result']

    item_id = res['id']
    last_occ = res['last_occurrence_id']
    first_occ = res['first_occurrence_id']
    first_occ_date_time = dt.fromtimestamp(int(res['first_occurrence_timestamp']))

    print('')
    print('')
    print('Counter ', counter)
    print('Item ID', item_id)
    print('Most recent occurrence ID ', last_occ)
    print('Oldest occurrence ID ', first_occ)
    print('First occurrence time ', first_occ_date_time)
    print('Sleeping for 3 seconds')
    time.sleep(3)

    return item_id, last_occ, first_occ


def get_occurrence_batch(project_read_token, item_id, last_id):

    url = 'https://api.rollbar.com/api/1/item/{}/instances'.format(item_id)
    headers = {'X-Rollbar-Access-Token': project_read_token}
    params = {'lastId': str(last_id)}
    
    resp = requests.get(url, headers=headers, params=params)

    occ_list = json.loads(resp.text)['result']['instances']
    process_occurrences(occ_list)

    if len(occ_list) > 0:
        lowest_occ_id_in_batch = occ_list[-1]["id"]
    else:
        lowest_occ_id_in_batch = 0

    return lowest_occ_id_in_batch


def process_occurrences(occ_list):

    # Add your custom processing of returned occurrences here
    if len(occ_list) == 0:
        print('No occurrences in the list')

    for occ in occ_list:
        print_error_details(occ)


def print_error_details(occ):

    print(occ['id'])
    if 'data' in occ and 'body' in occ['data'] \
        and 'trace' in occ['data']['body'] \
        and  'exception' in occ['data']['body']['trace'] \
        and  'message' in occ['data']['body']['trace']['exception']:
        print(occ['data']['body']['trace']['exception']['message'])

def get_all(read_token, counter):

    item_id, last_occ, first_occ = get_item_id(read_token, counter)

    # Need to add 1 so that we dont miss the most recent occurrence
    last_occ = last_occ + 1

    while last_occ >= first_occ:
        last_occ = get_occurrence_batch(read_token, item_id, last_occ)



#
# CREATE 2 ENVIRONMENT VARIABLES
# 
# 1. ROLLBAR_READ_ACCESS_TOKEN
# This is a rollbar project access token with read scope
# See https://rollbar.com/ACCOUNT-NAME/PROJECT-NAME/settings/access_tokens/ 
#
# 2. ITEM_COUNTER
# This is the counter of the item. Its th number at the endof the URL when you open an item
# https://rollbar.com/ACCOUNT-NAME/PROJECT-NAME/items/ITEM-COUNTER/
#
# Create the environment variables using the following commands
#
# export ROLLBAR_READ_ACCESS_TOKEN=abcdef123456
# export ITEM_COUNTER=12345
#
# EXECUTE THE SCRIPT
#
# python3 get-occurrences.py
#

if __name__ == "__main__":

    read_token = os.getenv('ROLLBAR_READ_ACCESS_TOKEN')
    counter =  os.getenv('ITEM_COUNTER')
    get_all(read_token, counter)
