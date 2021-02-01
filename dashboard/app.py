#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  app.py
# Author: Jyotsna Priya
#  
#  Gage and Graph by MJRoBot.org 

'''
    Web Server for displaying sensor data with Gage and Graph plot and Highcharts. Microservices accessed are AWS IoT core and MongoDB Atlas
'''

from datetime import datetime
from dateutil import tz

import requests
import subprocess
import json
from pymongo import MongoClient
from pprint import pprint
from datetime import datetime
from flask import Flask, render_template, send_file, make_response, request

app = Flask(__name__)

# Retrieve last sensor data from AWS IoT shadow
def getLastShadowData():

    try:
        subprocess.check_call("python3 /home/ubuntu/SoilMonitor/basicShadowListener.py -e a3bikkrdsdyhco-ats.iot.us-east-1.amazonaws.com -r /home/ubuntu/SoilMonitor/certs/AmazonRootCA1.pem -c /home/ubuntu/SoilMonitor/certs/d23db933d6-certificate.pem.crt -k /home/ubuntu/SoilMonitor/certs/d23db933d6-private.pem.key -n RaspberryPi -id RaspberryPiApp", shell=True)
    except subprocess.CalledProcessError as exc:
        print(exc.output)
    f = open("/home/ubuntu/SoilMonitor/output.txt", "r")
    data = json.loads(f.read())
    timestamp = data['metadata']['reported']['moisture']['timestamp']
    temp = data['state']['reported']['temp']
    moisture = data['state']['reported']['moisture']
    f.close()
    time = str(datetime.fromtimestamp(timestamp)) 
    temp = float(temp)
    moisture = int(moisture)

    # Auto-detect zones:
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('America/Los_Angeles')
    utc = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
    utc = utc.replace(tzinfo=from_zone)

    # Convert time zone
    curr_zone_time = utc.astimezone(to_zone)
    return curr_zone_time, temp, moisture

def getSensorHistoryData():
    client = MongoClient('mongodb+srv://cmpe286user:password1234@cluster0.1s0gw.mongodb.net/SoilMonitor?retryWrites=true&w=majority')
    db=client.SoilMonitor
    # cursor = db.sensorHistoryData.find().sort("Timestamp", -1)
    cursor = db.sensorData.find().sort("Timestamp", -1)
    last_ten_days_data = {}
    temp_min = float('inf')
    for c in cursor:
        dt = c['Timestamp']
        # print(dt.strftime('%Y-%m-%d::%H-%M-%S.%f'))
        date = dt.strftime('%Y-%m-%d')
        time = dt.strftime('%H.%M')
        moistureLevel = c['Moisture Level']
        temp = c['Temperature'] 
        # print(date, time, moistureLevel, temp)
        if date not in last_ten_days_data:
            last_ten_days_data[date] = [time, moistureLevel, temp]
        else:
            if moistureLevel < last_ten_days_data[date][1]:
                last_ten_days_data[date] = [time, moistureLevel, temp]

        if len(last_ten_days_data) >= 10:
            break

    data = []
    for key, value in last_ten_days_data.items():
        data.append({"date": key, "timeMM": float(value[0]), "moistureLevel": value[1], "temperature": int(value[2])})

    return data


# main route 
@app.route("/")
def index():

    time, temperature, moisture = getLastShadowData()
    lastTenDaysData = getSensorHistoryData()

    templateData = {
        "time"        : time,
        "temperature" : temperature,
        "moisture"    : moisture,
        "lastTenDaysData": lastTenDaysData
    }
    # print(templateData)
    return render_template('index.html', **templateData)


if __name__ == "__main__":
   #app.run(host='0.0.0.0', port=5000, debug=True)
   app.run()
