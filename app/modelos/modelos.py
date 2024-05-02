from datetime import datetime
from decimal import Decimal as D 

from flask_sqlalchemy import SQLAlchemy
from marshmallow import fields, Schema
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import sqlalchemy.types as types
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.String(255), primary_key=True)
    email = db.Column(db.String(255))
    password = db.Column(db.String(512))
    doc_num = db.Column(db.String(255))
    doc_type = db.Column(db.String(10))
    name = db.Column(db.String(100))
    phone = db.Column(db.String(500))
    user_type = db.Column(db.Integer)
    token = db.Column(db.String(500))
    expiration_token = db.Column(db.DateTime)
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)

class StravaUser(db.Model):
    __tablename__ = 'strava_user'

    id = db.Column(db.String(255), primary_key=True)
    user_id = db.Column(db.String(255))
    athlete_id = db.Column(db.String(255))
    code = db.Column(db.String(255))
    scope = db.Column(db.String(255))
    access_token = db.Column(db.String(255))
    refresh_token = db.Column(db.String(255))
    timestamp = db.Column(db.Integer)
    expiration_token = db.Column(db.DateTime)
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)
    

class UserSessionSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        include_relationships = True
        load_instance = True

class StravaUserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = StravaUser
        include_relationships = True
        load_instance = True