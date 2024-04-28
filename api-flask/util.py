from functools import wraps
from flask import request
from flask_dance.contrib.google import make_google_blueprint, google
import logging, os

# Global variable to store call statistics
calls = {}

def log_stats(f):
    """Records call statistics for each API route."""
    @wraps(f)
    def decorated(*args, **kwargs):
        path = f.__name__ + ":" + request.method
        logging.info(f'API Call: {path}')

        global calls
        if path not in calls:
            calls[path] = 0
        calls[path] += 1

        return f(*args, **kwargs)
    return decorated

def check_auth(headers):
    """Checks the Authorization header for a valid API key."""
    if 'Authorization' in headers:
        logging.info(f'Authorization: {request.headers["Authorization"]}')
        args = request.headers['Authorization'].split(' ')
        if len(args) != 2 or args[0] != 'Bearer':
            return {'error': 'Unauthorized, requires Bearer auth header and token'}, 401

        if os.getenv('SECRET_KEY') != args[1]:
            return {'error': 'Unauthorized, invalid token'}, 401

        return {}, 200
    return {'error': 'Unauthorized, requires Bearer auth header and token'}, 401
