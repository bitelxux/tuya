#!/usr/bin/python3

import logging
import argparse
import json
import os
import pickledb
import random
import time
import yaml
from glob import glob
from prometheus_client import start_http_server, Gauge

import tinytuya

# Logging 
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

db = pickledb.load("persistent.db", True)

class TuyaExporter:

    devices = {}

    def __init__(self):
        self.load_devices()
        self.metric_dict = {}

    def load_devices(self):
        with open("devices.yml") as f:
            self.devices = yaml.load(f, yaml.SafeLoader)

    def create_gauge_for_metric(self):
        if not self.metric_dict.get('termo'):
            self.metric_dict['termo'] = Gauge('termo_instant_kwh', f"Termo instant kwh")
    
    def set_value(self):
        self.metric_dict['termo'].set(random.random())

    def main(self):
        exporter_port = int(os.environ.get("EXPORTER_PORT", "9877"))
        start_http_server(exporter_port)
        while True:
            for device in self.devices.keys():
                if not self.devices[device].get('ip'):
                    continue
                self.read_data(device)
                #self.create_gauge_for_metric()
                #self.set_value()
            time.sleep(5)

    def read_data(self, device_name):
        device_details = self.devices[device_name]
        device = tinytuya.OutletDevice(device_details['id'], device_details['ip'], device_details['key'])
        device.set_version(3.3)
        device.set_socketRetryLimit(1)
        device.set_socketTimeout(1)
        device.heartbeat(True)
        device.updatedps()
        data = device.status()
        print(f"{device_name}: {data}")
        if 'dps' in data:
           kwh = self.calc_kwh(device_name, data['dps'])
        else:
           print(f"Error reading {device_name}")
        return data

    def calc_kwh(self, device_name, data):
        device_details = self.devices[device_name]
        if device_details['kwh']:
            device_details['total_kwh'] =  data[device_details['kwh']]
        if not device_details.get('previous_kwh'):
            device_details['previous_kwh'] = data[device_details['wats']]/10
            stored_kwh = db.get(device_name)
            device_details['total_kwh'] = stored_kwh and stored_kwh or 0
            device_details['t0'] = time.time()
        else:
            try:
                device_details['read_kwh'] = data[device_details['wats']]/10 
                av = (device_details['previous_kwh'] + device_details['read_kwh']) / 2.0
            except e:
                print(f"ERROR {data}")
                raise(f"ERROR {data}")
            t = time.time() - device_details['t0'] 
            device_details['t0'] = time.time()
            power = (av / 3600) * t
            device_details['total_kwh'] += power
            device_details['previous_kwh'] = device_details['read_kwh']
             
            print(f"Last lecture: {av}, last period power: {power}, total power: {device_details['total_kwh']}")

        db.set(device_name, device_details['total_kwh'])
        return device_details['total_kwh'] 


def tests():
    c = TuyaExporter()
    c.load_devices()
    data = c.read_data('cuadro')

if __name__ == "__main__":
    c = TuyaExporter()
    c.main()


































