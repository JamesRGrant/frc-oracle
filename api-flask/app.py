import os
from dotenv import load_dotenv
from flask import Flask,  request, jsonify
import requests
import base64
from kafka import KafkaConsumer


# Load the environment variables
load_dotenv()

# To encode... 1. encode as aceii 2. encode as base64 3. decode as ascii
frc_key = base64.b64encode(os.getenv("FRC_API").encode("ascii")).decode("ascii")

app = Flask(__name__)

# Import the API routes AFTER you create the app and key
import events


# Get the status of the FRC API
@app.route("/api/admin/status")
def admin_status():
    output = {}
     
    # Verify the FRC API is up
    response = requests.get('https://frc-api.firstinspires.org/v3.0/')
    if response.status_code == 200:
        output["frc_api"] = "ok"
    else:
        output["frc_api"] = "error: " + response.reason

    # Verify our FRC API Key is valid
    url = "https://frc-api.firstinspires.org/v3.0/2024/events"
    headers = {'Authorization': f'Basic {frc_key}'}
    response = requests.request("GET", url, headers=headers)
    if response.status_code == 200:
        output["frc_api_auth"] = "ok"
    else:
        output["frc_api_auth"] = "error: " + response.reason
    
    # Verify the Kafka server is up
    try:
        topic = 'match-results'
        consumer = KafkaConsumer(bootstrap_servers='localhost:9092')
        topics = consumer.topics()
        consumer.close()
        output["kafka"] = f'online but topic {topic} not found'
        for t in topics:
            if t == topic:
                output["kafka"] = "ok"
                break;
    except:
        output["kafka"] = "error: not connected"
    
    return jsonify(output)



if __name__ == "__main__":
    # Since we don't have a database, we are going to hard code the default events
    for e in ['WIMI', 'WILA']:
        events.load_event(2024, e)
    app.run(use_reloader=True, port=5001)