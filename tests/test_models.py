# -*- coding: utf-8 -*-
from app.models import User


class TestUser:
    def test_same_hash_if_same_salt(self, monkeypatch):
        monkeypatch.setattr('werkzeug.security.gen_salt', lambda length: 'a' * length)
        assert User.generate_password_hash('foo') == User.generate_password_hash('foo')

    def test_different_hash_if_different_password_and_same_salt(self, monkeypatch):
        monkeypatch.setattr('werkzeug.security.gen_salt', lambda length: 'a' * length)
        assert User.generate_password_hash('foo') != User.generate_password_hash('bar')

    def test_different_hash_if_different_salt(self, monkeypatch):
        monkeypatch.setattr('werkzeug.security.gen_salt', lambda length: 'a' * length)
        first = User.generate_password_hash('foo')
        monkeypatch.setattr('werkzeug.security.gen_salt', lambda length: 'b' * length)
        second = User.generate_password_hash('foo')
        assert first != second

    def test_check_password(self):
        user = User(
            name='name',
            password_hash=User.generate_password_hash('foo'),
        )
        assert user.check_password('foo')
        assert not user.check_password('bar')

    def test_hash_changes_between_runs(self, monkeypatch):
        assert User.generate_password_hash('foo') != User.generate_password_hash('foo')
