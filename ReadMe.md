# Udacity Full Stack Item Catalogue Project

This is a website that allows you to view, create, edit and delete items in an item catalogue. While you can browse the catalogue without authentication, you will need to be signed in with Google in order to create, edit or delete items.

You can only change details of items that you have created yourself.

## Libraries
This project is built using Flask and Python 3 for the webserver, sqlalchemy as ORM, and sqlite for database.

### Dependencies
You will need to have these installed for the site to work.

1. Python 3
2. Sqlite
3. Sqlalchemy
4. oauth2client
5. httplib2
6. requests
7. JSON

Alternatively you can use `pipenv install`

## Installation
This package comes with a pre-built sqlite database already populated with some items. The database is in `itemcatalgue.db`

To see how this database is structed see `database_setup.py` You will find the sqlalchemy classes that were used there

The database was populated using `item_populator.py` You can see what has been aded to the database there.

Run `webserver.py`. You are now ready to access the site at `localhost:5000//`

### Some changes have been made to deploy on heroku

In order for OAuth2 to work on your installation, you will need to setup an API secret with Google and have your own client secret file. 

You will then need to change where the server finds this information based on your setup. In my case, I am deploying on heroku and using its enviornment variables to keep these values secret. 

a heroku enviornment variable is also used for the flask app secret that protects your session.


### Setting up a clean database
If you would like to setup your own empty database:
    1. Delete the file `itemcatalogue.db`.
    2. Run `database_setup.py` - this will create an empty database for you.
    3. You can populate the database in different ways
        a. Edit `item_populator.py` and run it to create your own items.
        b. Write your own python script to populate the database
        c. Run the webserver `webserver.py`, navigate to `localhost:5000//` in your browser, sign in and use the add item functionality.

## The API
The site includes an API with a JSON endpoint at `localhost:5000//api/v0.1/items/<int:itemId>` where `<int:ItemId` is an integer that represents the id of the item you are querying. 

An example of a returned JSON is:

```
{
  "category": "Cycling",
  "description": "A bike that you can use anywhere",
  "name": "Hybrid Bike"
}
```
