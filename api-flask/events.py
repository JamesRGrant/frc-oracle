from app import app, frc_key
from matches import load_matches
from flask import request, jsonify
from flask_cors import cross_origin
import requests
import util
import logging

# This is our in memory cache
g_events = {'Events': []}

@app.route("/api/events")
@util.log_stats
def route_events():  
    return jsonify(g_events)

@app.route("/api/events/<event_id>", methods = ['GET', 'PUT', 'POST', 'DELETE', 'OPTIONS'])
@cross_origin()
@util.log_stats
def route_event(event_id):  
    # Mixed case will not match
    event_id = event_id.upper()
    global g_events

    if request.method == 'GET':
        for e in g_events['Events']:
            if e['id'] == event_id:
                print(e['id'])
                return jsonify(e)
            
        return jsonify({'error': f'Event {event_id} not found, key is YEARCODE.  Ex: 2024WIMI  Use Post to add an event'}), 404
    
    if request.method == 'PUT':
        """create or recreate the event"""

        # Delete it if it exists
        print(f'Deleting event {event_id}')
        g_events.pop(event_id, None)

        year = event_id[0:4]
        code = event_id[4:]
        load_event(year, code)
        for e in g_events['Events']:
            if e['id'] == event_id:
                response = jsonify(e)
                response.headers.add('Access-Control-Allow-Origin', '*')
                response.headers.add('Access-Control-Allow-Credentials', 'True')
                response.headers.add('Access-Control-Allow-Methods', 'PUT, OPTIONS')
                response.headers.add('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, X-Auth-Token')
                return response
        
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
        response = jsonify({'error': 'Method Not Allowed'}), 405
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Credentials', 'True')
        response.headers.add('Access-Control-Allow-Methods', 'PUT, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, X-Auth-Token')
        return response

def load_event(year, code):
    code = code.upper()

    global g_events
    # Get the Event Name
    url = f'https://frc-api.firstinspires.org/v3.0/{year}/events'
    headers = {'Authorization': f'Basic {frc_key}'}
    params = {}
    params['eventCode'] = code
    response = requests.request("GET", url, headers=headers,params=params)
    if response.status_code == 200:
        events = response.json()['Events']
        logging.info(f'Loading event {year}{code}, FRC returned {len(events)} events')
        for event in events:
            if event['code'] == code:
                e = {'id': str(year) + code, 'name': event['name']}
                logging.info(f'Adding event {e}')
                g_events['Events'].append(e)
                break

        load_matches(year, code)