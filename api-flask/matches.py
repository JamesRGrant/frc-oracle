from app import app, frc_key
from flask import request, jsonify
import requests
import util

# This is our in memory cache
g_matches = {}

@app.route("/api/events/<event_id>/matches")
@util.log_stats
def route_matches(event_id):  
    event_id = event_id.upper()
    return jsonify(g_matches[event_id])

def load_matches(year, event):
    global g_matches

    new_matches = {}
    url = f'https://frc-api.firstinspires.org/v3.0/{year}/schedule/{event}'
    headers = {'Authorization': f'Basic {frc_key}'}
    params = {}
    params['tournamentLevel'] = 'Qualification'
    response = requests.request("GET", url, headers=headers,params=params)
    if response.status_code == 200:
        schedule = response.json()['Schedule']
        for match in schedule:
            id = match['matchNumber']
            name = match['description'] 
            red = []
            blue = []
            
            # This may be a problem if their JSON is out of order, the positions might be mixed up
            for team in match['teams']:
                if team['station'][0:3] == 'Red':
                    red.append(team['teamNumber'])
                else:
                    blue.append(team['teamNumber'])

            m = { 'name': name, 'teams': {'red': red, 'blue': blue}}
            new_matches[id] = m

    g_matches[str(year) + event] = new_matches


@app.route("/api/events/<event_id>/matches/<match_id>", methods=['PATCH'])
@util.log_stats
def route_match(event_id, match_id):  
    event_id = event_id.upper()

    match_id = int(match_id)

    global g_matches

    if request.method == 'PATCH':
        matches = g_matches[event_id]
        if matches is None:
            return jsonify({'error': f'Event {event_id} not found, key is YEARCODE.  Ex: 2024WIMI  Use Post to add an event'}), 404

        match = matches[match_id]
        if match is None:
            return jsonify({'error': f'Match {event_id}:{match_id} not found'}), 404

        data = request.get_json()
        if 'results' in data:
            match['results'] = data['results']
        elif 'algorithm' in data:
            algo = data['algorithm']
            red_win = data['red']['win']
            blue_win = data['blue']['win'] 

            if 'predictions' not in match:
                match['predictions'] = [{'algorithm': algo, 'red': {'win': [red_win]}, 'blue': {'win': [blue_win]}}]
            else:
                match['predictions'][0]['red']['win'].append(red_win)
                match['predictions'][0]['blue']['win'].append(blue_win)

        return 'Match was patched with new data.', 200
    else:
        return jsonify({'error': 'Method Not Allowed'}), 405
    
    