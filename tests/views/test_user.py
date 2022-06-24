# -*- coding: utf-8 -*-
import logging
from parameterized import parameterized
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

    def tearDown(self):
        with app.app_context():
            db.drop_all()

    def test_post_ok(self):
        with app.app_context():
            assert User.query.with_entities(User.name).all() == []
        response = self.client.post('/user', data=dict(username='bar'))
        assert response.status_code == 200
        assert response.json == {'status': 'ok'}
        with app.app_context():
            assert User.query.with_entities(User.name).all() == [('bar',)]

    @parameterized.expand([
        (None, 'This field is required.'),
        ('', 'This field is required.'),
        ('a', 'Field must be between 2 and 20 characters long.'),
        ('a' * 21, 'Field must be between 2 and 20 characters long.'),
        ('a b', 'Invalid input.'),
        ('1ab', 'Invalid input.'),
    ])
    def test_post_wrong_username(self, username, error):
        response = self.client.post('/user', data=dict(username=username))
        assert response.status_code == 400
        assert response.json == {'status': 'error', 'error': {'username': [error]}}

    def test_post_username_already_exists(self):
        with app.app_context():
            db.session.add(User(name='foo'))
            db.session.commit()
        response = self.client.post('/user', data=dict(username='foo'))
        assert response.status_code == 400
        assert response.json == {'status': 'error', 'error': 'user already exists'}
