import logging
import os
import azure.functions as func
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from azure.storage.blob import BlobServiceClient

app = Flask(__name__)

# Azure Blob Storage configuration
BLOB_STORAGE_CONNECTION_STRING = os.getenv("DefaultEndpointsProtocol=https;AccountName=pitwebstorage;AccountKey=mr4ZIFYYqhct+TvyhAR/J0JBEzvoaNlFRBOMttoxLzOaQG2Bmyv1w/6YN/ui0V0NTC+B/OeMWzvs+AStPwOBEA==;EndpointSuffix=core.windows.net")
BLOB_CONTAINER_NAME = os.getenv("pitwebstoragecontainer")
BLOB_DATABASE_FILE_NAME = "race_results.db"

class RaceResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    car = db.Column(db.String(120), nullable=False)
    run_number = db.Column(db.Integer, nullable=False)
    top_speed = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<RaceResult {self.name}>"

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
    with open(BLOB_DATABASE_FILE_NAME, "wb") as file:
        blob_client = container_client.get_blob_client(BLOB_DATABASE_FILE_NAME)
        download_stream = blob_client.download_blob()
        file.write(download_stream.readall())

def upload_database_file():
    blob_service_client = BlobServiceClient.from_connection_string(BLOB_STORAGE_CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)
    
    # Upload the database file to Blob Storage
    with open(BLOB_DATABASE_FILE_NAME, "rb") as file:
        blob_client = container_client.get_blob_client(BLOB_DATABASE_FILE_NAME)
        blob_client.upload_blob(file)

def create_app():
    # Set SQLAlchemy database URI to use SQLite in-memory database
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    db.init_app(app)

    # Initialize and download database file before the first request
    with app.app_context():
        initialize_blob_storage()
        download_database_file()

    # Register routes
    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/results")
    def results():
        data = RaceResult.query.all()  # Get all race results from the database
        return render_template("results.html", data=data)

    @app.route("/upload", methods=["GET", "POST"])
    def upload():
        if request.method == "POST":
            data = request.form  # Get form data sent in the request
            if not data:
                return jsonify({"message": "No data provided"}), 400
            # Save the data to the database
            result = RaceResult(
                name=data["name"],
                car=data["car"],
                run_number=int(data["run_number"]),
                top_speed=float(data["top_speed"]),
            )
            db.session.add(result)
            db.session.commit()
            return jsonify({"message": "Data received"}), 200
        else:
            return render_template("upload.html")

    @app.route("/upload_auto", methods=["POST"])
    def upload_auto():
        data = request.get_json()  # Get JSON data sent in the request
        if not data:
            return jsonify({"message": "No data provided"}), 400
        # Save the data to the database
        result = RaceResult(
            name=data["name"],
            car=data["car"],
            run_number=data["run_number"],
            top_speed=data["top_speed"],
        )
        db.session.add(result)
        db.session.commit()
        return jsonify({"message": "Data received"}), 200

    @app.route("/about")
    def about():
        return render_template("about.html")

    @app.route("/contact")
    def contact():
        return render_template("contact.html")

    return app

main = func.create_http_function(
    app=create_app(),
    route=None
)
