from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///race_results.db'
db = SQLAlchemy(app)

class RaceResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    car = db.Column(db.String(120), nullable=False)
    run_number = db.Column(db.Integer, nullable=False)
    top_speed = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<RaceResult {self.name}>'

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/results')
def results():
    data = RaceResult.query.all()  # Get all race results from the database
    return render_template('results.html', data=data)

@app.route('/upload', methods=['POST'])
def upload():
    # Here, you would typically get the data from the form and save it to the database.
    # For now, we'll just return a placeholder message.
    return jsonify({'message': 'Data received'}), 200

@app.route('/upload_auto', methods=['POST'])
def upload_auto():
    data = request.get_json()  # Get JSON data sent in the request
    if not data:
        return jsonify({'message': 'No data provided'}), 400
    # Save the data to the database
    result = RaceResult(name=data['name'], car=data['car'], run_number=data['run_number'], top_speed=data['top_speed'])
    db.session.add(result)
    db.session.commit()
    return jsonify({'message': 'Data received'}), 200

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create the database table
    app.run(host='0.0.0.0', port=5050, debug=True, use_reloader=False)


