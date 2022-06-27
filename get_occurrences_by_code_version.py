import argparse
import json
import logging
import requests
import sys
import textwrap
import time

import get_occurrences as go 


class ItemDetail:
    #
    # Class that holds min and max occurrence ids in the version/environment
    #
    def __init__(self, id, first_occ_id_in_version, last_occ_id_in_version) -> None:
        self.id = id
        self.first_occ_id_in_version = first_occ_id_in_version
        self.last_occ_id_in_version = last_occ_id_in_version
    
    def __repr__(self):
        msg = '(id={} first_occ_id_in_version={} last_occ_id_in_version={})'
        msg = msg.format(self.id, self.first_occ_id_in_version, self.last_occ_id_in_version)

        return msg


class CheckBuildException(Exception):
    pass

class CheckBuidlHelpFormatter(argparse.HelpFormatter):
    def _fill_text(self, text, width, indent):
        return "\n".join([textwrap.fill(line, width) for line in textwrap.indent(textwrap.dedent(text), indent).splitlines()])


class ItemOccurrencesInVersion:


    # See the API parameter details here
    # https://explorer.docs.rollbar.com/#tag/Versions/paths/~1api~11~1versions~1{version}~1items/get

    VERSIONS_URL = 'https://api.rollbar.com/api/1/versions/{}/items'

    # Default comma separated levels that will be chosen
    LEVELS = 'error,critical'

    # Default event type can be chosen 'new', 'repeated', 'reactivated', 'resolved'
    EVENT = 'new' 


    REQUEST_RETRIES = 3

    def __init__(self, access_token, code_version, environment, levels, event):
        """
        access_token - Rollbar project access token with read scope
        code_version - Typically a GIT commit SHA
        environment - The environment the code is running in
        levels - comma separated list of levels
        event - The type of event we want the data for
        """

        # verify that parameters are within allowed ranges
        ItemOccurrencesInVersion.validate_input(access_token, code_version, environment)

        self.access_token = access_token
        self.code_version = code_version
        self.environment = environment

        self.levels = levels
        self.event = event

        # list of items in the code_version/environment combination
        self.items = None



    @staticmethod
    def validate_input(access_token: str, code_version: str, environment: str):

        """
        verify that each parameter has an allowed value
        """

        # access_token is 36 character alpha_numeric
        is_str = isinstance(access_token, str)
        is_alpha_num = access_token.isalnum()
        str_len = len(access_token)

        if is_str == False or is_alpha_num == False or str_len != 32:
            raise ValueError('The access_token argument is not valid')

        # code_version alpha_numeric (less than 200 chars)
        is_str = isinstance(code_version, str)
        str_len = len(code_version)

        if is_str == False or str_len > 200:
            raise ValueError('The code_version argument is not valid')

        # environment alpha_numeric with: ., _, or - (less than 200 chars)
        environment = environment.replace('.', '')
        environment = environment.replace('-', '')
        environment = environment.replace('_', '')
        is_str = isinstance(environment, str)
        is_alpha_num = environment.isalnum()
        str_len = len(environment)

        if is_str == False or is_alpha_num == False or str_len > 200:
            raise ValueError('The environment argument is not valid')


    def print_occurrences(self):

        item: ItemDetail

        # print basic information about the occurrenes to the screen
        for item in self.items:
            go.print_item_occurrences(self.access_token, item.id, 
                                    item.first_occ_id_in_version, 
                                    item.last_occ_id_in_version)


    def set_items_in_version(self):
        """
        Call the Rollbar Versions API
        Populate the self.items object with the occurrence information
        """

        web_resp_text = self.make_api_call()
        self.populate_item_details(web_resp_text)


    def make_api_call(self):
        """
        Make call to Rollbar Versions API
        Return the response JSON string 
        """

        # retry a few times if request fails
        resp : requests.Response
        for i in range(0, self.REQUEST_RETRIES):
            resp = self.make_versions_api_call()

            if not resp or resp.status_code != 200:
                time.sleep(3)
            else:
                break


        return resp.text


    def make_versions_api_call(self):
        """
        Call Rollbar Versions API. 
        Return Response object
        """

        resp = None
        try:
            url = self.VERSIONS_URL.format(self.code_version)
            params = {'environment': self.environment,
                        'event': self.event,
                        'level': self.levels
                    }
            headers = {'X-Rollbar-Access-Token': self.access_token}

            resp = requests.get(url, params=params, headers=headers)
        except Exception as ex:
            logging.error('Error making request to Rollbar Versions API', exc_info=ex)


        return resp

    
    def populate_item_details(self, web_resp_text):
        """
        Get the counts for each type of item new, reactivated, repeated, resolved
        """

        json_data = json.loads(web_resp_text)
        # see https://explorer.docs.rollbar.com/#tag/Versions 
        items = json_data['result']

        item_detail_list = []
        for item in items:
            item_detail = ItemDetail(item['id'],
                                     item['first_in_version_occurrence_id'],
                                     item['last_occurrence_id'])
            item_detail_list.append(item_detail)

        self.items = item_detail_list


def parse_args():

    desc =  f'''
        Get all occurrences for New items in a code_verion running in an environment
        '''

    parser = argparse.ArgumentParser(description=desc, 
                                     formatter_class=CheckBuidlHelpFormatter)

    # required
    parser.add_argument('--access-token', type=str, required=True, 
        help='Rollbar project access token with read scope')
    parser.add_argument('--code-version', type=str, required=True, 
                        help='The code version of the application')
    parser.add_argument('--environment', type=str, required=True,
        help='The environment the application is running in')


    # optional
    parser.add_argument('--levels', type=str, default=ItemOccurrencesInVersion.LEVELS, 
        help='The comma separated list of item Levels we want the data for (critical,error,warning etc)')
    
    # optional
    parser.add_argument('--event', type=str, default=ItemOccurrencesInVersion.EVENT, 
        help='The type of event we want teh data for. Only pick 1 event type (new, reactivated,repeated, resolved')

    args = parser.parse_args()
    
    return args 


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO,
                        format='%(process)d-%(levelname)s-%(message)s',
                        handlers=[logging.StreamHandler()]
                        )
   
    args = parse_args()
    io = ItemOccurrencesInVersion(args.access_token, args.code_version, args.environment,
                                  args.levels, args.event)

    io.set_items_in_version()
    io.print_occurrences()