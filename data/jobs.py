import datetime
import sqlalchemy as sa
from sqlalchemy import orm
from .db_session import SqlAlchemyBase
from datetime import timedelta
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin


class Jobs(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'jobs'
    name = sa.Column(sa.String)        # Имя клиента
    phone = sa.Column(sa.String)       # Телефон
    car_model = sa.Column(sa.String)    # Марка/модель
    year = sa.Column(sa.Integer)        # Год выпуска
    mileage = sa.Column(sa.Integer)      # Пробег
    condition = sa.Column(sa.String)    # Состояние
    price_offer = sa.Column(sa.Integer)  # Предложенная цена
    status = sa.Column(sa.String)        # 

    user = orm.relationship('User')
    categories = orm.relationship("Category", secondary="association", backref="jobs")