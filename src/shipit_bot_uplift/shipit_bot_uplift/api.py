# -*- coding: utf-8 -*-
import mohawk
import requests
import json
import os
from cli_common.log import get_logger
from shipit_bot_uplift.helpers import ShipitJSONEncoder


logger = get_logger(__name__)


class NotFound(Exception):
    '''
    API 404 exception
    '''


class ApiClient(object):
    '''
    Api client to use remote shipit_uplift
    '''
    def setup(self, url, client_id, access_token):
        '''
        Setup API url & credentials
        '''
        self.api_url = url
        self.credentials = {
          'id': client_id,
          'key': access_token,
          'algorithm': 'sha256',
        }

    def list_analysis(self):
        '''
        List all analysis
        '''
        return self.make_request('get', '/analysis')

    def get_analysis(self, analysis_id):
        '''
        Get detailed analysis
        '''
        url = '/analysis/{}'.format(analysis_id)
        return self.make_request('get', url)

    def update_analysis(self, analysis_id, data):
        '''
        Update an analysis
        '''
        url = '/analysis/{}'.format(analysis_id)
        return self.make_request('put', url, data)

    def create_bug(self, data):
        '''
        Create (or update) a bug
        '''
        return self.make_request('post', '/bugs', data)

    def delete_bug(self, bugzilla_id):
        '''
        Delete a bug from its bugzilla id
        '''
        url = '/bugs/{}'.format(bugzilla_id)
        return self.make_request('delete', url)

    def list_patch_status(self, bugzilla_id):
        '''
        List all patch status linked to a bugzilla id
        '''
        url = '/bugs/{}/patches'.format(bugzilla_id)
        return self.make_request('get', url)

    def create_patch_status(self, bugzilla_id, data):
        '''
        Create a new patch status linked to a bugzilla id
        '''
        url = '/bugs/{}/patches'.format(bugzilla_id)
        return self.make_request('post', url, data)

    def make_request(self, method, url, data=None):
        '''
        Make an HAWK authenticated request on remote server
        Low level API access
        '''
        request = getattr(requests, method)
        if not request:
            raise Exception('Invalid method {}'.format(method))

        # Encode optional data as json
        if data is not None:
            data = json.dumps(data, cls=ShipitJSONEncoder)
        else:
            data = ''

        # Build HAWK token
        url = self.api_url + url
        hawk = mohawk.Sender(self.credentials,
                             url,
                             method,
                             content=data,
                             content_type='application/json')

        # Support dev ssl ca cert
        ssl_dev_ca = os.environ.get('SSL_DEV_CA')
        if ssl_dev_ca is not None:
            assert os.path.isdir(ssl_dev_ca), \
                'SSL_DEV_CA must be a dir with hashed dev ca certs'

        # Send request, using optional dev ca
        headers = {
            'Authorization': hawk.request_header,
            'Content-Type': 'application/json',
        }
        response = request(url, data=data, headers=headers, verify=ssl_dev_ca)
        if not response.ok:
            if response.status_code == 404:
                logger.warn('Not found response on {}'.format(url))
                raise NotFound
            raise Exception('Invalid response from {} {} : {}'.format(
                method, url, response.content))

        return response.json()


# Shared api client instance
api_client = ApiClient()
