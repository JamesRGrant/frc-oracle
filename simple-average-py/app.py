import os, sys, logging
from dotenv import load_dotenv
import requests, json
from kafka import KafkaConsumer
from time import sleep
import logging

# Start the logger to output to the console.  Use INFO for normal release, DEBUG to see data packets
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s|%(levelname)-8s|%(message)s')

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

def get_team_scores(event_id, match_id, red_score, blue_score):
    team_scores = {}
    future_matches = {}
    these_teams = []

    # Get the match data
    url = f'http://api:5001/api/events/{event_id}/matches'
    resp = requests.get(url)
    if resp.status_code != 200:
        logging.error(f'Match get failed: {resp.status_code}: {resp.text}')
        return
    logging.debug(f'Match data: {resp.json()}')
    for id in resp.json():
        logging.debug(f'Match: {id}')
        match = resp.json()[id]
        id = int(id)
        rt = match['teams']['red']
        bt = match['teams']['blue']
        
        if int(id) < int(match_id):
            this_red_score = match['results']['red']['score']
            this_blue_score = match['results']['blue']['score']

            for t in rt:
                if t in team_scores:
                    team_scores[t].append(this_red_score)
                else:
                    team_scores[t] = [this_red_score]
            for t in bt:  
                if t in team_scores:
                    team_scores[t].append(this_blue_score)
                else:
                    team_scores[t] = [this_blue_score]
        elif int(id) == int(match_id):
            these_teams = rt + bt

            # add the scores passed in to the teams
            for t in rt:
                if t in team_scores:
                    team_scores[t].append(red_score)
                else:
                    team_scores[t] = [red_score]
            for t in bt:  
                if t in team_scores:
                    team_scores[t].append(blue_score)
                else:
                    team_scores[t] = [blue_score]
        else:
            predict = False
            for t in rt:
                if t in these_teams:
                    predict = True
            for t in bt:
                if t in these_teams:
                    predict = True
            if predict:
                future_matches[int(id)] = {'red': rt, 'blue': bt}
    
    # Create the averages
    team_averages = {k: sum(v) / len(v) for k, v in team_scores.items()}

    logging.info(f'Team Averages: {team_averages}')
    logging.info(f'Future Matches: {len(future_matches)}')

    return team_averages, future_matches

def main():
    # Load from the .env file
    load_dotenv()
    logging.info("Loading environment variables from .env file.")

    # Load the environment variables
    env = load_env(['KAFKA_BOOTSTRAP_SERVER', 'KAFKA_TOPIC'])

    # Create the consumer
    consumer = None
    while True:    
        try:
            consumer = KafkaConsumer(env["KAFKA_TOPIC"], client_id='simple-average', bootstrap_servers=env["KAFKA_BOOTSTRAP_SERVER"])
            break
        except:
            logging.error("Could not connect to Kafka.  Retrying...")
            sleep(10)
            continue

    # Loop forever
    for message in consumer:
        # Convert from byte string to normal string
        msg = str(message.value, 'utf-8') 
        logging.debug("Received message: " + str(msg))

        dict = json.loads(msg)
        event = dict["event"]
        match_id = int(dict["match_id"])
        red = dict["red"]['score']
        blue = dict["blue"]['score']
        logging.debug(f'Event: {event}, Match: {match_id}, Red: {red}, Blue: {blue}')

        team_averages, future_matches = get_team_scores(event, match_id, red, blue)

        logging.debug(f'Team Averages: {team_averages}')
        logging.debug(f'Future Matches: {future_matches}')

        n = 0
        for seq, teams in future_matches.items():
            seq = int(seq)
            red = teams['red']
            blue = teams['blue']
            logging.debug(f'Predicting match {seq}: {red} vs {blue}')
            red_score = sum([team_averages.get(t, 0) for t in red]) / len(red)
            blue_score = sum([team_averages.get(t, 0) for t in blue]) / len(blue)

            logging.debug(f'Predicted match {seq}: {red}={red_score} vs {blue}={blue_score}')

            if red_score > 0 and blue_score > 0:
                red_win = 1 if red_score > blue_score else 0
                blue_win = 1 if blue_score > red_score else 0

                url = f'http://api:5001/api/events/{event}/matches/{seq}'
                headers = {'Content-Type': 'application/json', 'charset': 'utf-8'}
                data = {'algorithm': 'average_score', 'red': {'win': red_win}, 'blue': {'win': blue_win}}
                resp = requests.patch(url, json=data, headers=headers)
                if resp.status_code == 200:
                    logging.debug(f'Updated {event}:{seq} with {data}')
                else:
                    logging.error(f'Match patch failed: {resp.status_code}: {resp.text}')

            n += 1
        logging.info(f'Match {match_id} predicted {n} matches')

    # Close the consumer
    logging.info("Closing consumer.")
    consumer.close()
    


if __name__ == "__main__":
    main()