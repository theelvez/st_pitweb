from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# MySQL database configuration
DB_HOST = "pitwebdb.mysql.database.azure.com"
DB_USER = "pwadmin"
DB_PASSWORD = "sp33dtrack3R1!"
DB_NAME = "race_results"

# Create the MySQL connection URL without SSL parameters
DB_CONNECTION_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# Set the SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_DATABASE_URI"] = DB_CONNECTION_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class RaceResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    car = db.Column(db.String(120), nullable=False)
    run_number = db.Column(db.Integer, nullable=False)
    top_speed = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<RaceResult {self.name}>"

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

@app.route("/emptydb", methods=["GET", "POST"])
def emptydb():
    if request.method == "GET":
        return render_template("emptydb.html")
    elif request.method == "POST":
        # Delete all records from the database
        RaceResult.query.delete()
        db.session.commit()
        return jsonify({"message": "Database emptied"}), 200

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

if __name__ == "__main__":
    app.run()
