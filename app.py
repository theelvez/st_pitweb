from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/results')
def results():
    # For now, we'll just pass some dummy data to the template.
    # Later, you can replace this with real data from your database.
    data = [
        {'name': 'John Doe', 'car': 'Ford Mustang 2020', 'run_number': 1, 'top_speed': 120},
        {'name': 'Jane Doe', 'car': 'Chevrolet Camaro 2021', 'run_number': 2, 'top_speed': 115},
    ]
    return render_template('results.html', data=data)

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/upload_auto', methods=['POST'])
def upload_auto():
    data = request.get_json()  # Get JSON data sent in the request
    if not data:
        return jsonify({'message': 'No data provided'}), 400
    # Here, you would typically save the data to your database.
    # For now, we'll just print it to the console.
    print(data)
    return jsonify({'message': 'Data received'}), 200


if __name__ == '__main__':
    app.run(debug=True)
