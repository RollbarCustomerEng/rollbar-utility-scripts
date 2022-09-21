from http.client import HTTPException
import json
import logging
import os
import requests


#
# Get/Create your ACCOUNT_READ_SCOPE_ACCESS_TOKEN here
# https://rollbar.com/settings/accounts/YOUR_ACCOUNT_SLUG/access_tokens/
#
# Execute these from a terminal to create an environment variable with you access tokem
# export ACCOUNT_READ_ACCESS_TOKEN_FOR_METRICS=**********
#
ACCOUNT_READ_TOKEN = os.environ['ACCOUNT_READ_ACCESS_TOKEN_FOR_METRICS']


#
# We only look for project_access_tokens with these names
# The project_access_tokens MUST be 'read' scope ONLY
#
ALLOWED_PROJECT_TOKEN_NAMES = ['devops_team_read_token', 'read']



class Project:
    """
    A small class to store Rollbar Project details
    """

    def __init__(self):
        self.id = None
        self.name = None
        self.token = None



def get_all_projects(account_read_token):
    """
    Use this method to get the list of Projects in an account

    Arguments:
    account_read_token - An Account level access token with Read scope

    Returns:
    List of Project object with id and name properties populated (Doesnt set the token property)
    """


    url = 'https://api.rollbar.com/api/1/projects'
    headers = {'X-Rollbar-Access-Token': account_read_token}

    proj_list = []
    try:
        resp = requests.get(url, headers=headers)
        log = '/api/1/projects status={}'.format(resp.status_code)
        logging.info(log)

        dct = json.loads(resp.text)['result']

        for item in dct:
            if item['status'] == 'enabled':
                p = Project()
                p.id = item['id']
                p.name = item['name']
                proj_list.append(p)
        
    except Exception as ex:
        logging.error('Error making request to Rollbar Metrics API', exc_info=ex)

    return proj_list

def add_read_token_to_projects(proj_list, account_read_token, allowed_project_token_names):
    #
    # For each project object in proj_list add the token property
    #

    headers = {'X-Rollbar-Access-Token': account_read_token}

    for proj in proj_list:
        url = 'https://api.rollbar.com/api/1/project/{}/access_tokens'
        url = url.format(proj.id)

        resp = requests.get(url, headers=headers)
        log = '{} /api/1/project/{}/access_tokens status={}'.format(proj.name, proj.id, resp.status_code)
        logging.info(log)

        token_list = json.loads(resp.text)['result']
        for token in token_list:
            if token['name'] in allowed_project_token_names and \
                 len(token['scopes']) == 1 and \
                 token['scopes'][0] == 'read':
                proj.token = token['access_token']
                continue


def get_token_data_for_project(proj):

    url = "https://api.rollbar.com/api/1/project/{}/access_tokens".format(proj.id)

    headers = {"X-Rollbar-Access-Token": ACCOUNT_READ_TOKEN,
                "accept": "application/json"
              }

    token_data_list = []
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print('Error getting project access token data for ', proj.name, resp.status_code)
            return []

        token_list = json.loads(resp.text)['result']

        for token in token_list:
            token['access_token'] = '****' + token['access_token'][-5:]
            token_data_list.append(token)

    except Exception as ex:
        print(ex)

    return token_data_list


def print_token_details():
    proj_list = get_project_details()
    
    token_data_list = []
    for proj in proj_list:
        token_data_list.append(get_token_data_for_project(proj))

    
    for token_data in token_data_list:
        print(token_data)



def get_project_details():

    print('Getting project tokens for each project')
    # Get project name and project_id
    proj_list = get_all_projects(ACCOUNT_READ_TOKEN)

    print('Completed getting project read tokens')

    return proj_list

if __name__ == "__main__":
    print_token_details()
