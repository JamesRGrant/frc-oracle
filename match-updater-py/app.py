import os, sys, logging
from dotenv import load_dotenv
import requests, json
from kafka import KafkaConsumer
import time
from time import sleep

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

def main():
    # Load from the .env file
    load_dotenv()
    logging.info("Loading environment variables from .env file.")

    # Load the environment variables
    env = load_env(['KAFKA_BOOTSTRAP_SERVER', 'KAFKA_TOPIC'])

    # sleep(30)

    # Create the consumer
    consumer = None
    while True:    
        try:
            consumer = KafkaConsumer(env["KAFKA_TOPIC"], client_id='match-updater', bootstrap_servers=env["KAFKA_BOOTSTRAP_SERVER"])
            logging.info(f"Kafka Consumer created, subscribed to {consumer.subscription()}")
            break
        except:
            logging.error("Could not connect to Kafka.  Retrying...")
            time.sleep(10)
            continue

    # Loop forever
    for message in consumer:
        # Convert from byte string to normal string
        msg = str(message.value, 'utf-8') 
        logging.info("Received message: " + str(msg))

        dict = json.loads(msg)
        event = dict["event"]
        match_id = dict["match_id"]
        red = dict["red"]
        blue = dict["blue"]

        url = f'http://api:5001/api/events/{event}/matches/{match_id}'
        headers = {'Content-Type': 'application/json', 'charset': 'utf-8'}
        data = {'results': {'red': red, 'blue': blue}}
        resp = requests.patch(url, json=data, headers=headers)
        if resp.status_code == 200:
            logging.info(f'Updated {event}:{match_id} with {data}')
        else:
            logging.error(f'Match patch failed: {resp.status_code}: {resp.text}')

    # Close the consumer
    logging.info("Closing consumer.")
    consumer.close()
    
if __name__ == "__main__":
    main()