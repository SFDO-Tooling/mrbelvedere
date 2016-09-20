# mrbelvedere

A Python/Django web application that runs on Heroku to assist Salesforce developers and ISVs in releasing metadata to end users

# Installation

## Deploy to Heroku

Click the link below to deploy mrbelvedere to Heroku.  Use the "App Name (optional)" field to select an available name for your Heroku app.  Before submitting the form, continue to the next step using the selected app name to create a Connected App and get the Client ID and Client Secret to complete the form. 

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## Salesforce Connected App

* Select a persistent Salesforce org (i.e. your business org if you're an ISV or your DE org if a developer)
* Go to Setup -> Create -> Apps
    * New Connected App
        * Scopes: full, api, refresh_token
        * Callback URL: https://<your-app-name>.herokuapp.com/mpinstaller/oauth/callback

## Post deploy configuration

Using the Heroku toolbelt, run the following command to create an admin user in the app's database

    heroku run python manage.py createsuperuser --app <your-app-name>

# Configuring the mrbelvedere installer

## Accessing admin

Go to https://<your-app-name>.herokuapp.com/admin and log in using the user you created in Post deploy configuration

## Creating a Package

## Creating Package Versions

### Managed Package Version

### Metadata Zip URL Version

### Github Version

## Creating Package Version Dependencies

# Using the Installer

# Analyzing and Supporting Installations

# Configuring the Contributor Tool

# Using the Contributor Tool
