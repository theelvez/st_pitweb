from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, distinct
import random

app = Flask(__name__)

# SQLite database configuration
DB_NAME = "race_data.db"  # Replace with your SQLite database file name

# Create the SQLite connection URL
DB_CONNECTION_URL = f"sqlite:///{DB_NAME}"

# Set the SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_DATABASE_URI"] = DB_CONNECTION_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

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
      
    top_speed = RaceResult.query.order_by(desc("top_speed"))
    run_number = RaceResult.query.order_by("run_number", desc("top_speed"))
    name = RaceResult.query.order_by("name", "run_number")
    leader = RaceResult.query.order_by(desc("top_speed")).first()
    last = RaceResult.query.order_by(desc("id")).limit(5)
    club = RaceResult.query.filter(RaceResult.top_speed > 200).order_by(RaceResult.name).with_entities(RaceResult.name).distinct()
    
    data = RaceResult.query.order_by(desc("top_speed"), "run_number", "name")
    
    return render_template("results.html", top_speed=top_speed, run_number=run_number, name=name, leader=leader, club=club, last=last)
    
@app.route("/onedriver")
def onedriver():
      
    driver = RaceResult.query.filter(RaceResult.name == request.args.get('name'))
    top_speed = RaceResult.query.filter(RaceResult.name == request.args.get('name')).order_by(desc("top_speed")).limit(1)
    
    return render_template("driver.html", name=request.args.get('name'), driver=driver, top_speed=top_speed)
        

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
    app.run(host="0.0.0.0", port=5000, debug=True)
