# -*- coding: utf-8 -*-
import unittest

from app import app


class TestPingView(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_ping(self):
        response = self.client.get('/ping')
        assert response.data.decode('utf-8') == 'pong'
