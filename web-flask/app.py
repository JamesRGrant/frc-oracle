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
        
        
    url = "http://localhost:5001/api/events"
    resp = requests.get(url)
    if resp.status_code == 200:
        events = resp.json()
    
    
    return render_template("index.j2", events=events, google_data=google_data, fetch_url = google.base_url + "/oauth2/v2/userinfo")

@app.route("/login")
def login():
    return redirect(url_for("google.email"))

@app.route("/logout")
def logout():
    google_data = None
    return render_template("index.j2", google_data=google_data, fetch_url = google.base_url + "/oauth2/v2/userinfo")


if __name__ == "__main__":
    app.run(use_reloader=True)