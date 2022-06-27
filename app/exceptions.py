# -*- coding: utf-8 -*-
class BaseLocalException(Exception):
    pass


class NotFoundException(BaseLocalException):
    code: int = 404


class AlreadyExistsException(BaseLocalException):
    code: int = 400
