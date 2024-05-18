import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import patch, MagicMock
from app import app
import json
import random
from faker import Faker
from unittest import TestCase
from faker.generator import random
import string
from flask_restful import Api
from flask import Flask
from flask_restful import Resource
from modelos.modelos import (
    SportProfile,
    SportProfileSchema,
    db,
)
from urllib.parse import urlparse
from datetime import datetime

sport_profile_schema = SportProfileSchema()



class VistaSportProfile(TestCase):
    def setUp(self):
        self.data_factory = Faker()
        self.app = app.test_client()
        self.endpoint = "/sport_profile"

    def test_post_no_None(self):
        nuevo_sport_profile_fake = {
            "user_id": self.data_factory.name(),
            "sh_caminar": self.data_factory.random_digit(),
            "sh_trotar": self.data_factory.random_digit(),
            "sh_correr": self.data_factory.random_digit(),
            "sh_nadar":self.data_factory.random_digit(),
            "sh_bicicleta":self.data_factory.random_digit(),
            "pp_fractura":self.data_factory.random_digit(),
            "pp_esguinse":self.data_factory.random_digit(),
            "pp_lumbalgia":self.data_factory.random_digit(),
            "pp_articulacion":self.data_factory.random_digit(),
            "pp_migranias":self.data_factory.random_digit(),
            "i_vo2max": "130",
            "i_ftp": "266",
            "i_total_practice_time": "150.25",
            "i_total_objective_achived":"5",
            "h_total_calories":"3820",
            "h_avg_bpm": "120"
        }
        response = self.app.post(self.endpoint,
                                data = json.dumps(nuevo_sport_profile_fake),
                                headers={'Content-Type': 'application/json'}).get_data().decode("utf-8")
        print(response)
        self.assertIsNotNone(response)

class VistaSportProfileId(TestCase):
    def setUp(self):
        self.data_factory = Faker()
        self.app = app.test_client()
        self.endpoint_id = "/sport_profile/06e18a47"

    def test_put_no_None(self):
        nuevo_sport_profile_fake = {
            "user_id": self.data_factory.name(),
            "sh_caminar": self.data_factory.random_digit(),
            "sh_trotar": self.data_factory.random_digit(),
            "sh_correr": self.data_factory.random_digit(),
            "sh_nadar":self.data_factory.random_digit(),
            "sh_bicicleta":self.data_factory.random_digit(),
            "pp_fractura":self.data_factory.random_digit(),
            "pp_esguinse":self.data_factory.random_digit(),
            "pp_lumbalgia":self.data_factory.random_digit(),
            "pp_articulacion":self.data_factory.random_digit(),
            "pp_migranias":self.data_factory.random_digit(),
            "i_vo2max": "130",
            "i_ftp": "266",
            "i_total_practice_time": "150.25",
            "i_total_objective_achived":"5",
            "h_total_calories":"3820",
            "h_avg_bpm": "120"
        }
        response = self.app.put(self.endpoint_id,
                                data = json.dumps(nuevo_sport_profile_fake),
                                headers={'Content-Type': 'application/json'}).get_data().decode("utf-8")
        print(response)
        self.assertIsNotNone(response)

    def test_get_no_None(self):
        response = self.app.get(self.endpoint_id,
                                headers={'Content-Type': 'application/json'}).get_data().decode("utf-8")
        print(response)
        self.assertIsNotNone(response)

    def test_delete_no_None(self):
        response = self.app.delete(self.endpoint_id,
                                headers={'Content-Type': 'application/json'}).get_data().decode("utf-8")
        print(response)
        self.assertIsNotNone(response)
        

