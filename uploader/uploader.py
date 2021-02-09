import sys
import time, datetime
import copy

from posixpath import join as urljoin

import requests
import json
import pprint

sys.path.append('../')
from patches.utils import generate_checksum

from django.core import files

class Uploader():
    """
    For managing all the stuff

    the data dictionary you need to give it is of the form:
    {
    'recording': audio filename,
    'name': 'Entry title',
    'date': '2000-04-20T04:20:00' #strf %Y-%m-%dT%H:%M:%S 
    'authors' [list of display names],
    'license': the license number,
    'tags': [list of tag names],
    'desc': 'The entry description',
    'repo_attachments': [
        {'repo': url, 'commit':commit checksum, 'filename':filename },
        ],
    'images': [list of filenames],
    'attachments': [list of filenames]
    }

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

    def url(self, name):
        result = urljoin(self.base_url,'api', name)+'/'
        return result

    def __init__(self, base_url, data, auth, tag_resolution='ask'):
        """
        base_url is e.g. techtech.technologies/en/audio/
        data is a dictionary of the new entry to create
        auth is the requests authentication object
        tag_resolution is the method for dealing with new tags
            * ask: interactively ask the user to resolve each tag. This is the default
            * ignore: discard any tags that don't already exist
        """
        self.base_url = base_url
        self.auth = auth
        self.data = data
        if not tag_resolution.lower() in ['ask', 'ignore']:
            raise ValueError(f'Invalid tag resolution strategy - {tag_resolution}')
        self.tag_resolution = tag_resolution.lower()

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

    def dry_run(self):
        """
        Dry run test of uploading parts
        """
        print('*'*60)
        print('Doing dry run:')
        create_tags=[{'name':'ghost tag', 'description':'it is a ghost'}]
        r = self.post('tags', dry=True, data=create_tags[0])
        print('Created new tag ghost tag. API returned:')
        print(r.text)

        create_tags=[{'name':'bad tag', 'description':'it is a ghost'}]
        r = self.post('tags', dry=True, data=create_tags[0])
        print('Tried to create bad tag. API returned:')
        print(r.text)       

        print('Dry run finished.') 
        print('*'*60)

    def upload(self):
        """
        Do upload of self
        """
        valid_data = copy.deepcopy(self.data)
        valid_files = []
        valid_data['tags'] = []
        valid_data['images'] = []
        valid_data['attachments'] = []

        valid_files.append(('recording', open(self.data['recording'], 'rb')))

        #convert dates

        initial_time = self.data['date']
        if isinstance(initial_time, float):
            timestr = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(initial_time))
            valid_data['date'] = timestr

        #convert repo attachments to data for transfer
        try:
            valid_data['repo_attachments'] = json.dumps(self.data['repo_attachments'])
        except KeyError:
            pass

        #Get PK's of all tags and add missing tags as needed
        found_tags, missing_tags = self.get_tags()
        if self.tag_resolution == 'ask':
            fixed_tags = self.handle_missing_tags(missing_tags)
            found_tags.extend(fixed_tags)
        elif self.tag_resolution == 'ignore':
            print(f'Ignoring missing tags {missing_tags}')

        #add to valid data
        valid_data['tags'] = list(map(lambda x: x['name'], found_tags))

        #Determine new and existing images
        if 'images' in self.data.keys():
            found_images, missing_images = self.get_files('images', self.data['images'])
            valid_data['images'] = [x['id'] for x in found_images]
            for filename in missing_images:
                valid_files.append(('extra_images', open(filename, 'rb'))) 
        

        #Determine new and existing file attachments
        if 'attachments' in self.data.keys():
            found_att, missing_att = self.get_files('attachments', self.data['attachments'])
            valid_data['attachments'] = [x['id'] for x in found_att]
            for filename in missing_att:
                valid_files.append(('extra_attachments', open(filename, 'rb'))) 
      
        print('Uploading Data:')
        print(valid_data) 
        r = self.post('entries', dry=False, data=valid_data, files=valid_files)
        print('\nResponse Received:')
        print(r.text.replace('\n', ' '))


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
 

    def get_tags(self, tags= None):
        """
        Find all existing tags matching the names in tags
        Return found_tags, missing_tags
        found_tags = list of tag dictionaries
        missing_tags = list of tab names not found
        """
        if tags == None:
            tags = self.data['tags']
        r = self.get('tags', params = {'name': tags})
        found_tags = r.json()
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

    def _handle_missing_tag(self, tag):
        create = []
        fixed = []

        done = False
        while not done:
            option = input(
f"""Tag {tag} does not exist in the database. You may:
> try [name] - look for the given tag name and use that instead if it exists
> create     - create a new tag
> skip       - remove the tag from the upload
> """
)
            done = True
            cmd, *args = option.split(' ')
            cmd = cmd.lower()
            if cmd == 'try':
                if len(args) == 0:
                    print(f'Must give a new name to try.')
                    done = False
                    continue
                new_name = args[0]
                result, _ = self.get_tags([new_name])
                if len(result) == 0:
                    print(f'No matching tag for {new_name}')
                    done = False
                else:
                    fixed.extend(result)
            elif cmd == 'create':
                desc = input(f'Enter description for {tag}:\n')
                create.append({'name': tag, 'description': desc})
            elif cmd == 'skip':
                print(f'Skipping tag {tag}')
            else:
                print(f'Invalid option: {cmd}')
                done = False

        return create, fixed















