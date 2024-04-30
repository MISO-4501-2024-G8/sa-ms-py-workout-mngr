from dataclasses import dataclass

from datetime import datetime
import requests
from flask import request
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


class VistaStatusCheck(Resource):
    def get(self):
        return {"message": "OK", "code": 200}, 200