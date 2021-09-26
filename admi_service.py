from flask import Flask
from flask_mqtt import Mqtt
import yaml
import json
import sys
import random
import time

with open('config.yaml') as file:
    config = yaml.load(file, Loader=yaml.FullLoader)
    app = Flask(sys.argv[1])
    app.config['MQTT_BROKER_URL'] = config['broker']['ip']
    app.config['MQTT_BROKER_PORT'] = config['broker']['port']
    app.config['MQTT_USERNAME'] = config['broker']['username']
    app.config['MQTT_PASSWORD'] = config['broker']['password']
    app.config['MQTT_KEEPALIVE'] = config['broker']['keep alive']
    app.config['MQTT_TLS_ENABLED'] = config['broker']['tls enabled']

    mqtt = Mqtt()
    mqtt.topic_request = config['topics']['request']
    mqtt.topic_success = config['topics']['success']
    mqtt.topic_commands = config['topics']['commands']
    mqtt.topic_events = config['topics']['events']
    mqtt.service_name = sys.argv[1]
    mqtt.app_port = int(sys.argv[2])
    mqtt.error = sys.argv[3] == "True"
    mqtt.probability = float(sys.argv[4])
    mqtt.priority = int(sys.argv[5])
    mqtt.working_time = config['simulation']['request']['time'] * \
        config['simulation']['request']['spended fraction']


def publish_on_topic(topic, flag, info):
    message = {
        "name": mqtt.service_name,
        "flag": flag,
        "info": info
    }
    mqtt.publish(topic, json.dumps(message))


def publish_event(flag, msg):
    publish_on_topic(mqtt.topic_events, flag, msg)


def publish_error(msg):
    publish_event("error", msg)


def send_success_info(msg):
    publish_on_topic(mqtt.topic_success, "success", {"message": msg, "priority": mqtt.priority})


@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe(mqtt.topic_request)
    mqtt.subscribe(mqtt.topic_commands)
    publish_event("ready", "The service is ready to run.")


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    msg = json.loads(str(message.payload.decode("utf-8")))
    if message.topic == mqtt.topic_request:
        publish_event(
            "received", f"Admission request for user '{msg['info']['name']}' receved.")
        if mqtt.error and random.random() < mqtt.probability:
            publish_error("Service internal error!")
        else:
            publish_event("working", "Proccessing request...")
            time.sleep(mqtt.working_time)
            publish_event("success", "Admission completed.")
            send_success_info("Admission process completed.")
    elif msg['flag'] == 'command':
        raw_command = msg['info']['command']
        if raw_command == 'die':
            raise Exception("This is just an error to end the process. Please close this terminal.")


if __name__ == '__main__':
    mqtt.init_app(app)
    app.run(host='localhost', port=mqtt.app_port)
