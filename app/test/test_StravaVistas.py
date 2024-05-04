import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import patch, MagicMock
from app import app
import json
import random
import string
from flask_restful import Api
from flask import Flask
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
from urllib.parse import urlparse
from datetime import datetime

user_schema = UserSessionSchema()
strava_user_schema = StravaUserSchema()
strava_activity_schema = StravaActivitySchema()


class TestVistaHealthCheck(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app = app.test_client()

    def test_health_check(self):
        response = self.app.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {"message": "OK", "code": 200})


class TestVistaStravaLogin(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app = app.test_client()

    def test_strava_login(self):
        response = self.app.get("/strava_login")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).netloc, "www.strava.com")


class TestVistaActiveUser(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app = app.test_client()

    def test_active_user(self):
        user = User(
            id="123",
            email="",
            password="",
            doc_num="",
            doc_type="CC",
            name="John Doe",
            phone="1234567890",
            user_type=1,
            token="",
            expiration_token=datetime.now(),
            createdAt=datetime.now(),
            updatedAt=datetime.now(),
        )
        db.session.add(user)
        strava_user = StravaUser(
            id="123",
            user_id=user.id,
            athlete_id="123",
            code="123",
            scope="read",
            access_token="123",
            refresh_token="123",
            timestamp=123,
            last_sync="",
            expiration_token=datetime.now(),
            createdAt=datetime.now(),
            updatedAt=datetime.now(),
        )
        db.session.add(strava_user)
        db.session.commit()

        response = self.app.get("/active_user?user_id=123")
        response_data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data["strava_user"]["athlete_id"], "123")


class TestVistaStravaCallbackLocal(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app = app.test_client()

    @patch("requests.post")
    @patch("requests.get")
    def test_strava_callback_local(self,  mock_get, mock_post):
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: {"id": 123}),
            MagicMock(status_code=200, json=lambda: {"id": 456}),
            # Add more responses as needed
        ]
        mock_post.side_effect = [
            MagicMock(
                status_code=200,
                json=lambda: {
                    "access_token": "123",
                    "refresh_token": "123",
                    "expires_at": 123,
                    "athlete": {"id": 123},
                },
            ),
            MagicMock(
                status_code=200,
                json=lambda: {
                    "access_token": "456",
                    "refresh_token": "456",
                    "expires_at": 456,
                    "athlete": {"id": 456},
                },
            ),
            # Add more responses as needed
        ]
        response = self.app.get(
            "/auth_callback_local/123?code=123&state=123&scope=read"
        )
        self.assertEqual(response.status_code, 302)
        print(response.location)
        response_2 = self.app.get(
            "/auth_callback/456?code=456&state=456&scope=read"
        )
        self.assertEqual(response_2.status_code, 302)
        print(response_2.location)
