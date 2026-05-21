import flask
from flask import jsonify, make_response, request
from data import db_session
from data.jobs import Jobs
import json

blueprint = flask.Blueprint(
    'jobs_api',
    __name__,
    template_folder='templates'
)


@blueprint.route('/api/jobs', methods=['GET'])
def get_jobs():
    db_sess = db_session.create_session()
    jobs = db_sess.query(Jobs).all()
    
    return jsonify(
        {
            'jobs': [item.to_dict(only=(
                'id', 'job', 'team_leader', 'work_size', 
                'collaborators', 'start_date', 'end_date', 
                'is_finished')) for item in jobs]
        }
    )

@blueprint.route('/api/jobs/<int:job_id>')
def get_one_job(job_id):
    db_sess = db_session.create_session()
    jobs = db_sess.query(Jobs).filter(Jobs.id == job_id).first()
    if not jobs:
        return make_response(json.dumps({'error': 'Нет такого ID :()'}, ensure_ascii=False), 404)
    else:
        return jsonify({'job': jobs.to_dict(only=(
                'id', 'job', 'team_leader', 'work_size', 
                'collaborators', 'start_date', 'end_date', 
                'is_finished'))})
    
@blueprint.route('/api/jobs', methods=['POST'])
def create_job():
    if not request.json:
        return make_response(jsonify({'error': 'Нет данных'}), 400)
    
    fields = ('job', 'team_leader', 'work_size', 'collaborators')
    if not all(c in request.json for c in fields):
        return make_response(jsonify({'error': 'Не все данные'}), 400)
    db_sess = db_session.create_session()

    dob = Jobs(job=request.json['job'],
               team_leader=request.json['team_leader'],
        work_size=int(request.json['work_size']),
        collaborators=request.json['collaborators'],
        is_finished=request.json.get('is_finished', False))
    db_sess.add(dob)
    db_sess.commit()
    return jsonify({'jobs': dob.to_dict(only=('id', 'job', 'team_leader', 'work_size', 
                                            'collaborators', 'is_finished'))})

@blueprint.route('/api/jobs/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    db_sess = db_session.create_session()
    job = db_sess.query(Jobs).filter(Jobs.id == job_id).first()

    if not job:
        return make_response(jsonify({'error': 'Not found'}), 404)
    
    db_sess.delete(job)
    db_sess.commit()
    
    return jsonify({'success': 'OK'})

@blueprint.route('/api/jobs/<int:job_id>', methods=['PUT'])
def edit_job(job_id):
    db_sess = db_session.create_session()
    job = db_sess.query(Jobs).filter(Jobs.id == job_id).first()
    
    if not job:
        return make_response(jsonify({'error': 'Not found'}), 404)
    
    if not request.json:
        return make_response(jsonify({'error': 'Нет данных'}), 400)
    
    allowed_fields = ('job', 'team_leader', 'work_size', 'collaborators', 'is_finished')
    if not all(key in allowed_fields for key in request.json.keys()):
        return make_response(jsonify({'error': 'Недопустимое поле'}), 400)
    
    # Обновляем только переданные поля
    if 'job' in request.json:
        job.job = request.json['job']
    if 'team_leader' in request.json:
        job.team_leader = request.json['team_leader']
    if 'work_size' in request.json:
        job.work_size = int(request.json['work_size'])
    if 'collaborators' in request.json:
        job.collaborators = request.json['collaborators']
    if 'is_finished' in request.json:
        job.is_finished = request.json['is_finished']
    
    db_sess.commit()
    
    return jsonify({'job': job.to_dict(only=(
        'id', 'job', 'team_leader', 'work_size',
        'collaborators', 'start_date', 'end_date',
        'is_finished'))})