import os, sys, logging
from dotenv import load_dotenv
from flask import Flask,  request, jsonify
from flask_cors import CORS, cross_origin
import requests
import base64
from kafka import KafkaConsumer
import util

# Start the logger to output to the console.  Use INFO for normal release, DEBUG to see data packets
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s|%(levelname)-8s|%(message)s')

# Load the environment variables
load_dotenv()

# To encode... 1. encode as aceii 2. encode as base64 3. decode as ascii
frc_key = base64.b64encode(os.getenv("FRC_API").encode("ascii")).decode("ascii")

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# Import the API routes AFTER you create the app and key
import events
import replay


# Get the status of the FRC API
@app.route("/api/admin/status")
@util.log_stats
def admin_status():
    resp = util.check_auth(request.headers)
    if resp[1] != 200:
        return resp
    
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

    # Display call statistics
    output["calls"] = util.calls  
    
    return jsonify(output)



if __name__ == "__main__":
    # Since we don't have a database, we are going to hard code the default events
    for e in ['WIMI', 'WILA']:
        events.load_event(2024, e)
    app.run(use_reloader=True, port=5001)