# -*- coding: utf-8 -*-
import pytest

from app import create_app


class TestPingView:
    @pytest.fixture(autouse=True)
    def _setup(self):
        app = create_app()
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_ping(self):
        response = self.client.get('/ping')
        assert response.data.decode('utf-8') == 'pong'
