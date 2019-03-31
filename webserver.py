import hashlib
import json
import jwt
from jwt.algorithms import RSAAlgorithm
import os

from flask import (Flask, jsonify, make_response, redirect, render_template,
                   request)
from flask import session as login_session
from flask import url_for

import google_auth_oauthlib.flow
from itemdb import (create_new_user, add_item, get_all_categories,
                    get_all_items, get_category_by_ID, get_item_by_ID,
                    get_item_count_in_category, get_items_by_category,
                    delete_item_by_ID, edit_item_by_ID)
from web_helpers import get_jwks_keys
import requests

application = Flask(__name__)

# Defaults application secret in case not specified in enviornment
application.secret_key = os.environ.get('FLASK_SECRET_KEY',
                                        "REPLACE THIS VERY SECRET KEY")

# Sets client secret from file if developing locally
# otherwise from enviornment
DEV = os.environ.get("DEV", False)
if DEV:
    with open("client_secret.json", "r") as file:
        CLIENT_SECRET = json.loads(file.read())
else:
    CLIENT_SECRET = json.loads(os.environ.get('CLIENT_SECRET'))

SCOPES = [
    'openid', 'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

JWKS_KEYS = get_jwks_keys()


# Routes for authentication
@application.route('/login')
def login():
    state = get_session_state()

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        CLIENT_SECRET, scopes=SCOPES)

    flow.redirect_uri = url_for('oauth2_callback', _external=True)
    authorization_url, _ = flow.authorization_url(state=state)

    return redirect(authorization_url)


@application.route('/oauth2_callback')
def oauth2_callback():
    state = get_session_state()

    # Validate state token
    if request.args.get('state') != state:
        response = make_response(json.dumps('Invalid State Parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        CLIENT_SECRET, scopes=SCOPES)

    flow.redirect_uri = url_for('oauth2_callback', _external=True)

    authorization_response = request.url
    # Replace with https to avoid InsecureTrasnportError
    authorization_response = authorization_response.replace('http', 'https')

    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials

    # Verify token comes from Google
    global JWKS_KEYS
    jwt_id_token = credentials.id_token
    jwt_headers = jwt.get_unverified_header(jwt_id_token)
    jwt_alg = jwt_headers['alg']
    jwt_kid = jwt_headers['kid']

    jwt_key = [key for key in JWKS_KEYS if key['kid'] == jwt_kid][0]
    if not jwt_key:
        JWKS_KEYS = get_jwks_keys()
        jwt_key = [key for key in JWKS_KEYS if key['kid'] == jwt_kid][0]

    public_key = RSAAlgorithm.from_jwk(json.dumps(jwt_key))
    audience = CLIENT_SECRET['web']['client_id']
    jwt_payload = jwt.decode(
        jwt_id_token, public_key, algorithms=[jwt_alg], audience=audience)
    print(jwt_payload)

    login_session['logged_in'] = True
    login_session['username'] = jwt_payload['given_name']
    login_session['email'] = jwt_payload['email']
    login_session['credentials_token'] = credentials.token
    login_session['db_user_id'] = create_new_user(login_session)

    return redirect(url_for('main_view'))


@application.route('/logout')
def logout():
    credentials_token = login_session.get('credentials_token', None)

    if credentials_token is None:
        login_session.pop('logged_in', None)
        login_session.pop('username', None)
        login_session.pop('email', None)
        return render_template(
            'error.html', ERROR_MESSAGE="You are already signed out")

    r = requests.post(
        'https://accounts.google.com/o/oauth2/revoke',
        params={'token': credentials_token},
        headers={'content-type': 'application/x-www-form-urlencoded'})

    if r.status_code == requests.codes.ok:
        login_session.pop('logged_in', None)
        login_session.pop('username', None)
        login_session.pop('email', None)
        login_session.pop('credentials_token', None)
        return render_template(
            'error.html', ERROR_MESSAGE="You have signed out")
    else:
        return render_template(
            'error.html', ERROR_MESSAGE="You are already signed out")


# The routes for the website
@application.route('/')
def main_view():
    # Set a state for the login session
    get_session_state()

    # Get the data we need from the db
    categories = get_all_categories()
    categoryCount = len(categories)
    items = get_all_items()
    itemCount = len(items)

    # Generate a list of how many items are in each category
    countList = []
    for cat in categories:
        countList.append(get_item_count_in_category(cat.id))

    return render_template(
        'main_view.html',
        cats=categories,
        catCount=categoryCount,
        countList=countList,
        items=items,
        itemCount=itemCount,
        login_session=login_session,
    )


@application.route('/categories/<int:categoryId>')
def category_view(categoryId):
    # Get the data we need from the db
    categories = get_all_categories()
    categoryCount = len(categories)
    activeCategory = get_category_by_ID(categoryId)
    items = get_items_by_category(categoryId)
    itemCount = len(items)

    # Generate a list of how many items are in each category
    countList = []
    for cat in categories:
        countList.append(get_item_count_in_category(cat.id))

    return render_template(
        'main_view.html',
        activeCategory=activeCategory,
        cats=categories,
        catCount=categoryCount,
        countList=countList,
        items=items,
        itemCount=itemCount,
        login_session=login_session)


@application.route('/items/<int:itemId>')
def item_view(itemId):
    activeItem = get_item_by_ID(itemId)
    category = get_category_by_ID(activeItem.category_id)
    items = get_items_by_category(activeItem.category_id)

    return render_template(
        'item_view.html',
        activeItem=activeItem,
        category=category,
        items=items,
        login_session=login_session)


@application.route('/items/addItem', methods=['GET', 'POST'])
def add_item_view():
    if not login_session.get('logged_in', False):
        return render_template(
            'error.html',
            ERROR_MESSAGE="You can only add an item if you are logged in")
    if request.method == 'GET':
        # Check that the user is logged in
        categories = get_all_categories()
        return render_template(
            'add_item.html',
            categories=categories,
            login_session=login_session)

    if request.method == 'POST':
        item = {}
        item['name'] = request.form.get('item_name')
        item['description'] = request.form.get('item_description')
        item['category_id'] = request.form.get('item_category')
        item['owner_id'] = login_session['db_user_id']
        addedItem = add_item(item)
        return item_view(addedItem.id)


@application.route('/items/<int:itemId>/edit', methods=['GET', 'POST'])
def edit_item_view(itemId):
    if not login_session.get('logged_in', False):
        return render_template(
            'error.html',
            ERROR_MESSAGE="You can only edit an item if you are logged in")
    item = get_item_by_ID(itemId)
    if item.owner_id != login_session['db_user_id']:
        return render_template(
            'error.html',
            ERROR_MESSAGE="You can only edit an item"
            "that you added with your account")
    if request.method == 'GET':
        categories = get_all_categories()
        return render_template(
            'edit_item.html',
            categories=categories,
            item=item,
            login_session=login_session)

    if request.method == 'POST':
        newItem = {}
        newItem['name'] = request.form.get('item_name')
        newItem['description'] = request.form.get('item_description')
        newItem['category_id'] = request.form.get('item_category')
        editedItem = edit_item_by_ID(itemId, newItem)
        return item_view(editedItem.id)


@application.route('/items/<int:itemId>/delete', methods=['GET', 'POST'])
def delete_item_view(itemId):
    if not login_session.get('logged_in', False):
        return render_template(
            'error.html',
            ERROR_MESSAGE="You can only delete an item if you are logged in")
    item = get_item_by_ID(itemId)
    if item.owner_id != login_session['db_user_id']:
        return render_template(
            'error.html',
            ERROR_MESSAGE="You can only delete an item "
            "that you added with your account")

    if request.method == 'GET':
        return render_template(
            'delete_item.html', item=item, login_session=login_session)
    if request.method == 'POST':
        categoryId = get_item_by_ID(itemId).category_id
        if delete_item_by_ID(itemId):
            return category_view(categoryId)


# Route for API
@application.route('/api/v0.1/items/<int:itemId>')
def view_item_details(itemId):
    item = get_item_by_ID(itemId)
    category = get_category_by_ID(item.category_id)
    response = {}
    response['name'] = item.name
    response['description'] = item.description
    response['category'] = category.name
    return jsonify(response)


def get_session_state():
    if login_session.get('state', False):
        state = login_session['state']
    else:
        state = hashlib.sha256(os.urandom(1024)).hexdigest()
        login_session['state'] = state

    return state


if __name__ == '__main__':
    application.debug = True
    application.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
