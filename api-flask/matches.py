from __main__ import app, frc_key
from flask import request, jsonify
import requests

# This is our in memory cache
g_matches = {}

@app.route("/api/events/<event_id>/matches")
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

