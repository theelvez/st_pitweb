from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from azure.storage.blob import BlobServiceClient

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///race_results.db'
db = SQLAlchemy(app)

# Azure Blob Storage configuration
BLOB_STORAGE_CONNECTION_STRING = '<your_blob_storage_connection_string>'
BLOB_CONTAINER_NAME = '<your_blob_container_name>'
BLOB_DATABASE_FILE_NAME = 'race_results.db'

class RaceResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    car = db.Column(db.String(120), nullable=False)
    run_number = db.Column(db.Integer, nullable=False)
    top_speed = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<RaceResult {self.name}>'

def initialize_blob_storage():
    blob_service_client = BlobServiceClient.from_connection_string(BLOB_STORAGE_CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)
    
    # Check if the container exists, create it if it doesn't
    if not container_client.exists():
        container_client.create_container()

def download_database_file():
    blob_service_client = BlobServiceClient.from_connection_string(BLOB_STORAGE_CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)
    
    # Download the database file from Blob Storage
    with open('race_results.db', 'wb') as file:
        blob_client = container_client.get_blob_client(BLOB_DATABASE_FILE_NAME)
        download_stream = blob_client.download_blob()
        file.write(download_stream.readall())

def upload_database_file():
    blob_service_client = BlobServiceClient.from_connection_string(BLOB_STORAGE_CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)
    
    # Upload the database file to Blob Storage
    with open('race_results.db', 'rb') as file:
        blob_client = container_client.get_blob_client(BLOB_DATABASE_FILE_NAME)
        blob_client.upload_blob(file)



@app.before_first_request
def before_first_request():
    initialize_blob_storage()
    download_database_file()



@app.teardown_appcontext
def teardown_appcontext(exception=None):
    upload_database_file()



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
    app.run()
