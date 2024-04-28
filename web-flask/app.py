import os, sys, logging
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
from flask_dance.contrib.google import make_google_blueprint, google
import requests


# Start the logger to output to the console.  Use INFO for normal release, DEBUG to see data packets
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s|%(levelname)-8s|%(message)s')

# This function loads requested environment variables (input array) into a dictionary and bails if not available
def load_env(env_vars):
    env_dict = {}
    for var in env_vars:
        env_dict[var] = os.getenv(var)
        logging.debug("Environment variable " + var + " = " + str(env_dict[var]))
        if env_dict[var] == None:
            logging.error("Environment variable " + var + " not set.  Exiting.")
            sys.exit(1)
    return env_dict

# Load from the .env file
load_dotenv()
logging.info("Loading environment variables from .env file.")

env = load_env(["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "SECRET_KEY", "OAUTHLIB_RELAX_TOKEN_SCOPE", "OAUTHLIB_INSECURE_TRANSPORT"])

# Create the flask app with Google Auth
app = Flask(__name__)
app.secret_key = env['SECRET_KEY']

# These two remove all the extra whitespace from script in the templates
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True
bp = make_google_blueprint(client_id=env['GOOGLE_CLIENT_ID'], client_secret=env['GOOGLE_CLIENT_SECRET'], reprompt_consent=True, scope=["email"], offline=True)
app.register_blueprint(bp, url_prefix="/login")


# This is the main page.  If the user is not logged in, it will show a login link.  
# If the user is logged in, it will show the user's email address and links to the Events
@app.route("/")
def index():
    # If not authorized, render the page with a login link by passing no data
    if not google.authorized:
        logging.info("Google not authorized")
        return render_template("index.j2")
    
    # Get the user data from Google to pass to the template
    try: 
        resp = google.get("/oauth2/v2/userinfo")
        if resp.status_code != 200:
            logging.info("Could not get google user info." + resp.text)
            return redirect(url_for("google.login"))
        google_data = resp.json()
        logging.debug(google_data)
    except:
        # Token expired log in again
        return redirect(url_for("google.login"))
    
    # Get the events we have indexed
    resp = requests.get('http://localhost:5001/api/events')
    if resp.status_code == 200:
        events = resp.json()
        logging.debug(events)
    
    return render_template("index.j2", events=events, google_data=google_data)


@app.route("/event/<id>")
def event(id):
    if not google.authorized:
        logging.info("Google not authorized")
        return render_template("index.j2")

    event_name = ''
    matches = {}

    # Get the event name
    url = "http://localhost:5001/api/events/" + id
    resp = requests.get(url)
    if resp.status_code == 200:
        event_name = resp.json()['name']
        logging.debug(f'Event name: {event_name}')
    else:
        event_name = 'Event invalid or not indexed'
        logging.error(f'Error getting event name: {resp.text}')

    # Get the matches
    url = "http://localhost:5001/api/events/" + id + "/matches"
    resp = requests.get(url)
    if resp.status_code == 200:
        matches = resp.json()
        logging.debug(f'Matches count: {matches.__len__()}')
    else:
        logging.error(f'Error getting matches: {resp.text}')
    
    # Calculate the accuracy, if there are no matches it will be 'TBD'
    final_guess_accuracy , all_guesses_accuracy = calculate_accuracy(matches)

    logging.info(f"Viewing {event_name} ({id}) with {matches.__len__()} matches.")

    return render_template("event.j2", title=event_name, matches=matches, final_guess_accuracy = final_guess_accuracy, all_guesses_accuracy = all_guesses_accuracy)

@app.route("/login")
def login():
    return redirect(url_for("google.login"))

@app.route("/logout")
def logout():
    try:
        # This will fail if you try it twice (if you are logged out and someone refreshes the logout page)
        del bp.token  # Delete OAuth token from storage
    finally:
        return render_template("index.j2")

def calculate_accuracy(matches):
    final_correct = 0
    final_total = 0
    all_correct = 0
    all_total = 0

    for id in matches:
        match = matches[id]
        if 'results' in match and 'predictions' in match:
            if match['results']['red']['win'] == 1:
                pred = match['predictions'][0]['red']['win']
            elif match['results']['blue']['win'] == 1:
                pred = match['predictions'][0]['blue']['win']
            else:
                logging.warning(f"Match {id} has no winner, unhandled case")
                break
            if pred[-1] == 1:
                final_correct += 1
            final_total += 1
            for x in pred:
                if x == 1:
                    all_correct += 1
                all_total += 1
    
    if final_total > 0:
        final_guess_accuracy = '{:0.2f}%'.format(final_correct / final_total * 100.0) 
        all_guesses_accuracy = '{:0.2f}%'.format(all_correct / all_total * 100.0)
    else:
        final_guess_accuracy = "TBD"
        all_guesses_accuracy = "TBD"

    logging.debug(f"Final guess accuracy: {final_guess_accuracy}, All guesses accuracy: {all_guesses_accuracy}")

    return final_guess_accuracy, all_guesses_accuracy


if __name__ == "__main__":
    app.run(use_reloader=True)