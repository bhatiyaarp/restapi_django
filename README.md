# Rest API 

An API is an application programming interface. It is a set of rules that allow programs to talk to each other. The developer creates the API on the server and allows the client to talk to it.

REST determines how the API looks like. It stands for “Representational State Transfer”. It is a set of rules that developers follow when they create their API. One of these rules states that you should be able to get a piece of data (called a resource) when you link to a specific URL.

Each URL is called a request while the data sent back to you is called a response.

A REST API works in a way where you search for something, and you get a list of results back from the service you’re requesting from.

# Working with Django Framework

To Create a API we need to first create a project then we need to add apps which contains the end point, we also need to work with django server

## Create Project
For creating a project you’ll have to take care of some initial setup. Namely, you’ll need to auto-generate some code that establishes a Django project – a collection of settings for an instance of Django, including database configuration, Django-specific options and application-specific settings.

From the command line, cd into a directory where you’d like to store your code, then run the following 

    command:  django-admin startproject rest

Let’s look at what startproject created:


     rest/
        manage.py
        rest/
            __init__.py
            settings.py
            urls.py
            asgi.py
            wsgi.py


These files are:

The outer mysite/ root directory is a container for your project. Its name doesn’t matter to Django; you can rename it to anything you like.

manage.py: A command-line utility that lets you interact with this Django project in various ways. You can read all the details about manage.py in django-admin and manage.py.
The inner mysite/ directory is the actual Python package for your project. Its name is the Python package name you’ll need to use to import anything inside it (e.g. rest.urls).

rest/__init__.py: An empty file that tells Python that this directory should be considered a Python package. If you’re a Python beginner, read more about packages in the official Python docs.

rest/settings.py: Settings/configuration for this Django project. Django settings will tell you all about how settings work.

rest/urls.py: The URL declarations for this Django project; a “table of contents” of your Django-powered site. You can read more about URLs in URL dispatcher.

rest/asgi.py: An entry-point for ASGI-compatible web servers to serve your project. See How to deploy with ASGI for more details.

rest/wsgi.py: An entry-point for WSGI-compatible web servers to serve your project. See How to deploy with WSGI for more details.


## Work with with django webserver

    command: python3 manage.py runserver
 
You’ll see the following output on the command line:

    Performing system checks...
    System check identified no issues (0 silenced).
    You have unapplied migrations; your app may not work properly until they are applied.
    Run 'python manage.py migrate' to apply them.
    Django version 3.1, using settings 'mysite.settings'
    Starting development server at http://127.0.0.1:8000/
    Quit the server with CONTROL-C.

## Creating Apps for our projeect
Creating the API app

Now that your environment – a “project” – is set up, you’re set to start doing work.
Each application you write in Django consists of a Python package that follows a certain convention. Django comes with a utility that automatically generates the basic directory structure of an app, so you can focus on writing code rather than creating directories.

    What’s the difference between a project and an app? An app is a Web application that does something – e.g., a Weblog system, a database of public records or a small poll app. A project is a collection of configuration and apps for a particular website. A project can contain multiple apps. An app can be in multiple projects.

Your apps can live anywhere on your Python path. In this tutorial, we’ll create our poll app in the same directory as your manage.py file so that it can be imported as its own top-level module, rather than a submodule of mysite.

To create your app, make sure you’re in the same directory as manage.py and type this command:


    command: python manage.py startapp api
That’ll create a directory polls, which is laid out like this:

    api/
        __init__.py
        admin.py
        apps.py
        migrations/
            __init__.py
        models.py
        tests.py
        views.py

# How to work with Rest API for comparing two images

From your root directory (166--/home/abhishekg/arpit/dj_rest/restvenv/)
    Run:
    
    Creating a project rest-->
    django-admin startproject rest
    
    Creating an app that contains files to build api
    python3 manage.py startapp api    
    
    
Root directory has following structure:
    
    rest/
      manage.py
      rest/
      api/
         __init__.py
        admin.py
        apps.py
        models.py
        tests.py
        views.py
        migrations/
      
      
Steps to follow

    1) Add bussiness logic to views.py---The endpoint calls are directed to specific functions/classes in the views of our app.
    2) In apps.py, we write the code to load our machine learning model, because here the model is loaded only once, and not every time the endpoint is called, thereby, reducing overhead.
    3) We need to create a URL and add it to the list urlpatterns in urls.py (both inside api directory and rest directory).

Final step is 

    Running our REST API!!!!!!!

Use the below command to run websever

    $ python manage.py runserver

Now open your browser and type the following URL- http://127.0.0.1:8000/
 


## Backend Development Basics

First fork the [DjangoGirls/tutorial](https://github.com/DjangoGirls/tutorial) repository to your personal GitHub account:

![Fork button](contributing/images/fork.png)

# Editing chapter content

## Simple changes

For simple changes like typo corrections you can use the GitHub online editor:

* Open your local fork page on GitHub,
* go to *README.md* file in any chapter,
* press the *Edit* icon (pen)

and you can edit the chapter directly on github.com.

![Edit button](contributing/images/edit.png)

Markdown syntax is used to edit the individual pages of the tutorial.

![GitHub editor](contributing/images/github_editor.png)

Save your changes and create a pull request as explained below.

## New content and complex changes

For adding new chapters, writing longer snippets of text or adding images, you need to get a copy of the tutorial to your local computer.

Either use the GitHub app for your operating system (mentioned above) or `git` command line to get the repository locally. You get the repository address from the front page of your own GitHub repository fork:

    git clone git@github.com:yourgithubusername/tutorial.git

Then, create a branch for your new changes to sit in. It helps to call the branch something related to the changes you are going to make.

    git checkout -b contributing

Download the [GitBook Editor](https://legacy.gitbook.com/editor) app to your computer.

Then you can open the tutorial in GitBook Editor (*File* > *Open book*).

Make any changes in the tutorial using GitBook and then save changes (*Book* > *Save all*).

Then commit the changes using `git` and push the changes to your remote GitHub repository.

Example:

    $ git status
    On branch contributing
    Untracked files:
      (use "git add <file>..." to include in what will be committed)

        contributing_and_editing_this_book/images/gitbook.png

    $ git add contributing_and_editing_this_book/images/gitbook.png

    $ git commit -m "Added gitbook editor screenshot"
    [contributing fe36152] Added gitbook screenshot
     1 file changed, 0 insertions(+), 0 deletions(-)
     create mode 100644 contributing_and_editing_this_book/images/gitbook.png

    $ git push
    Counting objects: 11, done.
    Delta compression using up to 8 threads.
    Compressing objects: 100% (5/5), done.
    Writing objects: 100% (5/5), 266.37 KiB | 0 bytes/s, done.
    Total 5 (delta 1), reused 0 (delta 0)
    To git@github.com:miohtama/tutorial.git
       b37ca59..fe36152  contributing -> contributing

If you don't want to download the GitBook Editor app you can also go to the [GitBook website](https://legacy.gitbook.com/), sign up for free and work directly in your browser.

C

# Further information and help

GitHub has an excellent [documentation](https://help.github.com/). Check it out if you need help!

For further questions please [contact DjangoGirls](https://djangogirls.org/).
