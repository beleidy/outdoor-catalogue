import os
import random
import string
import httplib2
import json
import requests
from oauth2client import client
from itemdb import *
from flask import session as login_session
from flask import (Flask, request, redirect, url_for, render_template,
                   make_response, jsonify)

app = Flask(__name__)

# MAKE SURE YOU CHANGE THE SECRET KEY BEFORE DEPLOYMENT
app.secret_key = os.environ.get('SECRET_KEY')

GOOGLE_SECRET = os.environ.get("GOOGLE_SECRET")
CLIENT_ID = GOOGLE_SECRET['web']['client_id']


# Routes for authentication
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, CLIENT_ID=CLIENT_ID)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate the state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid State Parameter', 401))
        response.headers['Content-Type'] = 'application/json'
        return response

    # Protect against CSRF attacks
    if not request.headers.get('X-Requested-With'):
        response = make_response(json.dumps('No X-Requested-With header', 403))
        response.headers['Content-Type'] = 'application/json'
        return response

    code = bytes.decode(request.data)

    # Exchange auth code for access token, refresh token, and ID token
    credentials = client.credentials_from_clientsecrets_and_code(
        'client_secret.json',
        ['https://www.googleapis.com/auth/drive.appdata', 'profile', 'email'],
        code)

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    userInfo = answer.json()

    # Get profile info from ID token
    email = credentials.id_token['email']
    name = userInfo['name']

    # Store the information in the login_session
    login_session['email'] = email
    login_session['logged_in'] = True
    login_session['username'] = name
    login_session['access_token'] = credentials.access_token
    login_session['db_user_id'] = createNewUser(login_session)

    # Send back a welcome message
    # this will be handled by the AJAX script on the client side
    output = "Welcome " + name + "\nYou are now signed in and will be" \
        "redirected to our main page shortly :)"

    return output


@app.route('/gdisconnect')
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
@app.route('/')
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

    return render_template('main_view.html',
                           cats=categories,
                           catCount=categoryCount,
                           countList=countList,
                           items=items,
                           itemCount=itemCount,
                           login_session=login_session,
                           )


@app.route('/categories/<int:categoryId>')
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

    return render_template('main_view.html',
                           activeCategory=activeCategory,
                           cats=categories,
                           catCount=categoryCount,
                           countList=countList,
                           items=items,
                           itemCount=itemCount,
                           login_session=login_session)


@app.route('/items/<int:itemId>')
def ItemView(itemId):
    activeItem = getItemByID(itemId)
    category = getCategoryByID(activeItem.category_id)
    items = getItemsByCategory(activeItem.category_id)

    return render_template('item_view.html',
                           activeItem=activeItem,
                           category=category,
                           items=items,
                           login_session=login_session)


@app.route('/items/addItem', methods=['GET', 'POST'])
def AddItemView():
    if not login_session.get('logged_in', False):
        return render_template(
            'error.html',
            ERROR_MESSAGE="You can only add an item if you are logged in")
    if request.method == 'GET':
        # Check that the user is logged in
        categories = getAllCategories()
        return render_template(
            'add_item.html', categories=categories,
            login_session=login_session)

    if request.method == 'POST':
        item = {}
        item['name'] = request.form.get('item_name')
        item['description'] = request.form.get('item_description')
        item['category_id'] = request.form.get('item_category')
        item['owner_id'] = login_session['db_user_id']
        addedItem = addItem(item)
        return ItemView(addedItem.id)


@app.route('/items/<int:itemId>/edit', methods=['GET', 'POST'])
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
            'edit_item.html', categories=categories,
            item=item, login_session=login_session)

    if request.method == 'POST':
        newItem = {}
        newItem['name'] = request.form.get('item_name')
        newItem['description'] = request.form.get('item_description')
        newItem['category_id'] = request.form.get('item_category')
        editedItem = editItemById(itemId, newItem)
        return ItemView(editedItem.id)


@app.route('/items/<int:itemId>/delete', methods=['GET', 'POST'])
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
@app.route('/api/v0.1/items/<int:itemId>')
def ViewItemDetails(itemId):
    item = getItemByID(itemId)
    category = getCategoryByID(item.category_id)
    response = {}
    response['name'] = item.name
    response['description'] = item.description
    response['category'] = category.name
    return jsonify(response)


if __name__ == '__main__':
    app.debug = False
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
