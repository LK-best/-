import flask
from flask import jsonify, make_response, request
from data import db_session
from data.users import Users

blueprint = flask.Blueprint(
    'users_api',
    __name__,
    template_folder='templates'
)

@blueprint.route('/api/users', methods=['GET'])
def get_users():
    db_sess = db_session.create_session()
    users = db_sess.query(Users).all()
    return jsonify(
        {
            'users': [item.to_dict(only=(
                'id', 'name', 'surname', 'age', 'position', 
                'speciality', 'address', 'email', 'modified_date', 'created_date'
            )) for item in users]
        }
    )

@blueprint.route('/api/users/<int:user_id>', methods=['GET'])
def get_one_user(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(Users).filter(Users.id == user_id).first()
    if not user:
        return make_response(jsonify({'error': 'Not found'}), 404)
    return jsonify(
        {
            'user': user.to_dict(only=(
                'id', 'name', 'surname', 'age', 'position', 
                'speciality', 'address', 'email', 'modified_date', 'created_date'
            ))
        }
    )

@blueprint.route('/api/users', methods=['POST'])
def create_user():
    if not request.json:
        return make_response(jsonify({'error': 'Нет данных'}), 400)
    
    required_fields = ('name', 'surname', 'age', 'email')
    if not all(key in request.json for key in required_fields):
        return make_response(jsonify({'error': 'Не все обязательные данные'}), 400)
    
    db_sess = db_session.create_session()
    
    user = Users(
        name=request.json['name'],
        surname=request.json['surname'],
        age=int(request.json['age']),
        position=request.json.get('position', ''),
        speciality=request.json.get('speciality', ''),
        address=request.json.get('address', ''),
        email=request.json['email']
    )
    
    db_sess.add(user)
    db_sess.commit()
    return jsonify({'user': user.to_dict(only=(
        'id', 'name', 'surname', 'age', 'position', 
        'speciality', 'address', 'email'
    ))})

@blueprint.route('/api/users/<int:user_id>', methods=['PUT'])
def edit_user(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(Users).filter(Users.id == user_id).first()
    
    if not user:
        return make_response(jsonify({'error': 'Not found'}), 404)
    
    if not request.json:
        return make_response(jsonify({'error': 'Нет данных'}), 400)
    
    allowed_fields = ('name', 'surname', 'age', 'position', 'speciality', 'address', 'email')
    if not all(key in allowed_fields for key in request.json.keys()):
        return make_response(jsonify({'error': 'Недопустимое поле'}), 400)
    
    if 'name' in request.json:
        user.name = request.json['name']
    if 'surname' in request.json:
        user.surname = request.json['surname']
    if 'age' in request.json:
        user.age = int(request.json['age'])
    if 'position' in request.json:
        user.position = request.json['position']
    if 'speciality' in request.json:
        user.speciality = request.json['speciality']
    if 'address' in request.json:
        user.address = request.json['address']
    if 'email' in request.json:
        user.email = request.json['email']
    
    db_sess.commit()
    
    return jsonify({'user': user.to_dict(only=(
        'id', 'name', 'surname', 'age', 'position', 
        'speciality', 'address', 'email', 'modified_date', 'created_date'
    ))})

@blueprint.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(Users).filter(Users.id == user_id).first()
    
    if not user:
        return make_response(jsonify({'error': 'Not found'}), 404)
    
    db_sess.delete(user)
    db_sess.commit()
    
    return jsonify({'success': 'OK'})