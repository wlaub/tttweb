import sys
import time, datetime
import copy

from posixpath import join as urljoin

import requests
import json
import pprint

import os
#print(os.getcwd())
#sys.path.append('../')

from ..patches.utils import generate_checksum

from django.core import files

class TTTAPI():
    """
    For querying the api

    License numbers:
    1 All rights reserved
    2 Creative Commons Attribution-NonCommercial-NoDerivs 3.0 Unported
    3 Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported
    4 Creative Commons Attribution-NoDerivs 3.0 Unported
    5 Creative Commons Attribution-NonCommercial 3.0 Unported
    6 Creative Commons Attribution-ShareAlike 3.0 Unported
    7 Creative Commons Attribution 3.0 Unported
    8 Public Domain

    """

    licenses = {
        1: 'All Rights Reserved',
        2: 'CC BY-NC-ND',
        3: 'CC BY-NC-SA',
        4: 'CC BY-ND',
        5: 'CC BY-NC',
        6: 'CC BY-SA',
        7: 'CC BY',
        8: 'Public Domain',
        }

    licenses_reverse = {v:k for k,v in licenses.items()}

    def url(self, name):
        result = urljoin(self.base_url,'api', name)+'/'
        return result

    def __init__(self, base_url, auth):
        """
        base_url is e.g. techtech.technologies/en/audio/
        auth is the requests authentication object
        """
        self.base_url = base_url + '/en/audio'
        self.auth = auth

    def post(self, target, dry = True, **kwargs):
        """
        Custom post function to work with dry runs
        """
        kwargs['data']['write'] = not dry
        kwargs['auth'] = self.auth
        r = requests.post(
            self.url(target),
            **kwargs
            )
        return r

    def get(self, target, **kwargs):
        r = requests.get(self.url(target), **kwargs)
        return r

    def get_name(self, name):
        r = self.get('entries', params={'names': [name]})
        return r.json()['results']

    def get_recording_name(self, name):
        r = self.get('entries', params={'filenames': [name]})
        return r.json()['results']

    def get_files(self, target, filenames):
        """
        Identify existing unique files by checksum. Can be used
        for both images and attachments
        """
        if len(filenames) == 0:
            return [],[]

        hashmap = {}
        for filename in filenames:
            with open(filename, 'rb') as fp:
                f = files.File(fp)
                checksum = generate_checksum(f)
                hashmap[checksum] = filename
        hashes = list(hashmap.keys())
        r = self.get(target, params={'checksums':hashes})
        found_files = r.json()
        found_names =list(map(lambda x: hashmap[x['checksum']], found_files))
        missing_files = []
        for filename in filenames:
            if not filename in found_names:
                missing_files.append(filename)

        print(target)
        print(found_files)
        print(missing_files)
        print('-'*80)

        return found_files, missing_files


    def get_authors(self, auths):
        """
        find authors matching the given list of display names
        """
        r = self.get('authors', params = {'display_name': auths})
        found_auths = r.json()['results']
        found_names = list(map(lambda x: x['display_name'], found_auths))
        missing_auths = []
        for auth in auths:
            if not auth in found_names:
                missing_auths.append(auth)
        return found_auths, missing_auths




    def get_tags(self, tags):
        """
        Find all existing tags matching the names in tags
        Return found_tags, missing_tags
        found_tags = list of tag dictionaries
        missing_tags = list of tab names not found
        """
        r = self.get('tags', params = {'name': tags})
        found_tags = r.json()['results']
        found_names = list(map(lambda x: x['name'].lower(), found_tags))
        missing_tags = []
        for tag in tags:
            if not tag.lower() in found_names:
                missing_tags.append(tag)
        return found_tags, missing_tags


    def handle_missing_tags(self, tags):
        """
        Ask the user about and deal with the given list of missing tags
        1. Try a different tag name (e.g. if there was a typo)
        2. Skip the tag
        3. Create a new tag
        return a list of pk's for the new tag's
        """
        create_tags = [] #new tags to create
        fixed_tags = [] #tags successfully looked up as list of tag dicts
        """
        for tag in tags:
            create, fixed = self._handle_missing_tag(tag)
            create_tags.extend(create)
            fixed_tags.extend(fixed)

        for create in create_tags:
            r = self.post('tags', dry=False, data = create)
            obj = r.json()
            if r.status_code == 201:
                print(f'Created tag: {obj["name"]}')
                fixed_tags.append(obj)
            else:
                pass
                print(f'Failed to create tag:')
                pprint.pprint(obj)

        return fixed_tags
        """

    def create_tags(self, tags, dry=False):
        """
        Given a list of tags of the form {"name", "description"}, create these
        tags on the server. Return a list of the server responses.
        """

        results = []        
        for tag in tags:
            r = self.post('tags', dry=dry, data = tag)
            obj = r.json()
            results.append([r.status_code, obj])

        return results








