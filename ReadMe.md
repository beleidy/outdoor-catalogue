# Outdoor Catalogue

Outdoor catalogue lets users catalogue their outdoor-activity items. Users must sign in using their Google accounts in order to add or edit items. 

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

* Python 3
* Pipenv
* PostgreSQL running locally on port 5432

### Installing

Clone the repo and install dependencies
```
git clone https://gitlab.com/beleidy/outdoor-catalogue.git
cd outdoor-catalogue
Pipenv install

```
Setup the database and fill it with demo items

```
python item_populator.py
```

[Create and download your Google OAuth2.0 client secret json file](https://developers.google.com/identity/protocols/OAuth2WebServer#creatingcred) and store it as `client_secret.json`

Next, run the webserver. We assign 1 to the enviornment variable `DEV` so that the server knows to connect to a local database.
```
DEV=1 python webserver.py
```

Point your browser at `http://localhost:5000` and you can start using the app

## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* [Pipenv](https://pipenv.readthedocs.io/en/latest/) -- dependency management
* [Falsk](http://flask.pocoo.org/) -- webserver framework
* [OAuth2.0 via Google](https://developers.google.com/identity/protocols/OAuth2) -- authentication
* [PostgreSQL](https://www.postgresql.org/)


## Authors

* **Amr Elbeleidy** - *Initial work*
