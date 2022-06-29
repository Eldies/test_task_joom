from enum import Enum


class RepeatTypeEnum(str, Enum):
    none = 'none'
    daily = 'daily'
    weekly = 'weekly'
    every_working_day = 'every_working_day'
    yearly = 'yearly'
    monthly = 'monthly'