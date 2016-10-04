# mrbelvedere

A Python/Django web application that runs on Heroku to assist Salesforce developers and ISVs in releasing metadata to end users

# Installation

## Deploy to Heroku

Click the link below to deploy mrbelvedere to Heroku.  Use the "App Name (optional)" field to select an available name for your Heroku app.  Before submitting the form on Heroku, create a Connected App in your Salesforce org and get the Client ID and Client Secret to complete the Heroku form.

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## Salesforce Connected App

1. Log in to a persistent Salesforce org (e.g. your business org if you're an ISV, or your DE org if a developer)
2. Go to Setup -> Create -> Apps
3. Create a new Connected App
4. Use any values you'd like for app name, api name, and contact email
5. Click `Enable OAuth Settings` and use these settings:
    * Scopes: full, api, refresh_token
    * Callback URL: `https://<your-app-name>.herokuapp.com/mpinstaller/oauth/callback`
6. Use these values from the Connected App to complete the Heroku form:
    * Consumer Key -> MPINSTALLER_CLIENT_ID
    * Consumer Secret -> MPINSTALLER_CLIENT_SECRET
    * Callback URL -> MPINSTALLER_CALLBACK_URL

## Post deploy configuration

Clone the mrbelvedere repository and `cd` into it. Using the Heroku toolbelt, log in to your account using `heroku login` and then run the following command to create an admin user in the app's database:

    heroku run python manage.py createsuperuser --app <your-app-name>

# Configuring the mrbelvedere installer

## Accessing admin

Go to `https://<your-app-name>.herokuapp.com/admin` and log in using the user you created in Post deploy configuration

## Creating a Package

* Click `Add` next to Packages under the mpinstaller app
* Enter the package's namespace
    * If the package has a managed package namespace, use that namespace
    * If the package only contains unmanaged metadata, use whatever namespace you want
    * The namespace will become the installer url at `/mpinstaller/<namespace>`
    * AlphaNumeric, _, and -
* Enter a name for the package
* Enter content for the package
    * **Content Intro**: The content shown to users on the installer's main page before starting an installation
    * **Content Success**: The content shown to users after a successful installation
    * **Content Failure**: The content shown to users after a failure

## Creating Package Versions

### Manage Package Versions

* Click `Add` next to PackageVersions under the mpinstaller app
* Select the package
* Enter a name for the version (e.g. 1.1)
* Enter the version number in the Number field

### Github Versions

* Click `Add` next to PackageVersions under the mpinstaller app
* Select the package
* Enter a name for the version (e.g. Github - Unmanaged)
* Enter the repo_url in the repo_url field (e.g. https://github.com/SaleforceFoundation/mrbelvedere-df16-demo-project)
* Enter your Github username
* Enter your Github password or app token
* Enter the subdirectory of the repo where metadata is stored (e.g. src)
* Enter the name of the package configured in the `<fullName>` element of the package.xml (e.g. DF16 mrbelvedere demo project)

### Metadata Zip URL Version

* Click `Add` next to PackageVersions under the mpinstaller app
* Select the package
* Enter a name for the version
* Enter a zip file url

## Creating Package Version Dependencies

# Using the Installer

Go to `/mpinstaller/<namespace>`

# Analyzing and Supporting Installations

# Configuring the Contributor Tool

Set the SOCIAL_AUTH_GITHUB_KEY and SOCIAL_AUTH_GITHUB_SECRET environment variables on the Heroku app to enable Github OAuth necessary for the Contributor tool.  The values should come from a Github OAuth Application you create for the app with a callback of `https://<yourappname>.herokuapp.com/`

Any package that has a Current - Github version configured is made available for contributions through the Contributor Tool

# Using the Contributor Tool

Go to `/contributor`
