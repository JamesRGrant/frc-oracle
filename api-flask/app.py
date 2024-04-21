import os
from dotenv import load_dotenv
from flask import Flask,  request, jsonify
import requests
import base64

load_dotenv()
# To encode... 1. encode as aceii 2. encode as base64 3. decode as ascii
frc_key = base64.b64encode(os.getenv("FRC_API").encode("ascii")).decode("ascii")
app = Flask(__name__)

@app.route("/api/events")
def events():
    my_events = ['WIMI', 'WILA']  
    events = {}
    events['Events'] = []

    # WILA WIMI
    url = "https://frc-api.firstinspires.org/v3.0/2024/events"
    headers = {'Authorization': f'Basic {frc_key}'}
    params = {}

    for my_event in my_events:
        params['eventCode'] = my_event
        response = requests.request("GET", url, headers=headers,params=params)
        first = response.json()['Events'][0]
        e = {'id': '2024' + first['code'], 'name': first['name']}
        events['Events'].append(e)
    
    return jsonify(events)

@app.route("/api/admin/status")
def admin_status():
    output = {}
     
    response = requests.get('https://frc-api.firstinspires.org/v3.0/')
    if response.status_code == 200:
        output["frc_api"] = "ok"
    else:
        output["frc_api"] = "error" + response.text
    
    return jsonify(output)

if __name__ == "__main__":
    app.run(use_reloader=True, port=5001)