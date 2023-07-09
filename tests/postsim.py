import csv
import json
import requests
import time


def format_data_to_json(row):
    # Format the CSV row into a JSON object
    data = {
        'name': row[0],
        'car': row[1],
        'run_number': int(row[2]),
        'top_speed': float(row[3])
    }
    return json.dumps(data)


def make_post_request(json_data):
    # Make an HTTP POST request to the server
    url = 'https://pitweb.azurewebsites.net/upload_auto'  # Replace with the actual URL
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json_data, headers=headers)
    
    if response.status_code == 200:
        print('POST request successful')
    elif response.status_code == 400:
        error_message = response.json().get('error')  # Assuming the server returns the error message as JSON
        print(f'POST request failed. Status Code: 400. Error Message: {error_message}')
    else:
        print(f'POST request failed. Status Code: {response.status_code}')


def process_csv_file(file_path, wait_time):
    with open(file_path, 'r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip the header row

        for row in csv_reader:
            json_data = format_data_to_json(row)
            make_post_request(json_data)
            time.sleep(wait_time)


if __name__ == '__main__':
    file_path = 'dummydata.csv'
    seconds = 5  # Replace with the desired number of seconds to wait
    process_csv_file(file_path, seconds)
