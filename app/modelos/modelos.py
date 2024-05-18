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
    last_sync = db.Column(db.String(255))
    expiration_token = db.Column(db.DateTime)
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)
    
class StravaActivity(db.Model):
    __tablename__ = 'strava_activity'

    id = db.Column(db.String(255), primary_key=True)
    athlete_id = db.Column(db.String(500))
    activity_name = db.Column(db.String(255))
    activity_description = db.Column(db.String(500))
    activity_type = db.Column(db.String(255))
    activity_distance = db.Column(db.Float)
    activity_trainer = db.Column(db.Integer)
    activity_commute = db.Column(db.Integer)
    start_date_local = db.Column(db.String(255))
    elapsed_time = db.Column(db.Integer)
    sync = db.Column(db.Integer)
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)

class SportUser(db.Model):
    __tablename__ = 'sport_user'

    id = db.Column(db.String(255), primary_key=True)
    gender = db.Column(db.String(255))
    age = db.Column(db.String(512))
    weight = db.Column(db.String(255))
    height = db.Column(db.String(255))
    birth_country = db.Column(db.String(512))
    birth_city = db.Column(db.String(500))
    residence_country = db.Column(db.String(500))
    residence_city = db.Column(db.String(500))
    residence_seniority = db.Column(db.Integer)
    sports = db.Column(db.String(500))
    acceptance_notify = db.Column(db.Integer)
    acceptance_tyc = db.Column(db.Integer)
    acceptance_personal_data = db.Column(db.Integer)
    typePlan =  db.Column(db.String(500))
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)

class SportProfile(db.Model):
    __tablename__ = 'sport_profile'

    id = db.Column(db.String(255), primary_key=True)
    sh_caminar = db.Column(db.Integer)
    sh_trotar = db.Column(db.Integer)
    sh_correr = db.Column(db.Integer)
    sh_nadar = db.Column(db.Integer)
    sh_bicicleta = db.Column(db.Integer)
    pp_fractura = db.Column(db.Integer)
    pp_esguinse = db.Column(db.Integer)
    pp_lumbalgia = db.Column(db.Integer)
    pp_articulacion = db.Column(db.Integer)
    pp_migranias = db.Column(db.Integer)
    i_vo2max = db.Column(db.Float)
    i_ftp = db.Column(db.Float)
    i_total_practice_time = db.Column(db.Integer)
    i_total_objective_achived =  db.Column(db.Integer)
    h_total_calories = db.Column(db.Integer)
    h_avg_bpm =  db.Column(db.Float)
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

class StravaActivitySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = StravaActivity
        include_relationships = True
        load_instance = True

class SportUserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = SportUser
        include_relationships = True
        load_instance = True

class SportProfileSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = SportProfile
        include_relationships = True
        load_instance = True