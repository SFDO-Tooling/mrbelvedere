# mrbelvedere

A build bot used to fill gaps in triggering jobs and interacting with the GitHub API for [CumulusCI](https://github.com/SalesforceFoundation/mrbelvedere).

## Key Functionality

* Create a framework to easily build custom logic around GitHub post-commit web hooks to trigger jobs in Jenkins
* Create triggers for commits on individual branches to trigger builds in Jenkins
* Automatically create new triggers for newly create jobs and branches based on their ref prefix
* Serve up the latest available production and beta Force.com managed package for a repository using GitHub Releases in the [CumulusCI](http://salesforcefoundation.github.io/CumulusCI/) process.
* Handle build authorization of pull requests via pull request comments posted by admin users

## Installation

mrbelvedere is a web application built on [Django](http://www.djangoproject.com).  These instructions cover deploying the app to [Heroku](https://www.heroku.com) though it should be possible to run it on your own server.

You will need the [heroku](https://devcenter.heroku.com/articles/quickstart) command line tool setup and linked to your Heroku account.

    git clone git@github.com:SalesforceFoundation/mrbelvedere
        Cloning into 'mrbelvedere'...
        remote: Counting objects: 133, done.
        remote: Compressing objects: 100% (56/56), done.
        remote: Total 133 (delta 72), reused 130 (delta 72)
        Receiving objects: 100% (133/133), 22.21 KiB | 0 bytes/s, done.
        Resolving deltas: 100% (72/72), done.
        Checking connectivity... done`

    cd mrbelvedere/
    
    heroku create
        Creating salty-journey-4106... done, stack is cedar
        http://salty-journey-4106.herokuapp.com/ | git@heroku.com:salty-journey-4106.git
        Git remote heroku added

    git remote -v
        heroku  git@heroku.com:salty-journey-4106.git (fetch)
        heroku  git@heroku.com:salty-journey-4106.git (push)
        origin  git@github.com:SalesforceFoundation/mrbelvedere (fetch)
        origin  git@github.com:SalesforceFoundation/mrbelvedere (push)
    
    git push heroku master
        The authenticity of host 'heroku.com (50.19.85.154)' can't be established.
        RSA key fingerprint is 8b:48:5e:67:0e:c9:16:47:32:f2:87:0c:1f:c8:60:ad.
        Are you sure you want to continue connecting (yes/no)? yes
        Warning: Permanently added 'heroku.com,50.19.85.154' (RSA) to the list of known hosts.
        Initializing repository, done.
        Counting objects: 133, done.
        Delta compression using up to 4 threads.
        Compressing objects: 100% (56/56), done.
        Writing objects: 100% (133/133), 22.21 KiB | 0 bytes/s, done.
        Total 133 (delta 72), reused 133 (delta 72)

        -----> Python app detected
        -----> No runtime.txt provided; assuming python-2.7.4.
        -----> Preparing Python runtime (python-2.7.4)
        -----> Installing Distribute (0.6.36)
        -----> Installing Pip (1.3.1)
        -----> Installing dependencies using Pip (1.3.1)
        Downloading/unpacking Django==1.5.4 (from -r requirements.txt (line 1))
        ...
        Running setup.py egg_info for package Django
        ...
        Installing collected packages: Django, South, amqp, anyjson, billiard, celery, decorator, distribute, dj-database-url, dj-static, django-rq, django-toolbelt, docutils, gunicorn, jenkinsapi, kombu, psycopg2, python-dateutil, pytz, redis, requests, rq, six, static, times
        Running setup.py install for Django
          changing mode of build/scripts-2.7/django-admin.py from 600 to 755
           
          changing mode of /app/.heroku/python/bin/django-admin.py to 755
         
        ...
         
        Successfully installed Django South amqp anyjson billiard celery decorator distribute dj-database-url dj-static django-rq django-toolbelt docutils gunicorn jenkinsapi kombu psycopg2 python-dateutil pytz redis requests rq six static times
        Cleaning up...

        -----> Discovering process types
          Procfile declares types -> web

        -----> Compressing... done, 38.1MB
        -----> Launching... done, v5
          http://salty-journey-4106.herokuapp.com deployed to Heroku

        To git@heroku.com:salty-journey-4106.git
          * [new branch]      master -> master


    heroku run python manage.py syncdb
        Running `python manage.py syncdb` attached to terminal... up, run.9882
        Syncing...
        Creating tables ...
        Creating table auth_permission
        Creating table auth_group_permissions
        Creating table auth_group
        Creating table auth_user_groups
        Creating table auth_user_user_permissions
        Creating table auth_user
        Creating table django_content_type
        Creating table django_session
        Creating table django_site
        Creating table django_admin_log
        Creating table south_migrationhistory
        
        You just installed Django's auth system, which means you don't have any superusers defined.
        Would you like to create one now? (yes/no): yes
        Username (leave blank to use 'u22151'): jlantz
        Email address: jlantz@salesforcefoundation.org
        Password: 
        Password (again): 
        Superuser created successfully.
        Installing custom SQL ...
        Installing indexes ...
        Installed 0 object(s) from 0 fixture(s)
        
        Synced:
        > django.contrib.auth
        > django.contrib.contenttypes
        > django.contrib.sessions
        > django.contrib.sites
        > django.contrib.messages
        > django.contrib.staticfiles
        > django.contrib.admin
        > django.contrib.admindocs
        > south
        > django_rq

        Not synced (use migrations):
        - mrbelvedere
        (use ./manage.py migrate to migrate these)


    heroku run python manage.py migrate
        Running `python manage.py migrate` attached to terminal... up, run.5334
        Running migrations for mrbelvedere:
        - Migrating forwards to 0004_auto__add_field_repository_username__add_field_repository_password.
        > mrbelvedere:0001_initial
        > mrbelvedere:0002_auto__add_field_repositorynewbranchjob_prefix
        > mrbelvedere:0003_auto__add_field_repository_owner
        > mrbelvedere:0004_auto__add_field_repository_username__add_field_repository_password
        - Loading initial data for mrbelvedere.
        Installed 0 object(s) from 0 fixture(s)

    heroku run python manage.py createcachetable cache
        Running `python manage.py createcachetable cache` attached to terminal... up, run.1060

At this point, your app should be running on Heroku where you can login using the created login at http://YOUR_APP.herokuapp.com/admin

## Configuration

Configuring the app is simple but not necessarily the most elegant process.  At some point in the future, more work will likely be done to build custom views for the following configurations but for now we just leverage Django's out of the box admin.

### Add Jenkins Site

1. In the Django admin for your app (http://YOUR_APP.herokuapp.com/admin), click the Add link for 'Jenkins Site'.
2. Enter a slug (becomes part of the url path for the site in the app), site url, and username/password.  If you are using the Github Authentication Plug In to handle Jenkins security as the [CumulusCI](https://github.com/SalesforceFoundation/CumulusCI/blob/master/docs/setup/README.md) setup documentation details, you need to go to your account in Jenkins and get your API token to use as the password.
3. Go to http://YOUR_APP.herokuapp.com/mrbelvedere/jenkins/YOUR_SLUG/update_jobs
4. Go back to the Django admin (http://YOUR_APP.herokuapp.com/admin)
5. Click on Jobs and you should see all your Jenkins jobs listed

### Create GitHub Webhook

1. In GitHub, login as your robot user account and click Account Settings -> Applications.  Create a new personal access token.  Copy the token when shown on screen.
2. In the Django admin, create a new repository.  Use the format git@github.com/SalesforceFoundation/mrbelvedere.git for the url.  NOTE: the format of the url is important as it is used as a key to lookup the repository by the webhook handlers.  Enter the Owner (i.e. SalesforceFoundation), the robot user's username, and the personal access token created in step 1 as the password.
3. Go to the url http://YOUR_APP.herokuapp.com/mrbelvedere/repo/OWNER/REPO_NAME/webhooks/create which will create the necessary webhooks agains the repository using the access information setup in step 2.
4. Do a commit against your repository
5. Check the **Pushs** section of the Django admin.  You should see the commit appear here.  Sometimes the webhook takes a few minutes to come through for the first time.

### Creating triggers

The mrbelvedere application is used by the [CumulusCI](https://github.com/SalesforceFoundation/CumulusCI) to trigger Jenkins jobs with logic not possible through the available Jenkins plugin community.

When mrbelvedere receives a GitHub post-commit webhook, it creates a Pull in the database.  The Pull is linked to a Repository, GithubUser, and Branch, all of which are created automatically if they did not previously exist.  These objects create a reference point to easily bind in custom trigger logic.

The triggers pass the branch name of the commit `branch` and the email of the last committer's `email` as parameters to the build job.

#### Manual triggers on branch commit

1. Go to the Django admin and Add a Branch Job Trigger.  Select the branch and select the job you want any commits to the branch to trigger.  So long as active is checked, any commits to the branch should trigger the job.

#### Automatic triggers on branch creation

Sometimes, it is helpful to create new job triggers against newly created branches using a prefix.  The CumulusCI process uses this for the Cumulus_feature, Cumulus_uat, and Cumulus_rel builds.

The system treats tags as branches just with different refs.  `refs/heads/*` refers to branches while `refs/tags/*` refers to tags.  This allows for creation of new Branch Job Triggers on creation of either a branch or a tag.

For example, the Cumulus_feature job should be triggered by any commit to a branch whose ref starts with `refs/heads/feature`.  To make the process easier for a developer, a Repository New Branch Job is created to automatically build a Branch Job Trigger on any feature branches to trigger the Cumulus_feature job.

The Cumulus_uat job triggers on creation of a new tag.  It's Repository New Branch Job prefix is `refs/tags/uat` and it triggers the Cumulus_uat job.

If no prefix is provided, all new branches or tags will have a Branch Job Trigger built for the specified job.

## Handling Force.com Managed Package Versions

mrbelvedere was built for use in [Project Cumulus](https://github.com/SalesforceFoundation/Cumulus) by the [Salesforce.com Foundation](http://www.salesforcefoundation.org).  We encountered a use case that was easiest solved by adding the functionality to the mrbelvedere application we were already using as part of our CI process.

**Use Case**: I want to fetch the current version number and corresponding repository tag for beta and production managed package releases.  We use GitHub's Releases section to publish releases.  However, a release must be tagged, then deployed to a packaging org, then published before it is available to install.  We don't want a Release's version to be published until it is available for install.  Once the managed package is available, we already paste the install url into the body of the Release on GitHub so it made sense to look for the latest Release with an install_url in the body for beta and production releases (beta = prerelease in GitHub).

Solution:
http://YOUR_APP.herokuapp.com/mrbelvedere/repo/OWNER/REPO_NAME/version
http://YOUR_APP.herokuapp.com/mrbelvedere/repo/OWNER/REPO_NAME/version/tag

http://YOUR_APP.herokuapp.com/mrbelvedere/repo/OWNER/REPO_NAME/version/beta
http://YOUR_APP.herokuapp.com/mrbelvedere/repo/OWNER/REPO_NAME/version/beta/tag

These links return either the version number (1.1 for production, 1.1 (Beta 3) for beta) or tag (rel/1.1 for production, uat/1.1-beta3 for beta).  The urls are called by both Jenkins and the Cumulus project's [build.xml](https://github.com/SalesforceFoundation/Cumulus/blob/master/build.xml) file to determine the most recent managed package.

## Pull Request Build Moderation

**Use Case**: I want to moderate builds of certain pull requests (submitted from within the repository and/or submitted through a fork).  If a pull request with a RepositoryPullRequestJob configuration matching the pull request is found, first check that the source branch is not behind the target branch by any commits.  If the source branch is behind, comment on the pull request that the target branch needs to be merged with the source branch.  Once the source branch is not beind the target branch, post a comment requesting an admin to approve build.  When an admin then posts `**mrbelvedere: approved**` anywhere in a comment on the pull request, the job configured in the RepositoryPullRequestJob will be triggered to build the source branch.  The pull request is then marked as approved and any subsequent commits will automatically re-trigger the build.  Whenever a build is triggered, post a comment that the build has started with a link to the build status page in Jenkins.  Whenever a build is completed, update the Commit Status in GitHub so the build shows on the pull request.

### Implementation

1. Create a Jenkins job which receives the `repository`, `branch`, and `email` parameters.  `email` should have a default value configured in Jenkins in case the email is not available from information in the GitHub API in which case no email parameter is passed to trigger the build.

2. Set the git repository to `${repository}` and branch to `origin/${branch}`

3. Using the Jenkins Notification Plugin, configure a Notification Endpoint under Job Notifications.  The endpoint should send JSON via HTTP to http://YOUR_APP.herokuapp.com/mrbelvedere/jenkins/YOUR_SLUG/post_build_webhook where YOUR_SLUG is the slug you entered for the Jenkins Site created earlier in the Django control panel.

4. Refresh your jobs: http://YOUR_APP.herokuapp.com/mrbelvedere/jenkins/YOUR_SLUG/update_jobs

5. In the Django control panel, add a new RepositoryPullRequestJob:
  
   **Repository**: Select the repository you want to monitor for pull requests
   **Job**: Select the Jenkins job you created in step 3
   **Moderated**: If checked, pull request builds must first be approved by an admin.  If unchecked, any matching pull request will automatically be built (dangerous, especially if building forks of a public repository)
   **Forked**: If checked, this rule applies to pull requests submitted from a forked repository (typically by external contributors)
   **Internal**: If checked, this rule applies to pull requests submitted from a branch within the main repository (typically by internal developers)
   **Repo admins**: If checked, any user with write access to the selected repository is automatically an admin capable of approving build of a pull request
   **Admins**: A manual list of authorized users.  Useful if you want to have admin users who can comment on a pull request but not write to the repository.  Also useful if you want to have only a subset of users with write access to the repository able to approve builds (Repo admins = False).

At this point, a new pull request submitted to the selected repository should have the use case fully implemented.
