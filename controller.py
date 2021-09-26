from time import sleep
from flask import Flask
from flask_mqtt import Mqtt
import threading
import yaml
import json
import os
from openpyxl import Workbook
from datetime import datetime


class ExcelLog:
    def __init__(self, name):
        self.wb = Workbook()
        self.ws = self.wb.active
        self.name = name
        self.ws.append(["TIME", "NAME", "FLAG", "INFO"])

    def add(self, msg):
        dt = datetime.now()
        self.ws.append([str(dt), msg['name'], msg['flag'], msg['info']])
        print(dt, msg['name'], msg['flag'], msg['info'])

    def save(self):
        self.wb.save(self.name)


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
    mqtt.topic_events = config['topics']['events']
    mqtt.topic_commands = config['topics']['commands']
    mqtt.service_name = config['controller']['name']
    mqtt.app_port = config['controller']['app port']
    mqtt.admi_service_info = config['active redundancy']
    # mqtt.receptor_name = config['receptor']['name']
    if config['simulation']['fail counter']['enable']:
        mqtt.max_fail_count = config['simulation']['fail counter']['max']
    else:
        mqtt.max_fail_count = None
    mqtt.setup = True
    mqtt.log = ExcelLog("simulation_log.xlsx")


def publish_on_topic(topic, flag, info):
    message = {
        "name": mqtt.service_name,
        "flag": flag,
        "info": info
    }
    mqtt.publish(topic, json.dumps(message))


def publish_command(info):
    publish_on_topic(mqtt.topic_commands, "command", info)


def start_admi_service(service_info_dic):
    os.system(f"python3 admi_service.py {service_info_dic['name']} {service_info_dic['app port']} {service_info_dic['error']['enable']} {service_info_dic['error']['probability']} {service_info_dic['priority']}")


def start_receptor():
    os.system("python3 receptor_service.py")


def add_internal_event(flag, info):
    mqtt.log.add({"name": mqtt.service_name, "flag": flag, "info": info})


@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe(mqtt.topic_events)
    add_internal_event("setup", "Creating required services...")
    mqtt.services = []
    mqtt.services_count = 0
    mqtt.services_ready = 0
    mqtt.main_admi_service = None
    for admin_service in mqtt.admi_service_info:
        service = threading.Thread(target=start_admi_service,
                                   args=(admin_service,))
        mqtt.services.append(service)
        service.start()
        mqtt.services_count += 1
        if not mqtt.main_admi_service or admin_service['priority'] < mqtt.main_admi_service[1]:
            mqtt.main_admi_service = (admin_service['name'], admin_service['priority'])

    service = threading.Thread(target=start_receptor)
    mqtt.services.append(service)
    mqtt.services_count += 1
    service.start()
    add_internal_event("setup", "Services created!")


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    msg = json.loads(str(message.payload.decode("utf-8")))
    if message.topic == mqtt.topic_events:
        mqtt.log.add(msg)

        if mqtt.setup :
            mqtt.services_ready += 1
            add_internal_event("setup", f"{msg['name']} is ready to receive orders.")
            if mqtt.services_ready == mqtt.services_count:
                add_internal_event("setup", "All the services are ready for receive orders.")
                mqtt.setup = False
                publish_command({'command': 'set', 'arguments': ['main service', mqtt.main_admi_service[0]]})
                if mqtt.max_fail_count:
                    publish_command({'command': 'set', 'arguments': ['fail count', mqtt.max_fail_count]})
                publish_command({'command': 'start'})
        elif msg["flag"] == "stopped":
            add_internal_event("ended", "Simulation ended.")
            mqtt.log.save()
            publish_command({'command': 'die'})
            sleep(1)
            raise Exception("This is just an error to end the process. Please close this terminal")



if __name__ == '__main__':
    mqtt.init_app(app)
    app.run(host='localhost', port=mqtt.app_port)


# import threading
# import os
# import time

# def star_service(arg):
#     os.system(f"python {arg}")

# service1 = threading.Thread(target=star_service, args=("admin.py",))
# service1.start()
# time.sleep(2)
# service2 = threading.Thread(target=star_service, args=("receptor.py",))
# service2.start()
