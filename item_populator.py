from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item

engine = create_engine('sqlite:///itemcatalogue.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Add Categories
category_array = ["Cycling", "Camping", "Hiking", "Running"]
for category in category_array:
    cat = Category(name=category)
    session.add(cat)
    session.commit()

# Add items
cycling_array = [
    ("Road Bike", "A bike that you can use on the road"),
    ("Mountain Bike", "A bike that you can use in the mounatins"),
    ("Hybrid Bike", "A bike that you can use anywhere"),
    ("Panniers", "Bags that hang off your bike"),
    ("Tool Kit", "A set of tools to fix your bike when things go wrong"),
    ]
camping_array = [
    ("Tent", "Your home away from home"),
    ("Sleeping Bag", "Slide into this bag, and sleep warmly"),
    ("Insulation Mat",
     "A mat to go under your sleeping bag"
     " to insulate you from the cold ground"),
    ("Torch", "Let there be light!"),
    ]
hiking_array = [
    ("Hard Shell", "Protects you from water and wind"),
    ("Soft Shell", "A warm jacket that's neither waterproof, nor windproof"),
    ("Baselayer", "The layer touching your skin"),
    ("Boots",
     "Insert your feet into these for a more comfortable hike"),
    ("Walking Poles",
     "Walking sticks, but not just for the elderly and infirm"),
    ("Insulating Jacket",
     "Down down down... this jacket will keep you warm, "
     "but totally non-breathable"),
    ]
running_array = [
    ("Running Shoes",
     "Shoes that make your run easier on your feet and knees"),
    ("Socks", "Pieces of cloth that sit between your feet and shoes"),
    ("Running Shorts",
     "No, these shorts don't run away from you, "
     "but will make you run more with more comfort"),
    ("Running Top",
     "Because there is only so much tanning you can do "
     "before the burning kicks in"),
    ]

for item in cycling_array:
    i = Item(name=item[0], description=item[1], category_id=1)
    session.add(i)
    session.commit()

for item in camping_array:
    i = Item(name=item[0], description=item[1], category_id=2)
    session.add(i)
    session.commit()

for item in hiking_array:
    i = Item(name=item[0], description=item[1], category_id=3)
    session.add(i)
    session.commit()

for item in running_array:
    i = Item(name=item[0], description=item[1], category_id=4)
    session.add(i)
    session.commit()
