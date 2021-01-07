import sys
import time, datetime
import copy

import requests
import json
import pprint

sys.path.append('../')
from patches.utils import generate_checksum

class Uploader():
    """
    For managing all the stuff
    """

    def url(self, name):
        return self.base_url+'api/'+name+'/'

    def __init__(self, base_url, data, auth):
        """
        base_url is e.g. techtech.technologies/en/audio/
        data is a dictionary of the new entry to create
        auth is the requests authentication object
        """
        self.base_url = base_url
        self.auth = auth
        self.data = data

    def post(self, target, dry = True, **kwargs):
        """
        Custom post function to work with dry runs
        """
        if not 'params' in kwargs.keys():
            kwargs['params'] = {}
        kwargs['params'].update({'write':not dry})
        kwargs['auth'] = self.auth
        r = requests.post(
            self.url(target),
            **kwargs
            )
        return r

    def dry_run(self):
        """
        Dry run test of uploading parts
        """
        print('Doing dry run:')
        create_tags=[{'name':'ghost tag', 'description':'it is a ghost'}]
        r = self.post('tags', dry=True, data=create_tags[0])
        print(r.text)       
 

    def upload(self):
        """
        Do upload of self
        """
        valid_data = copy.deepcopy(self.data)
        valid_data['tags'] = []
        valid_data['images'] = []
        valid_data['attachments'] = []
        valid_data['recording'] = None

        #convert repo attachments to data for transfer
        try:
            valid_data['repo_attachments'] = json.dumps(self.data['repo_attachments'])
        except KeyError:
            pass

        #Get PK's of all tags and add missing tags as needed
        found_tags, missing_tags = self.get_tags()
        fixed_tags = self.handle_missing_tags(missing_tags)
        found_tags.extend(fixed_tags)

        #add to valid data
        valid_data['tags'] = list(map(lambda x: x['id'], found_tags))

        self.get_attachments()

        print(valid_data)

    def get_attachments(self, attachments = None):
        if attachments == None:
            attachments = self.data['attachments']
        hashmap = {}
        for filename in attachments:
            with open(filename, 'rb') as fp:
                checksum = generate_checksum(fp)
            

    def get_tags(self, tags= None):
        """
        Retrieve the pk's for all of the tags in this entry
        Return found_tags, missing_tags
        found_tags = list of tag dictionaries
        missing_tags = list of tab names not found
        """
        if tags == None:
            tags = self.data['tags']
        r = requests.get(self.url('tags'), params = {'name':tags})
        found_tags = json.loads(r.text)
        found_names = list(map(lambda x: x['name'].lower(), found_tags))
        missing_tags = []
        for tag in tags:
            if not tag in found_names:
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















