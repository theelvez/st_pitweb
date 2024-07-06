from flask import Flask, render_template, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from flask_sse import sse
from sqlalchemy import desc, distinct, or_
from time import sleep, ctime, time
from threading import Event
import csv

app = Flask(__name__)

db_update_event = Event()

# SQLite database configuration
DB_NAME = "SVTdF-2024.sqlite"  # Replace with your SQLite database file name

# Create the SQLite connection URL
DB_CONNECTION_URL = f"sqlite:///{DB_NAME}"

# Set the SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_DATABASE_URI"] = DB_CONNECTION_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db = SQLAlchemy(app)

runs_per_heat = 8

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
    def __repr__(self):
        return f"<Driver {self.driver_id} {self.driver_name} {self.run_count}>"

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
    
class ExtendedResultsTable(db.Model):
    __tablename__ = 'extended_results_table'
    result_id = db.Column(db.Integer, primary_key=True)
    time_to_60 = db.Column(db.Float, nullable=False)
    time_to_100 = db.Column(db.Float, nullable=False)
    time_to_150 = db.Column(db.Float, nullable=False)
    time_to_200 = db.Column(db.Float, nullable=False)
    time_to_top_speed = db.Column(db.Float, nullable=False)
    speed_at_finish = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<ExtendedResult {self.result_id}>"
    
class UnscheduledDriver:
    def __init__(self, driver_id, driver_name, scheduled_run_count, paid_run_count):
        self.driver_id = driver_id
        self.driver_name = driver_name
        self.scheduled_run_count = scheduled_run_count
        self.paid_run_count = paid_run_count
    def __repr__(self):
        return f"<({self.driver_id}) {self.driver_name} s:{self.scheduled_run_count} p:{self.paid_run_count}>"

# ------------------------------------------------------------
# /
# ------------------------------------------------------------
@app.route("/")
def home():
    return render_template("home.html")

def find_unscheduled_drivers():
    unscheduled_drivers = []

    drivers = DriverTable.query.all()
    for driver in drivers:
        num_runs_scheduled = RunTable.query.filter_by(driver_id = driver.driver_id).count()
        num_runs_paid = driver.run_count
        if (num_runs_paid != num_runs_scheduled):
            new_entry = UnscheduledDriver(
                driver_id = driver.driver_id,
                driver_name = driver.driver_name,
                scheduled_run_count = num_runs_scheduled,
                paid_run_count = num_runs_paid
            )
            unscheduled_drivers.append(new_entry)
    return unscheduled_drivers

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
        RunTable.result_id,
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
    
    cars = CarTable.query.order_by(CarTable.car_description).join(
        DeviceAssignmentTable, CarTable.car_id == DeviceAssignmentTable.car_id
    ).with_entities(
        CarTable.car_id,
        CarTable.car_description,
        DeviceAssignmentTable.car_id.label('device_in_car')
    )

    unscheduled_drivers = find_unscheduled_drivers()

    next_result_id = 1
    for run in RunTable.query.all():
        next_result_id = max(next_result_id, run.result_id)

    next_result_id += 1

    return render_template(
        "schedule.html",
        schedule = schedule.all(),
        cars = cars.all(),
        unscheduled_drivers = unscheduled_drivers,
        next_result_id = next_result_id
        )

# ------------------------------------------------------------
# /raw-tables
# ------------------------------------------------------------
@app.route("/raw-tables")
def raw_tables():
    print("raw_tables:\n")
    devices = (
        DeviceTable.query.order_by(DeviceTable.device_id)
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
        RunTable.query.order_by(RunTable.heat, RunTable.run)
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
    extended_results = (
        ExtendedResultsTable.query
        .with_entities(
            ExtendedResultsTable.result_id,
            ExtendedResultsTable.time_to_60,
            ExtendedResultsTable.time_to_100,
            ExtendedResultsTable.time_to_150,
            ExtendedResultsTable.time_to_200,
            ExtendedResultsTable.time_to_top_speed,
            ExtendedResultsTable.speed_at_finish,
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
        extended_results=extended_results,
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

    db_update_event.set()
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
    
    db_update_event.set()
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

    db_update_event.set()
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
    
    db_update_event.set()
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

    db_update_event.set()
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
    
    db_update_event.set()
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

    db_update_event.set()
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
    
    db_update_event.set()
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

    db_update_event.set()
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
            heat = 999,
            run = 888,
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
        result_id = results.first().result_id
        print(f"MODIFY RECORD {result_id}")
        results.first().heat = 999
        results.first().run = 888
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
    
    do_move_run_to(result_id, heat, run)

    db_update_event.set()
    return jsonify({"message": "run_table updated"}), 200
# ------------------------------------------------------------
# /remove_extended_results_table_record
# ------------------------------------------------------------
# Expected format:
#   [Content-Type: text/plain]
#   POST {{result_id}}
@app.route("/remove_extended_results_table_record", methods=["POST"])
def remove_extended_results_table_record():
    data = request.get_data(as_text=True)
    print(f"remove_extended_results_table_record: {data}\n")
    if not data:
        return jsonify({"message": "No data provided"}), 

    result_id = data.strip()
    ExtendedResultsTable.query.filter_by(result_id = result_id).delete()
    db.session.commit()
    db_update_event.set()

    return jsonify({"message": "extended_results_table updated"}), 200

# ------------------------------------------------------------
# /add_extended_results_table_record
# ------------------------------------------------------------
# Expected format:
#   [Content-Type: text/plain]
#   POST {{result_id}},{{time_to_60}},{{time_to_100}},{{time_to_150}},{{time_to_200}},{{time_to_top_speed}},{{speed_at_finish}}
@app.route("/add_extended_results_table_record", methods=["POST"])
def add_extended_results_table_record():
    data = request.get_data(as_text=True)
    print(f"add_extended_results_table_record: {data}\n")
    if not data:
        return jsonify({"message": "No data provided"}), 400
    
    values = data.split(",")
    print(values)

    result_id = values[0].strip()
    time_to_60 = values[1].strip()
    time_to_100 = values[2].strip()
    time_to_150 = values[3].strip()
    time_to_200 = values[4].strip()
    time_to_top_speed = values[5].strip()
    speed_at_finish = values[6].strip()

    results = ExtendedResultsTable.query.filter_by(result_id = result_id)
    if (results.count() == 0):
        result = ExtendedResultsTable(
            result_id = result_id,
            time_to_60 = time_to_60,
            time_to_100 = time_to_100,
            time_to_150 = time_to_150,
            time_to_200 = time_to_200,
            time_to_top_speed = time_to_top_speed,
            speed_at_finish = speed_at_finish,
        )
        db.session.add(result)
        db.session.commit()
    else:
        print(f"MODIFY RECORD {results.first().result_id}")
        results.first().time_to_60 = time_to_60
        results.first().time_to_100 = time_to_100
        results.first().time_to_150 = time_to_150
        results.first().time_to_200 = time_to_200
        results.first().time_to_top_speed = time_to_top_speed
        results.first().speed_at_finish = speed_at_finish
        db.session.commit()
        print("MODIFY RECORD COMPLETE")
    
    db_update_event.set()
    return jsonify({"message": "extended_results_table updated"}), 200
# ------------------------------------------------------------
# /empty_run_table
# ------------------------------------------------------------
# Expected format:
#   [Content-Type: text/plain]
#   POST 
# @app.route("/empty_run_table", methods=["POST"])
# def empty_run_table():
#     print("EMPTY RUN TABLE")
#     RunTable.query.delete()
#     db.session.commit()
#     db_update_event.set()
#     return jsonify({"message": "run table emptied"}), 200

@app.route("/empty_run_table", methods=["POST"])
def empty_run_table():
    #
    # DELETE run_table and device_assignment_table
    #
    RunTable.query.delete()
    DeviceAssignmentTable.query.delete()
    db.session.commit()

    #
    # VALIDATE that we have sentiel values and add them, if they don't exist
    #
    if CarTable.query.filter_by(car_id = 0).count() <= 0:
        db.session.add(CarTable(car_id = 0, car_description = "UNKNOWN", car_owner = "None"))

    if DriverTable.query.filter_by(driver_id = 0).count() <= 0:
        db.session.add(DriverTable(driver_id = 0, driver_name = "UNKNOWN", run_count = 0))

    if DeviceTable.query.filter_by(device_id = 0).count() <= 0:
        db.session.add(DeviceTable(mac_address = "UNKNOWN", device_id = 0))

    db.session.commit()
    
    #
    # Car -> Device mapping: start with car_id == device_id
    # 
    cars = CarTable.query.all()
    for car in cars:
        db.session.add(DeviceAssignmentTable(car_id = car.car_id, device_id = car.car_id))
    
    db.session.commit()
    db_update_event.set()
    return jsonify({"message": "run table emptied"}), 200

def find_next_available_heat(driver_id, car_id, next_unfull_heat, max_heat):
    next_run = 1
    heat = next_unfull_heat[0] # passed as the fist element of an array so it's by-reference
    while heat <= max_heat:
        next_run = RunTable.query.filter_by(heat = heat).count() + 1
        if next_run <= runs_per_heat:
            if RunTable.query.filter(RunTable.heat == heat, or_(RunTable.driver_id == driver_id, RunTable.car_id == car_id)).count() > 0:
                heat += 1
                continue
            else: 
                break
        else:
            # heat filled up, remember this 
            next_unfull_heat[0] = next_unfull_heat[0] + 1
            heat += 1

    return heat, next_run

# ------------------------------------------------------------
# /populate_run_table
# ------------------------------------------------------------
# Expected format:
#   [Content-Type: text/plain]
#   POST 
@app.route("/populate_run_table", methods=["POST"])
def populate_run_table():
    #
    # Runs
    #   Give drivers one entry per run using their owned car as the car, unless they have more than one car
    #   Device id == car id
    #
    result_id = RunTable.query.order_by(desc(RunTable.result_id)).first().result_id + 1
    gps_speed_timestamp = "--"
    gps_top_speed = 0.0
    laser_speed_timestamp = "--"
    laser_top_speed = 0.0
    top_speed = 0.0
    datafile_path = "--"
    drivers = DriverTable.query.order_by(desc(DriverTable.run_count), DriverTable.driver_id).all()

    total_run_count = 0
    for driver in drivers:
        total_run_count += driver.run_count

    max_heat = int(total_run_count / runs_per_heat) + 1

    print("------------------------")
    print(f"scheduling {total_run_count} runs in {max_heat} heats")

    unscheduled_drivers = find_unscheduled_drivers()

    next_unfull_heat = [ 1 ]
    for driver in unscheduled_drivers:
        driver_run_count = driver.paid_run_count - driver.scheduled_run_count
        driver_name = driver.driver_name
        driver_id = driver.driver_id
        print(f"....driver {driver_name} gets {driver_run_count} more runs")
        matching_cars = CarTable.query.filter(CarTable.car_owner == driver_name).all()
        print(f"....found {len(matching_cars)} matching cars")
        car_id = 0
        if (len(matching_cars) == 1):
            car_id = matching_cars[0].car_id

        for index in range(driver_run_count):
            heat, run = find_next_available_heat(driver_id, car_id, next_unfull_heat, max_heat)

            new_record = RunTable(
                result_id = result_id,
                heat = heat,
                run = run,
                driver_id = driver_id,
                car_id = car_id,
                device_id = car_id,
                gps_speed_timestamp = gps_speed_timestamp,
                gps_top_speed = gps_top_speed,
                laser_speed_timestamp = laser_speed_timestamp,
                laser_top_speed = laser_top_speed,
                top_speed = top_speed,
                datafile_path = datafile_path
            )
            result_id += 1
            db.session.add(new_record)
    print("------------------------")
    db.session.commit()
    db_update_event.set()
    return jsonify({"message": "run table populated"}), 200

def renumber_runs_in_heat(heat):
    runs = RunTable.query.filter(RunTable.heat == heat).order_by(RunTable.run).all()
    run_number = 1
    for run in runs:
        run.run = run_number
        run_number += 1
    return

def do_move_run_to(result_id, to_heat, to_run):

    if (to_run == "0" and to_heat == "0"):
        run_to_delete = RunTable.query.filter(RunTable.result_id == result_id)
        from_heat = run_to_delete.first().heat
        run_to_delete.delete()
        db.session.commit()
        renumber_runs_in_heat(from_heat)
        db.session.commit()
        return "run removed"

    # make room for the run in the to_heat
    to_runs = RunTable.query.filter(RunTable.heat == to_heat).order_by(RunTable.run).all()
    run_number = 1
    for run in to_runs:
        if run_number >= int(to_run):
            run.run = run_number + 1
        run_number += 1
    db.session.commit()

    run_to_modify = RunTable.query.filter(RunTable.result_id == result_id).first()
    from_heat = run_to_modify.heat
    run_to_modify.heat = to_heat
    run_to_modify.run = to_run

    db.session.commit()

    # renumber the runs in from_heat and to_heat
    renumber_runs_in_heat(from_heat)
    renumber_runs_in_heat(to_heat)
    db.session.commit()
    db_update_event.set()
    return f"run {result_id} moved to {to_heat}-{to_run}"


# ------------------------------------------------------------
# /move_run_from_to
# ------------------------------------------------------------
# Expected format:
#   [Content-Type: text/plain]
#   POST result_id,to_heat,to_run
@app.route("/move_run_from_to", methods=["POST"])
def move_run_from_to():
    print("move_run_from_to: ")
    data = request.get_data(as_text=True)
    print(data)
    print("\n")
    if not data:
        return jsonify({"message": "No data provided"}), 400
    
    values = data.split(",")
    print(values)
    # Save the data to the database
    result_id = values[0].strip()
    to_heat = values[1].strip()
    to_run = values[2].strip()

    message = do_move_run_to(result_id, to_heat, to_run)

    db_update_event.set()
    print(message)
    return jsonify({"message": message}), 200


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
    car_id = run_table_row.car_id
    heat = run_table_row.heat
    run = run_table_row.run

    run_table_row.gps_top_speed = gps_top_speed
    run_table_row.top_speed = gps_top_speed
    db.session.commit()

    print("-------")
    print(f"mac_address: {mac_address}")
    print(f"gps_top_speed: {gps_top_speed}")
    print(f"device_id: {device_id}")
    print(f"car_id: {car_id}")
    print(f"car_description: {car_description}")
    print(f"result_id: {result_id}")
    print(f"car_id: {car_id}")
    print(f"heat: {heat}")
    print(f"run: {run}")
    print("-------")

    db_update_event.set()

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


def get_message():
    '''this could be any function that blocks until data is ready'''
    db_update_event.wait()
    db_update_event.clear()
    s = ctime(time())
    return s

@app.route('/stream')
def stream():
    def eventStream():
        while True:
            # wait for source data to be available, then push it
            yield 'data: {}\n\n'.format(get_message())
    return Response(eventStream(), mimetype="text/event-stream")


# ------------------------------------------------------------
# main
# ------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True, threaded=True)
