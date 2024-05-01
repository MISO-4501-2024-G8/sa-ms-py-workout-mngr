from dataclasses import dataclass

from datetime import datetime
import requests
from flask import request, redirect
from flask_jwt_extended import create_access_token, jwt_required
from flask_restful import Resource

from modelos.modelos import (
    User,
    UserSessionSchema,
    db,
)

from pathlib import Path
from decouple import config
import json
import uuid

from sqlalchemy.exc import IntegrityError

user_schema = UserSessionSchema()

client_id = '125884'
client_secret = 'a0f691d5d314ebf2042c2e8ab477c7fcbfc2f86c'
redirect_uri = 'http://localhost:5001/auth_callback'
authorization_base_url = 'https://www.strava.com/oauth/authorize'
token_url = 'https://www.strava.com/oauth/token'
athlete_url = 'https://www.strava.com/api/v3/athlete'


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

class VistaStravaCallback(Resource):
    def get(self):
        code = request.args.get('code')
        state = request.args.get('state')
        print(' * code:', code)
        print(' * state:', state)
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'grant_type': 'authorization_code'
        }
        response = requests.post(token_url, data=data)
        print(' * response:', response.status_code)
        if response.status_code == 200:
            response_data = response.json()
            print(' * response_data:', response_data)
            timestamp = response_data.get('expires_at')
            fecha = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            print("La fecha correspondiente al timestamp es:", fecha)
            access_token = response_data.get('access_token')
            refresh_token = response_data.get('refresh_token')
            print(' * access_token:', access_token)
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            response_athlete = requests.get(athlete_url, headers=headers)
            athlete = response_athlete.json()
            print(' * athlete:', athlete)
            return {
                "message": "OK", 
                "code": 200, 
                "expires_at": str(fecha), 
                "timestamp":timestamp,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "athlete": athlete
            }, 200
        return {"message": "Error", "code": 500}, 500
    
class VistaRefreshToken(Resource):
    def get(self):
        refresh_token = request.args.get('token')
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
            print("La fecha correspondiente al timestamp es:", fecha)
            access_token = response_data.get('access_token')
            refresh_token = response_data.get('refresh_token')
            print(' * access_token:', access_token)
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            response_athlete = requests.get(athlete_url, headers=headers)
            athlete = response_athlete.json()
            return {
                "message": "OK", 
                "code": 200, 
                "expires_at": str(fecha), 
                "timestamp":timestamp,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "athlete": athlete
            }, 200
        return {"message": "Error", "code": 500}, 500