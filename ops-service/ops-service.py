from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, distinct
import csv

app = Flask(__name__)

# SQLite database configuration
DB_NAME = "SVTdF-2024.sqlite"  # Replace with your SQLite database file name

# Create the SQLite connection URL
DB_CONNECTION_URL = f"sqlite:///{DB_NAME}"

# Set the SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_DATABASE_URI"] = DB_CONNECTION_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db = SQLAlchemy(app)

print("ops-service starting...\n")

# ------------------------------------------------------------
# schema
# ------------------------------------------------------------
class DeviceTable(db.Model):
    __tablename__ = 'device_table'
    mac_address = db.Column(db.Text, primary_key=True)
    device_id = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<Device {self.mac_address} {self.device_id}>"
    
class DriverTable(db.Model):
    __tablename__ = 'driver_table'
    driver_id = db.Column(db.Integer, primary_key=True)
    driver_name = db.Column(db.Text, nullable=False)
    run_count = db.Column(db.Integer, nullable=False)

class CarTable(db.Model):
    __tablename__ = 'car_table'
    car_id = db.Column(db.Integer, primary_key=True)
    car_description = db.Column(db.Text, nullable=False)
    car_owner = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<Car {self.car_id} {self.car_description} {self.car_owner}>"

class DeviceAssignmentTable(db.Model):
    __tablename__ = 'device_assignment_table'
    device_id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<DeviceAssignment {self.device_id} {self.car_id}>"

class RunTable(db.Model):
    __tablename__ = 'run_table'
    result_id = db.Column(db.Integer, primary_key=True)
    heat = db.Column(db.Integer, nullable=False)
    run = db.Column(db.Integer, nullable=False)
    driver_id = db.Column(db.Integer, nullable=False)
    car_id = db.Column(db.Integer, nullable=False)
    device_id = db.Column(db.Integer, nullable=False)
    gps_speed_timestamp = db.Column(db.Text, nullable=False)
    gps_top_speed = db.Column(db.Float, nullable=False)
    laser_speed_timestamp = db.Column(db.Text, nullable=False)
    laser_top_speed = db.Column(db.Float, nullable=False)
    top_speed = db.Column(db.Float, nullable=False)
    datafile_path = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<Run {self.result_id}>"

# ------------------------------------------------------------
# /
# ------------------------------------------------------------
@app.route("/")
def home():
    return render_template("home.html")

# ------------------------------------------------------------
# /
# ------------------------------------------------------------
@app.route("/schedule")
def schedule():
    schedule = RunTable.query.order_by(RunTable.heat, RunTable.run).join(
        DeviceAssignmentTable, RunTable.device_id == DeviceAssignmentTable.device_id
    ).join(
        CarTable, RunTable.car_id == CarTable.car_id
    ).join(
        DriverTable, DriverTable.driver_id == RunTable.driver_id
    ).with_entities(
        RunTable.heat,
        RunTable.run,
        RunTable.car_id,
        RunTable.device_id,
        RunTable.top_speed,
        DriverTable.driver_id,
        DriverTable.driver_name,
        DeviceAssignmentTable.car_id.label('device_in_car'),
        CarTable.car_description
    )
    #print(schedule)
    
    return render_template(
        "schedule.html",
        schedule=schedule.all())

# ------------------------------------------------------------
# /raw-tables
# ------------------------------------------------------------
@app.route("/raw-tables")
def raw_tables():
    print("raw_tables:\n")
    devices = (
        DeviceTable.query
        .with_entities(
            DeviceTable.mac_address, 
            DeviceTable.device_id
        )
        .all()
    )
    drivers = (
        DriverTable.query
        .with_entities(
            DriverTable.driver_id,
            DriverTable.driver_name,
            DriverTable.run_count
        )
        .all()
    )
    cars = (
        CarTable.query
        .with_entities(
            CarTable.car_id,
            CarTable.car_description,
            CarTable.car_owner
        )
        .all()
    )
    device_assignments = (
        DeviceAssignmentTable.query
        .with_entities(
            DeviceAssignmentTable.device_id,
            DeviceAssignmentTable.car_id
        )
        .all()
    )
    runs = (
        RunTable.query
        .with_entities(
            RunTable.result_id,
            RunTable.heat,
            RunTable.run,
            RunTable.driver_id,
            RunTable.car_id,
            RunTable.device_id,
            RunTable.gps_speed_timestamp,
            RunTable.gps_top_speed,
            RunTable.laser_speed_timestamp,
            RunTable.laser_top_speed,
            RunTable.top_speed,
            RunTable.datafile_path
        )
        .all()
    )
    print("    query done\n")
    print(runs)
    return render_template(
        "raw-tables.html", 
        devices=devices,
        drivers=drivers,
        cars=cars,
        device_assignments=device_assignments,
        runs=runs,
    )

# ------------------------------------------------------------
# /remove_device_table_record
# ------------------------------------------------------------
# Expected format:
#   [Content-Type: text/plain]
#   POST {{mac_address}}
@app.route("/remove_device_table_record", methods=["POST"])
def remove_device_table_record():
    data = request.get_data(as_text=True)
    print(f"remove_device_table_record: {data}\n")
    if not data:
        return jsonify({"message": "No data provided"}), 

    mac_address = data.strip()
    DeviceTable.query.filter_by(mac_address = mac_address).delete()
    db.session.commit()

    return jsonify({"message": "device_table updated"}), 200

# ------------------------------------------------------------
# /add_device_table_record
# ------------------------------------------------------------
# Expected format:
#   [Content-Type: text/plain]
#   POST {{mac_address}},{{device_id}}
@app.route("/add_device_table_record", methods=["POST"])
def add_device_table_record():
    data = request.get_data(as_text=True)
    print(f"add_device_table_record: {data}\n")
    if not data:
        return jsonify({"message": "No data provided"}), 400
    
    values = data.split(",")
    print(values)
    # Save the data to the database
    mac_address = values[0].strip().upper()
    device_id = values[1].strip()

    print(f"QUERY FIRST in add operation")
    results = DeviceTable.query.filter_by(mac_address = mac_address)
    if (results.count() == 0):
        # TODO: VALIDATE MAC_ADDRESS format

        result = DeviceTable(
            mac_address=mac_address,
            device_id=device_id,
        )
        db.session.add(result)
        db.session.commit()

        # TODO: ERROR HANDLING  
    else:
        print(f"MODIFY RECORD {results.first().mac_address}")
        results.first().device_id = device_id
        db.session.commit()
        print("MODIFY RECORD COMPLETE")
    
    return jsonify({"message": "device_table updated"}), 200

# ------------------------------------------------------------
# /remove_driver_table_record
# ------------------------------------------------------------
# Expected format:
#   [Content-Type: text/plain]
#   POST {{driver_id}}
@app.route("/remove_driver_table_record", methods=["POST"])
def remove_driver_table_record():
    data = request.get_data(as_text=True)
    print(f"remove_driver_table_record: {data}\n")
    if not data:
        return jsonify({"message": "No data provided"}), 

    driver_id = data.strip()
    DriverTable.query.filter_by(driver_id = driver_id).delete()
    db.session.commit()

    return jsonify({"message": "driver_table updated"}), 200

# ------------------------------------------------------------
# /add_driver_table_record
# ------------------------------------------------------------
# Expected format:
#   [Content-Type: text/plain]
#   POST {{driver_id}},{{driver_name}},{{run_count}}
@app.route("/add_driver_table_record", methods=["POST"])
def add_driver_table_record():
    data = request.get_data(as_text=True)
    print(f"add_driver_table_record: {data}\n")
    if not data:
        return jsonify({"message": "No data provided"}), 400
    
    values = data.split(",")
    print(values)
    # Save the data to the database
    driver_id = values[0].strip()
    driver_name = values[1].strip()
    run_count = values[2].strip()

    print(f"QUERY FIRST in add operation")
    results = DriverTable.query.filter_by(driver_id = driver_id)
    if (results.count() == 0):
        # TODO: VALIDATE MAC_ADDRESS format

        result = DriverTable(
            driver_id = driver_id,
            driver_name = driver_name,
            run_count = run_count
        )
        db.session.add(result)
        db.session.commit()

        # TODO: ERROR HANDLING  
    else:
        print(f"MODIFY RECORD {results.first().driver_id}")
        results.first().driver_name = driver_name
        results.first().run_count = run_count
        db.session.commit()
        print("MODIFY RECORD COMPLETE")
    
    return jsonify({"message": "driver_table updated"}), 200
    
# ------------------------------------------------------------
# /remove_car_table_record
# ------------------------------------------------------------
# Expected format:
#   [Content-Type: text/plain]
#   POST {{car_id}}
@app.route("/remove_car_table_record", methods=["POST"])
def remove_car_table_record():
    data = request.get_data(as_text=True)
    print(f"remove_car_table_record: {data}\n")
    if not data:
        return jsonify({"message": "No data provided"}), 

    car_id = data.strip()
    CarTable.query.filter_by(car_id = car_id).delete()
    db.session.commit()

    return jsonify({"message": "car_table updated"}), 200

# ------------------------------------------------------------
# /add_car_table_record
# ------------------------------------------------------------
# Expected format:
#   [Content-Type: text/plain]
#   POST {{car_id}},{{car_description}},{{car_owner}}
@app.route("/add_car_table_record", methods=["POST"])
def add_car_table_record():
    data = request.get_data(as_text=True)
    print(f"add_car_table_record: {data}\n")
    if not data:
        return jsonify({"message": "No data provided"}), 400
    
    values = data.split(",")
    print(values)
    # Save the data to the database
    car_id = values[0].strip()
    car_description = values[1].strip()
    car_owner = values[2].strip()

    print(f"QUERY FIRST in add operation")
    results = CarTable.query.filter_by(car_id = car_id)
    if (results.count() == 0):
        # TODO: VALIDATE MAC_ADDRESS format

        result = CarTable(
            car_id = car_id,
            car_description = car_description,
            car_owner = car_owner
        )
        db.session.add(result)
        db.session.commit()

        # TODO: ERROR HANDLING  
    else:
        print(f"MODIFY RECORD {results.first().car_id}")
        results.first().car_description = car_description
        results.first().car_owner = car_owner
        db.session.commit()
        print("MODIFY RECORD COMPLETE")
    
    return jsonify({"message": "car_table updated"}), 200

# ------------------------------------------------------------
# /remove_device_assignment_table_record
# ------------------------------------------------------------
# Expected format:
#   [Content-Type: text/plain]
#   POST {{device_id}}
@app.route("/remove_device_assignment_table_record", methods=["POST"])
def remove_device_assignment_table_record():
    data = request.get_data(as_text=True)
    print(f"remove_device_assignment_table_record: {data}\n")
    if not data:
        return jsonify({"message": "No data provided"}), 

    device_id = data.strip()
    DeviceAssignmentTable.query.filter_by(device_id = device_id).delete()
    db.session.commit()

    return jsonify({"message": "device_assignment_table updated"}), 200

# ------------------------------------------------------------
# /add_device_assignment_table_record
# ------------------------------------------------------------
# Expected format:
#   [Content-Type: text/plain]
#   POST {{device_id}},{{car_id}}
@app.route("/add_device_assignment_table_record", methods=["POST"])
def add_device_assignment_table_record():
    data = request.get_data(as_text=True)
    print(f"add_device_assignment_table_record: {data}\n")
    if not data:
        return jsonify({"message": "No data provided"}), 400
    
    values = data.split(",")
    print(values)
    # Save the data to the database
    device_id = values[0].strip()
    car_id = values[1].strip()

    print(f"QUERY FIRST in add operation")
    results = DeviceAssignmentTable.query.filter_by(device_id = device_id)
    if (results.count() == 0):
        # TODO: VALIDATE MAC_ADDRESS format

        result = DeviceAssignmentTable(
            device_id = device_id,
            car_id = car_id
        )
        db.session.add(result)
        db.session.commit()

        # TODO: ERROR HANDLING  
    else:
        print(f"MODIFY RECORD {results.first().device_id}")
        results.first().car_id = car_id
        db.session.commit()
        print("MODIFY RECORD COMPLETE")
    
    return jsonify({"message": "device_assignment_table updated"}), 200
# ------------------------------------------------------------
# /remove_run_table_record
# ------------------------------------------------------------
# Expected format:
#   [Content-Type: text/plain]
#   POST {{result_id}}
@app.route("/remove_run_table_record", methods=["POST"])
def remove_run_table_record():
    data = request.get_data(as_text=True)
    print(f"remove_run_table_record: {data}\n")
    if not data:
        return jsonify({"message": "No data provided"}), 

    result_id = data.strip()
    RunTable.query.filter_by(result_id = result_id).delete()
    db.session.commit()

    return jsonify({"message": "run_table updated"}), 200

# ------------------------------------------------------------
# /add_run_table_record
# ------------------------------------------------------------
# Expected format:
#   [Content-Type: text/plain]
#   POST {{car_id}},{{car_description}},{{car_owner}}
@app.route("/add_run_table_record", methods=["POST"])
def add_run_table_record():
    data = request.get_data(as_text=True)
    print(f"add_run_table_record: {data}\n")
    if not data:
        return jsonify({"message": "No data provided"}), 400
    
    values = data.split(",")
    print(values)
    result_id = values[0].strip()
    heat = values[1].strip()
    run = values[2].strip()
    driver_id = values[3].strip()
    car_id = values[4].strip()
    device_id = values[5].strip()
    gps_speed_timestamp = values[6].strip()
    gps_top_speed = values[7].strip()
    laser_speed_timestamp = values[8].strip()
    laser_top_speed = values[9].strip()
    top_speed = values[10].strip()
    datafile_path = values[11].strip() 

    print(f"QUERY FIRST in add operation")
    results = RunTable.query.filter_by(result_id = result_id)
    if (results.count() == 0):
        result = RunTable(
            result_id = result_id,
            heat = heat,
            run = run,
            driver_id = driver_id,
            car_id = car_id,
            device_id = device_id,
            gps_speed_timestamp = gps_speed_timestamp,
            gps_top_speed = gps_top_speed,
            laser_speed_timestamp = laser_speed_timestamp,
            laser_top_speed = laser_top_speed,
            top_speed = top_speed,
            datafile_path = datafile_path 
        )
        db.session.add(result)
        db.session.commit()
    else:
        print(f"MODIFY RECORD {results.first().result_id}")
        results.first().heat = heat
        results.first().run = run
        results.first().driver_id = driver_id
        results.first().car_id = car_id
        results.first().device_id = device_id
        results.first().gps_speed_timestamp = gps_speed_timestamp
        results.first().gps_top_speed = gps_top_speed
        results.first().laser_speed_timestamp = laser_speed_timestamp
        results.first().laser_top_speed = laser_top_speed
        results.first().top_speed = top_speed
        results.first().datafile_path = datafile_path
        db.session.commit()
        print("MODIFY RECORD COMPLETE")
    
    return jsonify({"message": "run_table updated"}), 200
# ------------------------------------------------------------
# /upload_run_result
# ------------------------------------------------------------
# Expected format:
#   [Content-Type: text/plain]
#   POST {{mac_address}},{{gps_top_speed}},{{gps_speed_timestamp}}
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
    mac_address = values[0].strip()
    gps_top_speed = float(values[1].strip())

    device_table_row = DeviceTable.query.filter(DeviceTable.mac_address == mac_address).first()
    if not device_table_row:
        return jsonify({"message": f"error, couldn't find device mac_address of '{mac_address}' in DeviceTable"}), 400
    
    device_id = device_table_row.device_id

    device_assignment_table_row = DeviceAssignmentTable.query.filter(DeviceAssignmentTable.device_id == device_id).first()
    if not device_assignment_table_row:
        return jsonify({"message": f"error, couldn't find device_id of '{device_id}' in DeviceAssignmentTable"}), 400

    car_id = device_assignment_table_row.car_id

    car_table_row = CarTable.query.filter(CarTable.car_id == car_id).first()
    if not car_table_row:
        return jsonify({"message": f"error, couldn't find car_id of '{car_id}' in CarTable"}), 400

    car_description = car_table_row.car_description

    #
    # TODO TODO TODO: need current heat number to disambiguate using
    #                 {heat, device_id, car_id} to lookup in run table!!!
    #
    run_table_row = RunTable.query.filter(
        (RunTable.device_id == device_id) and (RunTable.car_id == car_id)).first()
    if not run_table_row:
        return jsonify({"message": f"error, couldn't find device_id of '{device_id}' in RunTable"}), 400

    result_id = run_table_row.result_id
    driver_name = run_table_row.driver_name
    heat = run_table_row.heat
    run = run_table_row.run

    print("-------")
    print(f"mac_address: {mac_address}")
    print(f"gps_top_speed: {gps_top_speed}")
    print(f"device_id: {device_id}")
    print(f"car_id: {car_id}")
    print(f"car_description: {car_description}")
    print(f"result_id: {result_id}")
    print(f"driver_name: {driver_name}")
    print(f"heat: {heat}")
    print(f"run: {run}")
    print("-------")

    # Save the race result
    # result = RaceResult(
    #     device_id=device_id,
    #     name=name,
    #     car=car,
    #     run_number=run_number,
    #     top_speed=top_speed,
    # )
    # db.session.add(result)
    # db.session.commit()
    return jsonify({"message": "Data received"}), 200

# ------------------------------------------------------------
# main
# ------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
