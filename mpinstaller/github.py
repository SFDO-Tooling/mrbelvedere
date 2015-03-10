import base64
import git
import json
import os
import requests
import shutil
import tempfile
from mpinstaller.mdapi import ApiRetrievePackaged

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
        self.load_org_metadata(oauth, subpath)

        if not self.repo.index.diff(None):
            return

        # Get the full recursive tree
        branch = self.call_api('/git/refs/heads/%s' % self.branch)
        commit = self.call_api('/git/commits/%s' % branch['object']['sha'])
        self.tree = self.call_api('/git/trees/%s?recursive=1' % commit['tree']['sha'])

        # Loop through each diff and update the tree
        for diff in self.repo.index.diff(None):
            if diff.deleted_file:
                # FIXME: Implement delete handling
                pass
            elif diff.renamed:
                # FIXME: Implement rename handling
                pass
            elif diff.new_file:
                self.tree_add(diff)
            else:
                self.tree_update(diff)

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

    def load_org_metadata(self, oauth, subpath):
        # Get the metadata from the org     
        self.org_metadata = ApiRetrievePackaged(oauth, self.package_name)()

        # Clone the git repo locally 
        self.repo_dir = tempfile.mkdtemp()
        self.repo = git.Repo.clone_from('https://github.com/%s/%s' % (self.github_owner, self.github_repo), self.repo_dir, branch=self.branch)

        # Create a new empty tree list to hold updates
        self.new_tree = []

        # Extract the org metadata on top of the local repo
        self.extract_metadata_to_repo(subpath)

    def call_api(self, path, data=None):
        return github_api(
            self.github_owner,
            self.github_repo,
            path,
            data = data,
            username = self.username,
            password = self.password,
        )

    def extract_metadata_to_repo(self, subpath=None):
        for filename in self.org_metadata.namelist():
            if subpath:
                path = self.repo_dir + '/' + subpath + '/' + '/'.join(filename.split('/')[1:])
            else:
                path = self.repo_dir + '/' + '/'.join(filename.split('/')[1:])
            path_dir = os.path.dirname(path)
            if not os.path.exists(path_dir):
                os.makedirs(path_dir)
        
            source = self.org_metadata.open(filename)
            target = open(path, 'w')
            shutil.copyfileobj(source, target)

        if self.repo.untracked_files: 
            self.repo.index.add(self.repo.untracked_files)

    def tree_add(self, diff):
        blob_file = open(os.path.join(*(self.repo_dir, diff.a_blob.path)), 'r')

        # Add the blob to the tree
        self.new_tree.append({
            'path': diff.a_blob.path,
            'mode': '100644',
            'type': 'blob',
            'content': blob_file.read(),
        })

        blob_file.close()

    def tree_update(self, diff):
        blob_file = open(os.path.join(*(self.repo_dir, diff.a_blob.path)), 'r')

        # Update the blob in the tree
        self.new_tree.append({
            'path': diff.a_blob.path,
            'mode': '100644',
            'type': 'blob',
            'content': blob_file.read(),
        })
    
        blob_file.close()
