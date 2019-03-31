import os
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250))
    email = Column(String(250))


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250))


class Item(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    name = Column(String(250))
    description = Column(String(250))
    owner_id = Column(Integer, ForeignKey('user.id'))
    category_id = Column(Integer, ForeignKey('category.id'))
    user = relationship(User)
    category = relationship(Category)


DEV = os.environ.get("DEV", False)
if DEV:
    engine = create_engine(
        f"postgresql://postgres@localhost:5432/outdoor-catalogue")
else:
    DB_PASSWORD = os.environ.get("DB_PASSWORD")
    engine = create_engine(
        f"postgresql://postgres:{DB_PASSWORD}@outdoor-catalogue-postgresql.default.svc.cluster.local:5432/outdoor-catalogue"
    )

Base.metadata.create_all(engine)
