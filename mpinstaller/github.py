import base64
import json
import os
import requests
import shutil
import tempfile
import StringIO
from zipfile import ZipFile
from mpinstaller.mdapi import ApiRetrievePackaged
from mpinstaller.utils import zip_subfolder

# Mini GitHub API wrapper
def github_api(owner, repo, subpath, data=None, username=None, password=None):
    """ Takes a subpath under the repository (ex: /releases) and returns the json data from the api """
    api_url = 'https://api.github.com/repos/%s/%s%s' % (owner, repo, subpath)
    # Use Github Authentication if available for the repo
    kwargs = {}

    if not password:
        # Set password to an empty string instead of None
        password = ''

    if username:
        kwargs['auth'] = (username, password)

    if data is not None:
        resp = requests.post(api_url, data=json.dumps(data), **kwargs)
    else:
        resp = requests.get(api_url, **kwargs)

    try:
        data = json.loads(resp.content)
        return data
    except:
        return resp.status_code

class SalesforcePackageToGithub(object):
    
    def __init__(self, github_owner, github_repo, package_name, username, password, branch):
        self.github_owner = github_owner
        self.github_repo = github_repo
        self.package_name = package_name
        self.username = username
        self.password = password
        self.branch = branch
        self.tree = None
        self.new_tree = None

    def __call__(self, oauth, message, subpath=None):
        # Load metadata from the org into a local clone of the repo
        self.load_org_metadata(oauth)

        # Load repo metadata
        self.load_repo_metadata(subpath)

        # Build the new tree
        self.build_new_tree(subpath)

        # If there is nothing in new_tree, there is nothing to commit
        if not self.new_tree:
            return

        # Get the full recursive tree
        branch = self.call_api('/git/refs/heads/%s' % self.branch)
        commit = self.call_api('/git/commits/%s' % branch['object']['sha'])
        self.tree = self.call_api('/git/trees/%s?recursive=1' % commit['tree']['sha'])

        # Create the new tree
        self.new_tree = sorted(self.new_tree, key=lambda k: k['path']) 
        new_tree = self.call_api('/git/trees', {
            'base_tree': self.tree['sha'], 
            'tree': self.new_tree,
        })

        # Create a commit
        new_commit = self.call_api('/git/commits', {
            'message': message,
            'tree': new_tree['sha'],
            'parents': [commit['sha'],]
        })

        # Update the branch's head
        branch = self.call_api('/git/refs/heads/%s' % self.branch, {
            'sha': new_commit['sha'],
        })

        return new_commit

    def load_org_metadata(self, oauth):
        # Get the metadata from the org     
        org_metadata = ApiRetrievePackaged(oauth, self.package_name)()

        # Zip the package name folder's contents from the zip as a new zip
        self.org_metadata = zip_subfolder(org_metadata, self.package_name)

    def load_repo_metadata(self, subpath):
        # Download a copy of the head commit on the branch as a zip file
        response = requests.get('https://github.com/%s/%s/archive/%s.zip' % (self.github_owner, self.github_repo, self.branch))

        # Parse filename from the Content-Disposition header to add before path
        filename = response.headers['content-disposition'].split('; filename=')[-1]
        filename = filename.replace('.zip', '')

        repo_fp = StringIO.StringIO()
        repo_fp.write(response.content)
        repo_zip = ZipFile(repo_fp, 'r')

        subfolder = filename
        if subpath:
            subfolder += '/%s' % subpath

        self.repo = zip_subfolder(repo_zip, subfolder)
        
    def build_new_tree(self, subpath):
        # FIXME: we don't handle deleting files since that would require writing an entire new tree

        # Create a new empty tree list to hold updates
        self.new_tree = []

        # Use CRC comparisons to determine new and changed files
        for name in self.org_metadata.namelist():
            name_parts = name.split('/')
            try:
                if self.org_metadata.getinfo(name).CRC != self.repo.getinfo(name).CRC:
                    self.tree_update(name, subpath)
            except KeyError:
                # We get a KeyError if the file doesn't exist in the repo zip
                self.tree_add(name, subpath)
        
    def call_api(self, path, data=None):
        return github_api(
            self.github_owner,
            self.github_repo,
            path,
            data = data,
            username = self.username,
            password = self.password,
        )

    def tree_add(self, name, subpath):
        blob_file = self.org_metadata.open(name)

        if subpath:
            name = '%s/%s' % (subpath, name)

        # Add the blob to the tree
        self.new_tree.append({
            'path': name,
            'mode': '100644',
            'type': 'blob',
            'content': blob_file.read(),
        })

        blob_file.close()

    def tree_update(self, name, subpath):
        blob_file = self.org_metadata.open(name)

        if subpath:
            name = '%s/%s' % (subpath, name)

        # Update the blob in the tree
        self.new_tree.append({
            'path': name,
            'mode': '100644',
            'type': 'blob',
            'content': blob_file.read(),
        })
    
        blob_file.close()
