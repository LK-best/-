import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase


class CarRequest(SqlAlchemyBase):
    __tablename__ = 'car_requests'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    phone = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    car_model = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    car_year = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    mileage = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    condition = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    comment = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    price_offer = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    status = sqlalchemy.Column(sqlalchemy.String, default='Новая')
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"),
                                nullable=True)

    user = sqlalchemy.orm.relationship('User')
