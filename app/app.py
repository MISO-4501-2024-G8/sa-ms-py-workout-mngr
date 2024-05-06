import logging
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_restful import Api
from modelos.modelos import db
from vistas import (
    VistaStatusCheck, 
    VistaStravaLogin, 
    VistaStravaCallback, 
    VistaStravaCallbackLocal, 
    VistaRefreshToken,
    VistaStravaAtlhlete,
    VistaStravaActivities,
    VistaStravaActivityDetail,
    VistaActiveUser,
    VistaSyncActivities
)
import uuid

from decouple import config

app=Flask(__name__) # NOSONAR

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def generate_uuid():
    uid = uuid.uuid4()
    parts = str(uid).split('-')
    return parts[0]

logging.debug('Debug message')

DATABASE_URI = config('DATABASE_URL', default=f'sqlite:///workout_{generate_uuid()}.db')
#DATABASE_URI = config('DATABASE_URL', default=f'sqlite:///workout.db')
print(' * DATABASE_URI:', DATABASE_URI)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PROPAGATE_EXCEPTIONS'] = True

app_context = app.app_context()
app_context.push()
db.init_app(app)
db.create_all()
cors = CORS(app) # NOSONAR
api = Api(app)


api.add_resource(VistaStatusCheck, '/')
api.add_resource(VistaStravaLogin, '/strava_login')
api.add_resource(VistaStravaCallback, '/auth_callback/<string:id>')
api.add_resource(VistaStravaCallbackLocal, '/auth_callback_local/<string:id>')
api.add_resource(VistaRefreshToken, '/refresh_token')
api.add_resource(VistaStravaAtlhlete, '/strava_athlete')
api.add_resource(VistaActiveUser, '/active_user')
api.add_resource(VistaStravaActivities, '/strava_activities')
api.add_resource(VistaStravaActivityDetail, '/strava_activity')
api.add_resource(VistaSyncActivities, '/sync_activities')


jwt = JWTManager(app)


print(' * WORKOUT MNGR corriendo ----------------')

if __name__=='__main__': 
    app.run(port=5001, debug=True) # NOSONAR