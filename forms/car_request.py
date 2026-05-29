from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, IntegerField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Optional


class CarRequestForm(FlaskForm):
    name = StringField('Ваше имя', validators=[DataRequired()])
    phone = StringField('Телефон', validators=[DataRequired()])
    car_model = StringField('Марка и модель авто', validators=[DataRequired()])
    car_year = IntegerField('Год выпуска', validators=[Optional()])
    mileage = IntegerField('Пробег (км)', validators=[Optional()])
    condition = SelectField('Состояние авто',
                            choices=[
                                ('Хорошее', 'Хорошее'),
                                ('Удовлетворительное', 'Удовлетворительное'),
                                ('После ДТП', 'После ДТП'),
                                ('Не на ходу', 'Не на ходу'),
                                ('Кредит / залог', 'Кредит / залог'),
                                ('Без ПТС', 'Без ПТС')
                            ],
                            validators=[Optional()])
    comment = TextAreaField('Дополнительная информация', validators=[Optional()])
    submit = SubmitField('Получить оценку')
