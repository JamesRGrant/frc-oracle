import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
from flask_dance.contrib.google import make_google_blueprint, google
import requests

load_dotenv()
app = Flask(__name__)
client_id = os.getenv("GOOGLE_CLIENT_ID")
client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
app.secret_key = os.getenv("SECRET_KEY")
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
# For local only!!
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

bp = make_google_blueprint(client_id=client_id, client_secret=client_secret, reprompt_consent=True, scope=["email"], offline=True)
app.register_blueprint(bp, url_prefix="/login")

@app.route("/")
def index():
    google_data = None
    
    if google.authorized:
        try: 
            google_data = google.get("/oauth2/v2/userinfo").json()
            print(google_data)
        except:
            # Token expired log in again
            return redirect(url_for("google.login"))
        
    
    # Get the events we have indexed
    url = "http://localhost:5001/api/events"
    resp = requests.get(url)
    if resp.status_code == 200:
        events = resp.json()
    
    
    return render_template("index.j2", events=events, google_data=google_data, fetch_url = google.base_url + "/oauth2/v2/userinfo")

@app.route("/event/<id>")
def event(id):
    event_name = ''
    matches = {}

    # Get the event name
    url = "http://localhost:5001/api/events/" + id
    resp = requests.get(url)
    if resp.status_code == 200:
        event_name = resp.json()['name']

    # Get the matches
    url = "http://localhost:5001/api/events/" + id + "/matches"
    resp = requests.get(url)
    if resp.status_code == 200:
            matches = resp.json()

    # Calculate the accuracy
    final_guess_accuracy , all_guesses_accuracy = calculate_accuracy(matches)

    return render_template("event.j2", title=event_name, matches=matches, final_guess_accuracy = final_guess_accuracy, all_guesses_accuracy = all_guesses_accuracy, fetch_url = google.base_url + "/oauth2/v2/userinfo")

@app.route("/login")
def login():
    return redirect(url_for("google.email"))

@app.route("/logout")
def logout():
    google_data = None
    return render_template("index.j2", google_data=google_data, fetch_url = google.base_url + "/oauth2/v2/userinfo")

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
                # Don't handle ties yet
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

    return final_guess_accuracy, all_guesses_accuracy


if __name__ == "__main__":
    app.run(use_reloader=True)