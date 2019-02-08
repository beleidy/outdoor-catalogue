import hashlib
import json
import jwt
from jwt.algorithms import RSAAlgorithm
import os

import requests
from flask import (Flask, jsonify, make_response, redirect, render_template,
                   request)
from flask import session as login_session
from flask import url_for

import google.oauth2.credentials
import google_auth_oauthlib.flow
from itemdb import *

application = Flask(__name__)

# Defaults application secret in case not specified in enviornment
application.secret_key = os.environ.get('FLASK_SECRET_KEY',
                                        "REPLACE THIS VERY SECRET KEY")

# Sets client secret from file if developing locally
# otherwise from enviornment
DEV = os.environ["DEV"]
if DEV:
    with open("client_secret.json", "r") as file:
        CLIENT_SECRET = json.loads(file.read())
else:
    CLIENT_SECRET = json.loads(os.environ.get('CLIENT_SECRET'))

SCOPES = [
    'openid', 'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

JWKS_KEYS = False


# Routes for authentication
@application.route('/login')
def login():
    state = hashlib.sha256(os.urandom(1024)).hexdigest()
    login_session['state'] = state

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        CLIENT_SECRET, scopes=SCOPES)

    flow.redirect_uri = url_for('oauth2_callback', _external=True)

    authorization_url, _ = flow.authorization_url(state=state)

    return redirect(authorization_url)


@application.route('/oauth2_callback')
def oauth2_callback():
    state = login_session['state']

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
    jwt_id_token = credentials.id_token
    print(jwt.decode(jwt_id_token, verify=False))
    jwt_headers = jwt.get_unverified_header(jwt_id_token)
    print(jwt_headers)
    jwt_alg = jwt_headers['alg']
    print(jwt_alg)
    jwt_kid = jwt_headers['kid']

    # if not JWKS_KEYS:
    JWKS_KEYS = get_jwks_keys()
    jwt_key = [key for key in JWKS_KEYS if key['kid'] == jwt_kid][0]

    public_key = RSAAlgorithm.from_jwk(json.dumps(jwt_key))

    audience = CLIENT_SECRET['web']['client_id']

    jwt_payload = jwt.decode(
        jwt_id_token, public_key, algorithms=[jwt_alg], audience=audience)
    print(jwt_payload)

    # Get user info
    # userinfo_url = "https://www.googleapis.com/auth/userinfo.profile"
    # params = {'access_token': credentials.access_token, 'alt': 'json'}
    # answer = requests.get(userinfo_url, params=params)
    # userInfo = answer.json()

    # # Get profile info from ID token
    # email = credentials.id_token['email']
    # name = userInfo['name']

    # # Store the information in the login_session
    # login_session['email'] = email
    # login_session['logged_in'] = True
    # login_session['username'] = name
    # login_session['access_token'] = credentials.access_token
    # login_session['db_user_id'] = createNewUser(login_session)

    # Send back a welcome message
    # this will be handled by the AJAX script on the client side
    output = "Welcome\nYou are now signed in and will be" \
        "redirected to our main page shortly :)"

    return output


@application.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token', None)

    if access_token is None:
        return render_template(
            'error.html', ERROR_MESSAGE="You are already signed out")

    url = 'https://accounts.google.com/o/oauth2/revoke?' \
        'token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    if result['status'] == '200':
        del login_session['logged_in']
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        return render_template(
            'error.html', ERROR_MESSAGE="You have signed out")
    else:
        return render_template(
            'error.html', ERROR_MESSAGE="You are already signed out")


# The routes for the website
@application.route('/')
def MainView():
    # Get the data we need from the db
    categories = getAllCategories()
    categoryCount = len(categories)
    items = getAllItems()
    itemCount = len(items)

    # Generate a list of how many items are in each category
    countList = []
    for cat in categories:
        countList.append(getItemCountInCategory(cat.id))

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
def CategoryView(categoryId):
    # Get the data we need from the db
    categories = getAllCategories()
    categoryCount = len(categories)
    activeCategory = getCategoryByID(categoryId)
    items = getItemsByCategory(categoryId)
    itemCount = len(items)

    # Generate a list of how many items are in each category
    countList = []
    for cat in categories:
        countList.append(getItemCountInCategory(cat.id))

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
def ItemView(itemId):
    activeItem = getItemByID(itemId)
    category = getCategoryByID(activeItem.category_id)
    items = getItemsByCategory(activeItem.category_id)

    return render_template(
        'item_view.html',
        activeItem=activeItem,
        category=category,
        items=items,
        login_session=login_session)


@application.route('/items/addItem', methods=['GET', 'POST'])
def AddItemView():
    if not login_session.get('logged_in', False):
        return render_template(
            'error.html',
            ERROR_MESSAGE="You can only add an item if you are logged in")
    if request.method == 'GET':
        # Check that the user is logged in
        categories = getAllCategories()
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
        addedItem = addItem(item)
        return ItemView(addedItem.id)


@application.route('/items/<int:itemId>/edit', methods=['GET', 'POST'])
def EditItemView(itemId):
    if not login_session.get('logged_in', False):
        return render_template(
            'error.html',
            ERROR_MESSAGE="You can only edit an item if you are logged in")
    item = getItemByID(itemId)
    if item.owner_id != login_session['db_user_id']:
        return render_template(
            'error.html',
            ERROR_MESSAGE="You can only edit an item"
            "that you added with your account")
    if request.method == 'GET':
        categories = getAllCategories()
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
        editedItem = editItemById(itemId, newItem)
        return ItemView(editedItem.id)


@application.route('/items/<int:itemId>/delete', methods=['GET', 'POST'])
def DeleteItemView(itemId):
    if not login_session.get('logged_in', False):
        return render_template(
            'error.html',
            ERROR_MESSAGE="You can only delete an item if you are logged in")
    item = getItemByID(itemId)
    if item.owner_id != login_session['db_user_id']:
        return render_template(
            'error.html',
            ERROR_MESSAGE="You can only delete an item "
            "that you added with your account")

    if request.method == 'GET':
        return render_template(
            'delete_item.html', item=item, login_session=login_session)
    if request.method == 'POST':
        categoryId = getItemByID(itemId).category_id
        if deleteItemById(itemId):
            return CategoryView(categoryId)


# Route for API
@application.route('/api/v0.1/items/<int:itemId>')
def ViewItemDetails(itemId):
    item = getItemByID(itemId)
    category = getCategoryByID(item.category_id)
    response = {}
    response['name'] = item.name
    response['description'] = item.description
    response['category'] = category.name
    return jsonify(response)


def get_jwks_keys():
    GOOGLE_DISCOVERY_URI = "https://accounts.google.com/.well-known/openid-configuration"
    response = requests.get(GOOGLE_DISCOVERY_URI)
    response_json = response.json()
    jwks_uri = response_json.get("jwks_uri", None)
    if jwks_uri is not None:
        response = requests.get(jwks_uri)
        response_json = response.json()
    keys = response_json.get("keys", None)
    return keys


if __name__ == '__main__':
    application.debug = True
    application.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
