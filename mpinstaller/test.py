import base64
import git
import json
import os
import shutil
import tempfile
from django.contrib.auth.models import User
from mpinstaller.mdapi import ApiRetrievePackaged
from mpinstaller.models import PackageVersion
from mpinstaller.models import PackageInstallationSession
from mpinstaller.github import SalesforcePackageToGithub

# Grab a Salesforce OAuth session from the db
session = PackageInstallationSession.objects.all()[43]

# Grab Github credentials
user = User.objects.get(username='jlantz')
social_auth = user.social_auth.filter(provider='github')[0]
social_auth.refresh_token()
pv = PackageVersion.objects.get(id=16)
gh_auth = {'username': social_auth.tokens['access_token'], 'password': ''}
oauth = json.loads(session.oauth)
print gh_auth

# Initialize the API wrapper
push = SalesforcePackageToGithub(
    github_owner = 'jlantz',
    github_repo = 'Cumulus',
    package_name = 'Cumulus',
    username = gh_auth['username'],
    password = gh_auth['password'],
    branch = 'feature/branch-in-fork-only',
)

# Call the API wrapper to retrieve from org and commit to Github
resp = push(
    oauth=oauth, 
    message='test commit',
    subpath=pv.subfolder,
)

print resp
import pdb; pdb.set_trace()
