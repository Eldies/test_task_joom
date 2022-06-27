# -*- coding: utf-8 -*-
import pytest


class TestPingView:
    @pytest.fixture(autouse=True)
    def _setup(self, client):
        self.client = client

    def test_ping(self):
        response = self.client.get('/ping')
        assert response.data.decode('utf-8') == 'pong'
