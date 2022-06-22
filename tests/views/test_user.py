# -*- coding: utf-8 -*-
import logging
import unittest

from app import app, db
from models import User


class TestImageView(unittest.TestCase):
    def setUp(self):
        app.logger.setLevel(logging.DEBUG)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        with app.app_context():
            db.create_all()

        self.client = app.test_client()

    def test_post_ok(self):
        with app.app_context():
            assert User.query.with_entities(User.name).all() == []
        response = self.client.post('/user', data=dict(username='bar'))
        assert response.status_code == 200
        assert response.json == {'status': 'ok'}
        with app.app_context():
            assert User.query.with_entities(User.name).all() == [('bar',)]

    def test_post_no_username(self):
        response = self.client.post('/user', data=dict(foo='bar'))
        assert response.status_code == 400
        assert response.json == {'status': 'error', 'error': 'no username'}

    def test_post_username_already_exists(self):
        with app.app_context():
            db.session.add(User(name='foo'))
            db.session.commit()
        response = self.client.post('/user', data=dict(username='foo'))
        assert response.status_code == 400
        assert response.json == {'status': 'error', 'error': 'user already exists'}
