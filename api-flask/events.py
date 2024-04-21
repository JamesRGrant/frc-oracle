from __main__ import app, frc_key
from matches import load_matches
from flask import request, jsonify
import requests

# This is our in memory cache
g_events = {'Events': []}

@app.route("/api/events")
def route_events():  
    return jsonify(g_events)

@app.route("/api/events/<event_id>", methods = ['GET', 'PUT', 'POST', 'DELETE'])
def route_event(event_id):  
    # Mixed case will not match
    event_id = event_id.upper()

    if request.method == 'GET':
        for e in g_events['Events']:
            if e['id'] == event_id:
                print(e['id'])
                return jsonify(e)
            
        return jsonify({'error': f'Event {event_id} not found, key is YEARCODE.  Ex: 2024WIMI  Use Post to add an event'}), 404
    
    if request.method == 'PUT':
        """create or recreate the event"""
        year = event_id[0:4]
        code = event_id[4:]
        load_event(year, code)
        for e in g_events['Events']:
            if e['id'] == event_id:
                return jsonify(e)
        
        # If we failed it must not be a real event, return Bad Request
        return jsonify({'error': 'Event not valid, key is YEARCODE.  Ex: 2024WIMI'}), 400
            


    if request.method == 'POST':
        """modify/update """
        # We don't have a reason to update the event right now
        return jsonify({'error': 'Method Not Allowed'}), 405

    if request.method == 'DELETE':
        """delete user with ID <user_id>"""
        remove = None
        for e in g_events['Events']:
            if e['id'] == event_id:
                remove = e
                break
        
        if remove is not None:
            g_events['Events'].remove(remove)
            return jsonify({'success': 'Event Removed'}), 200
        else:
            return jsonify({'error': 'Event not found, key is YEARCODE.  Ex: 2024WIMI'}), 404

    else:
        return jsonify({'error': 'Method Not Allowed'}), 405

def load_event(year, code):
    global g_events
    # Get the Event Name
    url = f'https://frc-api.firstinspires.org/v3.0/{year}/events'
    headers = {'Authorization': f'Basic {frc_key}'}
    params = {}
    params['eventCode'] = code
    response = requests.request("GET", url, headers=headers,params=params)
    if response.status_code == 200:
        first = response.json()['Events'][0]
        e = {'id': str(year) + first['code'], 'name': first['name']}
        g_events['Events'].append(e)

        load_matches(year, code)