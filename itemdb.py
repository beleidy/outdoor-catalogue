import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item

DEV = os.environ.get("DEV", False)
if DEV:
    engine = create_engine(
        f"postgresql://postgres@localhost:5432/outdoor-catalogue")
else:
    DB_PASSWORD = os.environ.get("DB_PASSWORD")
    engine = create_engine(
        f"postgresql://postgres:{DB_PASSWORD}@outdoor-catalogue-postgresql.default.svc.cluster.local:5432/outdoor-catalogue"
    )

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def create_new_user(login_session):
    # Checks if the user already exists in db, if not creates a new user
    userId = get_userid_by_email(login_session['email'])
    if userId:
        return userId
    newUser = User(
        name=login_session['username'], email=login_session['email'])
    session.add(newUser)
    session.commit()
    return newUser.id


def get_userid_by_email(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return False


def get_all_categories():
    categories = session.query(Category).order_by(Category.name).all()
    session.close()
    return categories


def get_category_by_ID(categoryId):
    category = session.query(Category).filter_by(id=categoryId).one()
    session.close()
    return category


def get_item_count_in_category(categoryId):
    categoryCount = session.query(Item).filter_by(
        category_id=categoryId).count()
    return categoryCount


def get_all_items():
    items = session.query(Item).order_by(Item.name).all()
    session.close()
    return items


def get_item_by_ID(itemId):
    item = session.query(Item).filter_by(id=itemId).one()
    session.close()
    return item


def get_items_by_category(categoryId):
    items = session.query(Item).filter_by(category_id=categoryId).order_by(
        Item.name).all()
    session.close()
    return items


def get_items_by_user_ID(user_ID):
    items = session.query(Item).filter_by(owner_id=user_ID).order_by(
        Item.name).all()
    session.close()
    return items


def add_item(item):
    newItem = Item(
        name=item['name'],
        description=item['description'],
        category_id=item['category_id'],
        owner_id=item['owner_id'])
    session.add(newItem)
    session.commit()
    return newItem


def edit_item_by_ID(itemId, newItem):
    item = session.query(Item).filter_by(id=itemId).one()
    item.name = newItem['name']
    item.description = newItem['description']
    item.category_id = newItem['category_id']
    session.add(item)
    session.commit()
    return item


def delete_item_by_ID(itemId):
    session.query(Item).filter_by(id=itemId).delete()
    session.commit()
    return True
