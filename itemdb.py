import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item

DB_PASSWORD = os.environ.get("DB_PASSWORD")
engine = create_engine(
    f"postgresql://postgres:{DB_PASSWORD}@outdoor-catalogue-postgresql.default.svc.cluster.local:5432/outdoor-catalogue"
)

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def createNewUser(login_session):
    # Checks if the user already exists in db, if not creates a new user
    userId = getUseridByEmail(login_session['email'])
    if userId:
        return userId
    newUser = User(
        name=login_session['username'], email=login_session['email'])
    session.add(newUser)
    session.commit()
    return newUser.id


def getUseridByEmail(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return False


def getAllCategories():
    categories = session.query(Category).order_by(Category.name).all()
    session.close()
    return categories


def getCategoryByID(categoryId):
    category = session.query(Category).filter_by(id=categoryId).one()
    session.close()
    return category


def getItemCountInCategory(categoryId):
    categoryCount = session.query(Item).filter_by(
        category_id=categoryId).count()
    return categoryCount


def getAllItems():
    items = session.query(Item).order_by(Item.name).all()
    session.close()
    return items


def getItemByID(itemId):
    item = session.query(Item).filter_by(id=itemId).one()
    session.close()
    return item


def getItemsByCategory(categoryId):
    items = session.query(Item).filter_by(category_id=categoryId).order_by(
        Item.name).all()
    session.close()
    return items


def addItem(item):
    newItem = Item(
        name=item['name'],
        description=item['description'],
        category_id=item['category_id'],
        owner_id=item['owner_id'])
    session.add(newItem)
    session.commit()
    return newItem


def editItemById(itemId, newItem):
    item = session.query(Item).filter_by(id=itemId).one()
    item.name = newItem['name']
    item.description = newItem['description']
    item.category_id = newItem['category_id']
    session.add(item)
    session.commit()
    return item


def deleteItemById(itemId):
    session.query(Item).filter_by(id=itemId).delete()
    session.commit()
    return True
