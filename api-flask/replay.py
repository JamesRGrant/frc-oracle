from __main__ import app, frc_key
from flask import request, jsonify
import requests
from kafka import KafkaProducer
import json

@app.route("/api/events/<event_id>/replay", methods = [ 'POST'])
def route_replay(event_id):  
    event_id = event_id.upper()
    year = event_id[0:4]
    event = event_id[4:]

    try:
        # Setup the Kafka Producer
        producer = KafkaProducer(bootstrap_servers='localhost:9092')

        # Get the results from the FRC API
        url = f'https://frc-api.firstinspires.org/v3.0/{year}/matches/{event}'
        headers = {'Authorization': f'Basic {frc_key}'}
        params = {}
        params['tournamentLevel'] = 'Qualification'
        response = requests.request("GET", url, headers=headers,params=params)
        if response.status_code == 200:
            for match in response.json()['Matches']:
                id = match['matchNumber']
                redScore = match['scoreRedFinal']
                blueScore = match['scoreBlueFinal']
                red = {}
                red['win'] = 1 if redScore > blueScore else 0
                red['tie'] = 1 if redScore == blueScore else 0
                red['score'] = redScore
                blue = {}
                blue['win'] = 1 if blueScore > redScore else 0
                blue['tie'] = 1 if blueScore == redScore else 0
                blue['score'] = blueScore
                results = {'event': event_id, 'match_id': id, 'red': red, 'blue': blue}

                # Send the results to Kafka
                producer.send('match-results', key=event_id.encode('utf-8'), value=json.dumps(results).encode('utf-8'))

            # Clean up Kafka
            producer.flush()
            producer.close()
            return jsonify({'success': 'Matches sent to Kafka'}), 200
        else:
            # Clean up Kafka
            producer.flush()
            producer.close()
            return jsonify({'error': 'FRC API is down'}), 503

    except Exception as e:
        return jsonify({'error': str(e)}), 503
