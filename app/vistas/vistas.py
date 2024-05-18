from dataclasses import dataclass
from datetime import datetime
import requests
from flask import request, redirect
from flask_jwt_extended import create_access_token, jwt_required
from flask_restful import Resource
import logging

from modelos.modelos import (
    User,
    UserSessionSchema,
    StravaUser,
    SportProfile,
    StravaUserSchema,
    StravaActivity,
    StravaActivitySchema,
    SportProfileSchema,
    db,
)

from requests_toolbelt.multipart.encoder import MultipartEncoder
from pathlib import Path
from decouple import config
import json
import uuid

from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


user_schema = UserSessionSchema()
strava_user_schema = StravaUserSchema()
strava_activity_schema = StravaActivitySchema()
sport_profile_schema = SportProfileSchema()

client_id = '125884'
client_secret = 'a0f691d5d314ebf2042c2e8ab477c7fcbfc2f86c'
redirect_uri = 'http://localhost:5001/auth_callback'
authorization_base_url = 'https://www.strava.com/oauth/authorize'
token_url = 'https://www.strava.com/oauth/token'
athlete_url = 'https://www.strava.com/api/v3/athlete'
activities_url = 'https://www.strava.com/api/v3/athlete/activities'
activity_url = 'https://www.strava.com/api/v3/activities'

front_url = 'https://d1jiuccttec78g.cloudfront.net/#/strava'
front_url_local = 'http://localhost:4200/#/strava'


date_format = "%Y-%m-%d %H:%M:%S"
msg_error_user_not_registered = "Error usuario no registrado"
user_id_log = ' * user_id:'

def generate_uuid():
    uid = uuid.uuid4()
    parts = str(uid).split("-")
    return parts[0]

def callback_response(url):
    response  = dict()
    response["statusCode"] = 302
    response["headers"] = {
        "Location": url
    }
    return response, 302

class VistaStatusCheck(Resource):
    def get(self):
        return {"message": "OK", "code": 200}, 200


class VistaStravaLogin(Resource):
    def get(self):
        return redirect(
            authorization_base_url + 
            '?client_id=' + client_id + 
            '&redirect_uri=' + redirect_uri + 
            '&response_type=code&approval_prompt=auto&scope=activity:write,activity:read_all&state=test')

class VistaActiveUser(Resource):
    def get(self):
        user_id = request.args.get('user_id')
        print(user_id_log, user_id)
        logger.debug(user_id_log + user_id)
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            logger.error(" Usuario no registrado")
            return {"message": "Usuario no registrado", "code": 404}, 404
        strava_user = StravaUser.query.filter_by(user_id=user_id).first()
        if strava_user is None:
            logger.error(" Usuario no registrado en Strava")
            return {"message": "Usuario no registrado en Strava", "code": 404}, 404
        access_token = strava_user.access_token
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response_athlete = requests.get(athlete_url, headers=headers)
        print('status_code 1: ',response_athlete.status_code)
        if response_athlete.status_code != 200:
            return {"message": "Error register token is not working", "code": 500}, 500
        return {"message": "OK", "code": 200, "strava_user": strava_user_schema.dump(strava_user)}, 200

def resolve_callback(url, id):
    print(' * id:', id)
    error = request.args.get('error')
    if error:
        print(' * error:', error)
        return callback_response(url + '?error=' + error)
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        scope = request.args.get('scope')
        print(' * code:', code)
        print(' * state:', state)
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'grant_type': 'authorization_code'
        }
        response = requests.post(token_url, data=data)
        response_data = response.json()
        print(' * response_data:', response_data)
        print(' * response:', response.status_code)
        if response.status_code == 200:
            response_data = response.json()
            timestamp = response_data.get('expires_at')
            fecha = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            access_token = response_data.get('access_token')
            refresh_token = response_data.get('refresh_token')
            # Register user tokens
            print(' * access_token:', access_token)
            print(' * refresh_token:', refresh_token)
            print("La fecha correspondiente al timestamp es:", fecha)
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            response_athlete = requests.get(athlete_url, headers=headers)
            athlete = response_athlete.json()
            print(' * athlete:', athlete)
            athlete_id = athlete.get('id')
            expiration_token =datetime.strptime(
                fecha, date_format
            )
            # Save athlete
            user_registered = StravaUser.query.filter_by(user_id = id).first()
            if user_registered:
                user_registered.code = code
                user_registered.scope = scope
                user_registered.access_token = access_token
                user_registered.refresh_token = refresh_token
                user_registered.timestamp = timestamp
                user_registered.expiration_token = expiration_token
                user_registered.updatedAt = datetime.now()
                db.session.commit()
                print(' * user_registered:', strava_user_schema.dump(user_registered))
                return redirect(url + '?athlete_id=' + str(athlete_id))
            
            id_strava_user = generate_uuid()
            athlete = StravaUser (
                id=id_strava_user,
                user_id=id,
                athlete_id=athlete_id,
                code=code,
                scope=scope,
                access_token=access_token,
                refresh_token=refresh_token,
                timestamp=timestamp,
                expiration_token=expiration_token,
                createdAt=datetime.now(),
                updatedAt=datetime.now(),
            )
            db.session.add(athlete)
            db.session.commit()
            print(' * athlete:', athlete)
            return callback_response(url + '?athlete_id=' + str(athlete_id))
        return callback_response(url + '?error=Error al obtener el token')
    except IntegrityError as e:
        print(' * e:', e)
        return callback_response(url + '?error=Error al obtener el token')

class VistaStravaCallbackLocal(Resource):
    def get(self,id):
        return resolve_callback(front_url_local, id)

class VistaStravaCallback(Resource):
    def get(self,id):
        return resolve_callback(front_url, id)

def refresh_token(refresh_token, user_id):
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    response = requests.post(token_url, data=data)
    print(' * response:', response.status_code)
    if response.status_code == 200:
        response_data = response.json()
        print(' * response_data:', response_data)
        timestamp = response_data.get('expires_at')
        fecha = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        access_token = response_data.get('access_token')
        refresh_token = response_data.get('refresh_token')
        strava_user = StravaUser.query.filter_by(user_id=user_id).first()
        if strava_user:
            strava_user.access_token = access_token
            strava_user.refresh_token = refresh_token
            strava_user.timestamp = timestamp
            strava_user.expiration_token = datetime.strptime(
                fecha, date_format
            )
            strava_user.updatedAt = datetime.now()
            db.session.commit()
            return {
                "message": "OK", 
                "code": 200, 
                "expires_at": str(fecha), 
                "timestamp":timestamp,
                "access_token": access_token,
                "refresh_token": refresh_token
            }
    return {"message": "Error", "code": 500}

class VistaRefreshToken(Resource):
    def get(self):
        user_id = request.args.get('user_id')
        print(user_id_log, user_id)
        strava_user = StravaUser.query.filter_by(user_id=user_id).first()
        if strava_user is None:
            return {"message": msg_error_user_not_registered, "code": 404}, 404
        rslt = refresh_token(strava_user.refresh_token, user_id)
        return rslt

class VistaStravaAtlhlete(Resource):
    def get(self):
        user_id = request.args.get('user_id')
        print(user_id_log, user_id)
        strava_user = StravaUser.query.filter_by(user_id=user_id).first()
        if strava_user is None:
            return {"message": msg_error_user_not_registered, "code": 404}, 404
        access_token = strava_user.access_token
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response_athlete = requests.get(athlete_url, headers=headers)
        if response_athlete.status_code != 200:
            rslt = refresh_token(strava_user.refresh_token, user_id)
            if rslt.get('code') != 200:
                return rslt, 500
            access_token = rslt.get('access_token')
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            response_athlete = requests.get(athlete_url, headers=headers)
        athlete = response_athlete.json()
        return {"message": "OK", "code": 200, "athlete": athlete}, 200
    
def getActivities(user_id, access_token, strava_user):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response_activities = requests.get(activities_url, headers=headers)
    if response_activities.status_code != 200:
        rslt = refresh_token(strava_user.refresh_token, user_id)
        if rslt.get('code') != 200:
            return rslt, 500
        access_token = rslt.get('access_token')
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response_activities = requests.get(activities_url, headers=headers)
    return response_activities.json()

class VistaStravaActivities(Resource):
    def get(self):
        user_id = request.args.get('user_id')
        print(user_id_log, user_id)
        strava_user = StravaUser.query.filter_by(user_id=user_id).first()
        if strava_user is None:
            return {"message": msg_error_user_not_registered, "code": 404}, 404
        access_token = strava_user.access_token
        activities = getActivities(user_id, access_token, strava_user)
        return {"message": "OK", "code": 200, "activities": activities}, 200

    def post(self):
        user_id = request.args.get('user_id')
        print(user_id_log, user_id)
        strava_user = StravaUser.query.filter_by(user_id=user_id).first()
        if strava_user is None:
            return {"message": msg_error_user_not_registered, "code": 404}, 404
        access_token = strava_user.access_token
        
        json_data = request.get_json()
        form_data = MultipartEncoder(fields=json_data)
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': form_data.content_type
        }
        response = requests.post(activity_url, headers=headers, data=form_data)
        return {"message": "OK", "code": 200, "response": response.json()}, 200

class VistaStravaActivityDetail(Resource):
    def get(self):
        user_id = request.args.get('user_id')
        print(user_id_log, user_id)
        strava_user = StravaUser.query.filter_by(user_id=user_id).first()
        if strava_user is None:
            return {"message": msg_error_user_not_registered, "code": 404}, 404
        access_token = strava_user.access_token
        activity_id = request.args.get('activity_id')
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        activity_detail_url = f'{activity_url}/{activity_id}'
        response_activity = requests.get(activity_detail_url, headers=headers) # NOSONAR
        if response_activity.status_code != 200:
            rslt = refresh_token(strava_user.refresh_token, user_id)
            if rslt.get('code') != 200:
                return rslt, 500
            access_token = rslt.get('access_token')
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            response_activity = requests.get(activity_detail_url, headers=headers) # NOSONAR
        activity = response_activity.json()
        return {"message": "OK", "code": 200, "activity": activity}, 200

class VistaSyncActivities(Resource):
    def post(self):
        user_id = request.args.get('user_id')
        print(user_id_log, user_id)
        strava_user = StravaUser.query.filter_by(user_id=user_id).first()
        if strava_user is None:
            return {"message": msg_error_user_not_registered, "code": 404}, 404
        access_token = strava_user.access_token
        activities = getActivities(user_id, access_token, strava_user)
        for activity in activities:
            id_activity = activity.get('id')
            athlete_id = activity.get('athlete').get('id')
            activity_name = activity.get('name')
            activity_description = ''
            activity_type = activity.get('type')
            activity_distance = activity.get('distance')
            activity_trainer = activity.get('trainer')
            activity_commute = activity.get('commute')
            start_date_local = activity.get('start_date_local')
            elapsed_time = activity.get('elapsed_time')
            sync = 1
            activity_registered = StravaActivity.query.filter_by(id=id_activity).first()
            if activity_registered:
                activity_registered.athlete_id = athlete_id
                activity_registered.activity_name = activity_name
                activity_registered.activity_description = activity_description
                activity_registered.activity_type = activity_type
                activity_registered.activity_distance = activity_distance
                activity_registered.activity_trainer = activity_trainer
                activity_registered.activity_commute = activity_commute
                activity_registered.start_date_local = start_date_local
                activity_registered.elapsed_time = elapsed_time
                activity_registered.sync = sync
                activity_registered.updatedAt = datetime.now()
                db.session.commit()
            else:
                strava_activity = StravaActivity(
                    id=id_activity,
                    athlete_id=athlete_id,
                    activity_name=activity_name,
                    activity_description=activity_description,
                    activity_type=activity_type,
                    activity_distance=activity_distance,
                    activity_trainer=activity_trainer,
                    activity_commute=activity_commute,
                    start_date_local=start_date_local,
                    elapsed_time=elapsed_time,
                    sync=sync,
                    createdAt=datetime.now(),
                    updatedAt=datetime.now()
                )
                db.session.add(strava_activity)
                db.session.commit()
            
        strava_user.last_sync = datetime.now().strftime(date_format)
        db.session.commit()
        return {"message": "OK Sync", "code": 200, "activities": activities}, 200
    
class VistaSportProfile(Resource):
    def post(self):
        try:
            user_id = request.json["user_id"]
            print("user_id", user_id)
            user_profile = SportProfile(
                id = user_id,
                sh_caminar = request.json["sh_caminar"],
                sh_trotar=request.json["sh_trotar"],
                sh_correr=request.json["sh_correr"],
                sh_nadar=request.json["sh_nadar"],
                sh_bicicleta=request.json["sh_bicicleta"],
                pp_fractura=request.json["pp_fractura"],
                pp_esguinse=request.json["pp_esguinse"],
                pp_lumbalgia=request.json["pp_lumbalgia"],
                pp_articulacion=request.json["pp_articulacion"],
                pp_migranias=request.json["pp_migranias"],
                i_vo2max=request.json["i_vo2max"],
                i_ftp=request.json["i_ftp"],
                i_total_practice_time=request.json["i_total_practice_time"],
                i_total_objective_achived=request.json["i_total_objective_achived"],
                h_total_calories=request.json["h_total_calories"],
                h_avg_bpm=request.json["h_avg_bpm"],
                createdAt=datetime.now(),
                updatedAt=datetime.now(),
            )
            db.session.add(user_profile)
            db.session.commit()
            return {
                "message": "Se pudo crear el perfil deportivo exitosmante",
                "user_profile": sport_profile_schema.dump(user_profile),
                "code": 200,
            }, 200
        
        except Exception as e:
            print("error_msg", e)
            db.session.rollback()
            return {
                "message": "No se pudo crear el perfil de entrenamianto",
                "code": 500,
            }, 500
    
    """def get(self):
        user_profile = SportProfile.query.all()
        print("hola", user_profile[0].id)
        if user_profile is None:
            return {
                    "message": "no hay perfiles deportivos exisistentes",
                    "code": 404,
            }, 404
        
        return {
                "message": "Se Encontraron todos los perfiles deportivos buscados",
                "user_profile": sport_profile_schema.dump(user_profile),
                "code": 200,
            }, 200"""
    
class VistaSportProfileId(Resource): 
    def put(self, id):
        try:
            user_id = id
            print(user_id_log, user_id)
            user_profile = SportProfile.query.filter(SportProfile.id == user_id).first()
            if user_profile is None:
                return {
                    "message": "El perfil deportivo no existe",
                    "code": 404,
            }, 404
            user_profile.sh_caminar = request.json["sh_caminar"],
            user_profile.sh_trotar=request.json["sh_trotar"],
            user_profile.sh_correr=request.json["sh_correr"],
            user_profile.sh_nadar=request.json["sh_nadar"],
            user_profile.sh_bicicleta=request.json["sh_bicicleta"],
            user_profile.pp_fractura=request.json["pp_fractura"],
            user_profile.pp_esguinse=request.json["pp_esguinse"],
            user_profile.pp_lumbalgia=request.json["pp_lumbalgia"],
            user_profile.pp_articulacion=request.json["pp_articulacion"],
            user_profile.pp_migranias=request.json["pp_migranias"],
            user_profile.i_vo2max=request.json["i_vo2max"],
            user_profile.i_ftp=request.json["i_ftp"],
            user_profile.i_total_practice_time=request.json["i_total_practice_time"],
            user_profile.i_total_objective_achived=request.json["i_total_objective_achived"],
            user_profile.h_total_calories=request.json["h_total_calories"],
            user_profile.h_avg_bpm=request.json["h_avg_bpm"],
            user_profile.updatedAt=datetime.now(),
            
            db.session.commit() 
            return {
                "message": "Se pudo actualizar el perfil deportivo exitosmante",
                "user_profile": sport_profile_schema.dump(user_profile),
                "code": 200,
            }, 200
        except Exception as e:
            print(error_msg, e)
            db.session.rollback()
            return {
                "message": "No se pudo actualizar el perfil de entrenamianto",
                "code": 500,
            }, 500
        
    def get(self, id):
        user_id = id
        print(user_id_log, user_id)
        user_profile = SportProfile.query.filter(SportProfile.id == user_id).first()
        if user_profile is None:
            return {
                    "message": "El perfil deportivo buscado no existe",
                    "code": 404,
            }, 404
        
        return {
                "message": "Se Encontro El perfil deportivo buscado",
                "user_profile": sport_profile_schema.dump(user_profile),
                "code": 200,
            }, 200
    
    def delete(self, id):
        user_profile = SportProfile.query.get_or_404(id)
        if user_profile is None:
            return {
                    "message": "El perfil deportivo a eliminar no existe",
                    "code": 404,
            }, 404
        db.session.delete(user_profile)
        db.session.commit()
        return {
                "message": "Se elimino correctmante el perfil deportivo",
                "code": 200,
            }, 200


