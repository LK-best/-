@app.route('/info')
def spisok():
    db = db_session.create_session()
    jobs = db.query(Jobs).all()
    return render_template("base.html", jobs=jobs)