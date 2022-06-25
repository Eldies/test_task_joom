# -*- coding: utf-8 -*-
import logging
from parameterized import parameterized
import unittest

from app import app, db
from models import User


class TestUsersView(unittest.TestCase):
    def setUp(self):
        app.logger.setLevel(logging.DEBUG)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        with app.app_context():
            db.create_all()

        self.client = app.test_client()

    def tearDown(self):
        with app.app_context():
            db.drop_all()

    def test_post_ok(self):
        with app.app_context():
            assert User.query.with_entities(User.name).all() == []
        response = self.client.post('/users', data=dict(username='bar'))
        assert response.status_code == 200
        assert response.json == {'status': 'ok'}
        with app.app_context():
            assert User.query.with_entities(User.name).all() == [('bar',)]

    @parameterized.expand([
        (None, 'field required'),
        ('', 'ensure this value has at least 2 characters'),
        ('a', 'ensure this value has at least 2 characters'),
        ('a' * 21, 'ensure this value has at most 20 characters'),
        ('a b', 'string does not match regex "^[a-zA-Z_]\\w*$"'),
        ('1ab', 'string does not match regex "^[a-zA-Z_]\\w*$"'),
    ])
    def test_post_wrong_username(self, username, error):
        response = self.client.post('/users', data=dict(username=username))
        assert response.status_code == 400
        assert response.json == {'status': 'error', 'error': {'username': [error]}}

    def test_post_username_already_exists(self):
        with app.app_context():
            db.session.add(User(name='foo'))
            db.session.commit()
        response = self.client.post('/users', data=dict(username='foo'))
        assert response.status_code == 400
        assert response.json == {'status': 'error', 'error': 'user already exists'}
