from dataclasses import dataclass

from datetime import datetime
import requests
from flask import request, redirect
from flask_jwt_extended import create_access_token, jwt_required
from flask_restful import Resource

from modelos.modelos import (
    User,
    UserSessionSchema,
    StravaUser,
    StravaUserSchema,
    StravaActivity,
    StravaActivitySchema,
    db,
)

from requests_toolbelt.multipart.encoder import MultipartEncoder
from pathlib import Path
from decouple import config
import json
import uuid

from sqlalchemy.exc import IntegrityError

user_schema = UserSessionSchema()
strava_user_schema = StravaUserSchema()
strava_activity_schema = StravaActivitySchema()

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

def generate_uuid():
    uid = uuid.uuid4()
    parts = str(uid).split("-")
    return parts[0]

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
        print(' * user_id:', user_id)
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return {"message": "Usuario no registrado", "code": 404}, 404
        strava_user = StravaUser.query.filter_by(user_id=user_id).first()
        if strava_user is None:
            return {"message": "Usuario no registrado en Strava", "code": 404}, 404
        return {"message": "OK", "code": 200, "strava_user": strava_user_schema.dump(strava_user)}, 200

def resolve_callback(url, id):
    print(' * id:', id)
    error = request.args.get('error')
    if error:
        print(' * error:', error)
        return redirect(url + '?error=' + error)
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
            return redirect(url + '?athlete_id=' + str(athlete_id))
        return redirect(url + '?error=Error al obtener el token')
    except IntegrityError as e:
        print(' * e:', e)
        return redirect(url + '?error=Error al obtener el token')
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
        print(' * user_id:', user_id)
        strava_user = StravaUser.query.filter_by(user_id=user_id).first()
        if strava_user is None:
            return {"message": msg_error_user_not_registered, "code": 404}, 404
        rslt = refresh_token(strava_user.refresh_token, user_id)
        return rslt
class VistaStravaAtlhlete(Resource):
    def get(self):
        user_id = request.args.get('user_id')
        print(' * user_id:', user_id)
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
        print(' * user_id:', user_id)
        strava_user = StravaUser.query.filter_by(user_id=user_id).first()
        if strava_user is None:
            return {"message": msg_error_user_not_registered, "code": 404}, 404
        access_token = strava_user.access_token
        activities = getActivities(user_id, access_token, strava_user)
        return {"message": "OK", "code": 200, "activities": activities}, 200

    def post(self):
        user_id = request.args.get('user_id')
        print(' * user_id:', user_id)
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
        print(' * user_id:', user_id)
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
        print(' * user_id:', user_id)
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
