from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, distinct
import csv

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

print("hey\n")

class RaceResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    car = db.Column(db.String(120), nullable=False)
    run_number = db.Column(db.Integer, nullable=False)
    top_speed = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<RaceResult {self.name}>"


class Drivers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    car = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f"<Drivers {self.name}>"

class RunData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, nullable=False)
    lat = db.Column(db.Float, nullable=False)
    long = db.Column(db.Float, nullable=False)
    speed = db.Column(db.Float, nullable=False)

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/results")
def results():
    top_speed = (
        RaceResult.query.order_by(desc(RaceResult.top_speed))
        .with_entities(
            RaceResult.device_id,
            RaceResult.name,
            RaceResult.car,
            RaceResult.run_number,
            RaceResult.top_speed,
        )
        .all()
    )
    run_number = (
        RaceResult.query.order_by(RaceResult.run_number, desc(RaceResult.top_speed))
        .with_entities(
            RaceResult.device_id,
            RaceResult.name,
            RaceResult.car,
            RaceResult.run_number,
            RaceResult.top_speed,
        )
        .all()
    )
    name = (
        RaceResult.query.order_by(RaceResult.name, RaceResult.run_number)
        .with_entities(
            RaceResult.device_id,
            RaceResult.name,
            RaceResult.car,
            RaceResult.run_number,
            RaceResult.top_speed,
        )
        .all()
    )
    leader = (
        RaceResult.query.order_by(desc(RaceResult.top_speed))
        .with_entities(
            RaceResult.device_id,
            RaceResult.name,
            RaceResult.car,
            RaceResult.run_number,
            RaceResult.top_speed,
        )
        .first()
    )
    last = (
        RaceResult.query.order_by(desc(RaceResult.id))
        .with_entities(
            RaceResult.device_id,
            RaceResult.name,
            RaceResult.car,
            RaceResult.run_number,
            RaceResult.top_speed,
        )
        .limit(5)
        .all()
    )
    club = (
        RaceResult.query.filter(RaceResult.top_speed > 200)
        .order_by(RaceResult.name)
        .with_entities(RaceResult.name)
        .distinct()
        .all()
    )

    data = (
        RaceResult.query.order_by(desc(RaceResult.top_speed), RaceResult.run_number, RaceResult.name)
        .with_entities(
            RaceResult.device_id,
            RaceResult.name,
            RaceResult.car,
            RaceResult.run_number,
            RaceResult.top_speed,
        )
        .all()
    )

    return render_template(
        "results.html",
        top_speed=top_speed,
        run_number=run_number,
        name=name,
        leader=leader,
        club=club,
        last=last,
    )


@app.route("/onedriver")
def onedriver():
    driver_name = request.args.get("name")
    driver = (
        Drivers.query.filter(Drivers.name == driver_name)
        .with_entities(Drivers.device_id, Drivers.name, Drivers.car)
        .first()
    )
    top_speed = (
        RaceResult.query.filter(RaceResult.name == driver_name)
        .order_by(desc(RaceResult.top_speed))
        .with_entities(
            RaceResult.device_id,
            RaceResult.name,
            RaceResult.car,
            RaceResult.run_number,
            RaceResult.top_speed,
        )
        .limit(1)
        .first()
    )

    return render_template(
        "driver.html", name=driver_name, driver=driver, top_speed=top_speed
    )


@app.route("/upload_deprecated", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        data = request.form  # Get form data sent in the request
        if not data:
            return jsonify({"message": "No data provided"}), 400
        # Save the data to the database
        device_id = data.get("device_id")
        name = data.get("name")
        car = data.get("car")
        run_number = int(data.get("run_number"))
        top_speed = float(data.get("top_speed"))

        # Check if the driver already exists in the "drivers" table
        driver = Drivers.query.filter(Drivers.device_id == device_id).first()
        if not driver:
            # Create a new driver if not found
            driver = Driver(device_id=device_id, name=name, car=car)
            db.session.add(driver)

        # Save the race result
        result = RaceResult(
            device_id=device_id,
            name=name,
            car=car,
            run=run_number,
            top_speed=top_speed,
        )
        db.session.add(result)
        db.session.commit()
        return jsonify({"message": "Data received"}), 200
    else:
        return render_template("upload.html")


@app.route("/upload_auto_deprecated", methods=["POST"])
def upload_auto():
    data = request.get_json()  # Get JSON data sent in the request
    if not data:
        return jsonify({"message": "No data provided"}), 400
    # Save the data to the database
    device_id = data.get("device_id")
    name = data.get("name")
    car = data.get("car")
    run_number = data.get("run_number")
    top_speed = data.get("top_speed")

    # Check if the driver already exists in the "drivers" table
    driver = Drivers.query.filter(Drivers.device_id == device_id).first()
    if not driver:
        # Create a new driver if not found
        driver = Driver(device_id=device_id, name=name, car=car)
        db.session.add(driver)

    # Save the race result
    result = RaceResult(
        device_id=device_id,
        name=name,
        car=car,
        run=run_number,
        top_speed=top_speed,
    )
    db.session.add(result)
    db.session.commit()
    return jsonify({"message": "Data received"}), 200

@app.route("/upload_run_result", methods=["POST"])
def upload_run_result():
    print("upload_run_result: ")
    data = request.get_data(as_text=True)
    print(data)
    print("\n")
    if not data:
        return jsonify({"message": "No data provided"}), 400
    
    values = data.split(",")
    print(values)
    # Save the data to the database
    device_id = int(values[0].strip())
    run_number = device_id
    top_speed = float(values[1].strip())

    db_row = Drivers.query.filter(Drivers.device_id == device_id).first()
    if not db_row:
        return jsonify({"message": "error, couldn't find device id in Drivers table"}), 400

    name = db_row.name
    car = db_row.car

    print("-------")
    print(device_id)
    print(run_number)
    print(top_speed)
    print(name)
    print(car)
    print("-------")

    # Save the race result
    result = RaceResult(
        device_id=device_id,
        name=name,
        car=car,
        run_number=run_number,
        top_speed=top_speed,
    )
    db.session.add(result)
    db.session.commit()
    return jsonify({"message": "Data received"}), 200

@app.route("/upload_run_data", methods=["POST"])
def upload_run_data():
    print("upload_run_data:")
    data = request.get_data(as_text=True)
    #print("BLOB----------------")
    #print(data)
    #print("PARSED----------------")
    data = data.split("\n")
    dictReader = csv.DictReader(data, fieldnames = ['device_id', 'latitude', 'longitude', 'speed'], delimiter = ',', quotechar = '"')

    #index = 0
    for row in dictReader:
        newRow = RunData(
            device_id=row['device_id'],
            lat=row['latitude'],
            long=row['longitude'],
            speed=row['speed'],
        )
        db.session.add(newRow)

    db.session.commit()
        
    print("END----------------")

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
    app.run(host="0.0.0.0", port=80, debug=True)
