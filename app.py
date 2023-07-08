from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=pitwebstorage;AccountKey=mr4ZIFYYqhct+TvyhAR/J0JBEzvoaNlFRBOMttoxLzOaQG2Bmyv1w/6YN/ui0V0NTC+B/OeMWzvs+AStPwOBEA==;BlobEndpoint=https://pitwebstorage.blob.core.windows.net/;FileEndpoint=https://pitwebstorage.file.core.windows.net/;QueueEndpoint=https://pitwebstorage.queue.core.windows.net/;TableEndpoint=https://pitwebstorage.table.core.windows.net/"

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

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        data = request.form  # Get form data sent in the request
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        # Save the data to the database
        result = RaceResult(name=data['name'], car=data['car'], run_number=int(data['run_number']), top_speed=float(data['top_speed']))
        db.session.add(result)
        db.session.commit()
        return jsonify({'message': 'Data received'}), 200
    else:
        return render_template('upload.html')



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
    app.run()


