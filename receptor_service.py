from flask import Flask
from flask_mqtt import Mqtt
import threading
import yaml
import json
from faker import Faker
import sys

with open('config.yaml') as file:
    config = yaml.load(file, Loader=yaml.FullLoader)
    app = Flask(config['receptor']['name'])
    app.config['MQTT_BROKER_URL'] = config['broker']['ip']
    app.config['MQTT_BROKER_PORT'] = config['broker']['port']
    app.config['MQTT_USERNAME'] = config['broker']['username']
    app.config['MQTT_PASSWORD'] = config['broker']['password']
    app.config['MQTT_KEEPALIVE'] = config['broker']['keep alive']
    app.config['MQTT_TLS_ENABLED'] = config['broker']['tls enabled']

    mqtt = Mqtt()
    mqtt.topic_request = config['topics']['request']
    mqtt.topic_success = config['topics']['success']
    mqtt.topic_events = config['topics']['events']
    mqtt.topic_commands = config['topics']['commands']
    mqtt.request_time = config['simulation']['request']['time']
    mqtt.service_name = config['receptor']['name']
    mqtt.app_port = config['receptor']['app port']
    mqtt.service_running = False
    mqtt.fail_count = False
    mqtt.faker = Faker()


def publish_on_topic(topic, flag, info):
    message = {
        "name": mqtt.service_name,
        "flag": flag,
        "info": info
    }
    mqtt.publish(topic, json.dumps(message))


def publish_event(flag, msg):
    publish_on_topic(mqtt.topic_events, flag, msg)


def admission_request(user):
    publish_on_topic(mqtt.topic_request, "request", user)
    publish_event("request", f"Admission request for user '{user['name']}'.")


def publish_error(msg):
    publish_event("error", msg)

def stop_task():
    mqtt.success_validator.cancel()


def stop_simulation():
    mqtt.service_running = False
    publish_event("stopped", "Simulation stopped.")

def process_success_request():
    for message in mqtt.message_stack:
        if message["name"] == mqtt.main_admi_service:
            publish_event(
                "success", "The request was successfully handled by the main service")
            break
    else:
        mqtt.fail_counter += 1
        publish_error(
            f"Successful request of service '{mqtt.main_admi_service}' (main service) was not found in queue.")
        if len(mqtt.message_stack) > 0:
            mqtt.message_stack.sort(key=lambda msg: msg['info']['priority'])
            publish_event("switch",f"The successful request of the service '{mqtt.message_stack[0]['name']}' was taken as a backup. Fail counter = {mqtt.fail_counter}.")
        else:
            publish_error(f"There are not services available to handled the request. Request failed. Fail counter = {mqtt.fail_counter}.")

    mqtt.message_stack = []

    if mqtt.fail_count:
        if mqtt.fail_counter == mqtt.max_fail_count:
            publish_event(
                "details", f"The fail counter has reached its maximum ({mqtt.max_fail_count}).")
            stop_simulation()
            return

    start_task()


def start_task():
    admission_request(
        {"name": mqtt.faker.name(), "id": mqtt.faker.iana_id()})
    mqtt.success_validator = threading.Timer(
        mqtt.request_time, process_success_request)
    mqtt.success_validator.start()


@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe(mqtt.topic_success)
    mqtt.subscribe(mqtt.topic_commands)
    mqtt.main_admin_service = ""
    publish_event("ready", "The service is ready to run.")


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    msg = json.loads(str(message.payload.decode("utf-8")))
    if message.topic == mqtt.topic_success:
        if mqtt.service_running:
            mqtt.message_stack.append(msg)
    elif msg['flag'] == 'command':
        raw_command = msg['info']['command']
        if raw_command == 'start':
            if mqtt.main_admi_service:
                mqtt.service_running = True
                mqtt.message_stack = []
                mqtt.fail_counter = 0
                publish_event(
                    "running", f"The simulation has started.")
                start_task()
            else:
                publish_error(
                    "You must set the main admission service before start the simulation.")
        elif raw_command == 'stop':
            if not mqtt.service_running:
                publish_error("The simulation is not runnig yet.")
            else:
                stop_task()
                stop_simulation()
        elif raw_command == 'set':
            argument = msg['info']['arguments']
            if argument[0] == 'main service':
                mqtt.main_admi_service = argument[1]
                publish_event(
                    "setup", f"Set main admission service to {mqtt.main_admi_service}")
            elif argument[0] == 'fail count':
                mqtt.fail_count = True
                mqtt.max_fail_count = argument[1]
                publish_event(
                    "setup", f"Fail counter has been enable. Max: {argument[1]}")
        elif raw_command == 'die':
            raise Exception("This is just an error to end the process. Please close this terminal.")

if __name__ == '__main__':
    mqtt.init_app(app)
    app.run(host='localhost', port=mqtt.app_port)
