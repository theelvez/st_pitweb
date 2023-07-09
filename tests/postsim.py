import csv
import json
import requests
import time


def format_data_to_json(row):
    # Format the CSV row into a JSON object
    data = {
        'Name': row[0],
        'Car': row[1],
        'Run Number': int(row[2]),
        'Top Speed': float(row[3])
    }
    return json.dumps(data)


def make_post_request(json_data):
    # Make an HTTP POST request to the server
    url = 'https://pitweb.azurewebsites.net/upload'  # Replace with the actual URL
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json_data, headers=headers)
    if response.status_code == 200:
        print('POST request successful')
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
    seconds = 30 # Replace with the desired number of seconds to wait
    process_csv_file(file_path, seconds)
