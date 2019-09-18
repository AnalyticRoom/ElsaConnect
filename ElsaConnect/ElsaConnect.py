from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import io
import boto3
import datetime

mile = 1.609344

#!/usr/bin/env python
# encoding: utf-8

""" Simple Python class to access the Tesla JSON API
https://github.com/gglockner/teslajson
The Tesla JSON API is described at:
http://docs.timdorr.apiary.io/
Example:
import teslajson
c = teslajson.Connection('youremail', 'yourpassword')
v = c.vehicles[0]
v.wake_up()
v.data_request('charge_state')
v.command('charge_start')
"""
class Connection(object):
    """Connection to Tesla Motors API"""

    def __init__(self,
                 email='',
                 password='',
                 access_token='',
                 url="https://owner-api.teslamotors.com",
                 api="/api/1/",
                 client_id="e4a9949fcfa04068f59abb5a658f2bac0a3428e4652315490b659d5ab3f35a9e",
                 client_secret="c75f14bbadc8bee3a7594412c31416f8300256d7668ea7e6e7f06727bfb9d220"):
        """Initialize connection object
		
		Sets the vehicles field, a list of Vehicle objects
		associated with your account
		Required parameters:
		email: your login for teslamotors.com
		password: your password for teslamotors.com
		
		Optional parameters:
		access_token: API access token
		url: base URL for the API
		api: API string
		client_id: API identifier
		client_secret: Secret API identifier
		"""
        self.url = url
        self.api = api
        if not access_token:
            oauth = {
                "grant_type": "password",
                "client_id": client_id,
                "client_secret": client_secret,
                "email": email,
                "password": password}
            auth = self.__open("/oauth/token", data=oauth)
            access_token = auth['access_token']
        self.access_token = access_token
        self.head = {"Authorization": "Bearer %s" % self.access_token}
        self.vehicles = [Vehicle(v, self) for v in self.get('vehicles')['response']]

    def get(self, command):
        """Utility command to get data from API"""
        return self.__open("%s%s" % (self.api, command), headers=self.head)

    def post(self, command, data={}):
        """Utility command to post data to API"""
        return self.__open("%s%s" % (self.api, command), headers=self.head, data=data)

    def __open(self, url, headers={}, data=None):
        """Raw urlopen command"""
        req = Request("%s%s" % (self.url, url), headers=headers)
        try:
            req.data = urlencode(data).encode('utf-8')  # Python 3
        except:
            try:
                req.add_data(urlencode(data))  # Python 2
            except:
                pass
        resp = urlopen(req)
        charset = resp.info().get('charset', 'utf-8')
        return json.loads(resp.read().decode(charset))


class Vehicle(dict):
    """Vehicle class, subclassed from dictionary.
	
	There are 3 primary methods: wake_up, data_request and command.
	data_request and command both require a name to specify the data
	or command, respectively. These names can be found in the
	Tesla JSON API."""

    def __init__(self, data, connection):
        """Initialize vehicle class
		
		Called automatically by the Connection class
		"""
        super(Vehicle, self).__init__(data)
        self.connection = connection

    def data_request(self, name):
        """Get vehicle data"""
        result = self.get('data_request/%s' % name)
        return result['response']

    def wake_up(self):
        """Wake the vehicle"""
        return self.post('wake_up')

    def command(self, name):
        """Run the command for the vehicle"""
        return self.post('command/%s' % name)

    def get(self, command):
        """Utility command to get data from API"""
        return self.connection.get('vehicles/%i/%s' % (self['id'], command))

    def post(self, command):
        """Utility command to post data to API"""
        return self.connection.post('vehicles/%i/%s' % (self['id'], command))

import os

def establish_connection(user, pwd, token=None):
    print('Trying to access car')
    c = Connection(email=user, password=pwd, access_token=token)
    return c

def is_offline(c, car):
    for v in c.vehicles:
        if v["display_name"] == car:
            if v["state"] == "offline":
                return True
    return False


def get_odometer(c, car):
    odometer = None
    for v in c.vehicles:
        if v["display_name"] == car:
            d = v.data_request("vehicle_state")
            odometer = int(round(d["odometer"] * mile))
    return odometer

def get_speed(c, car):
    speed = None
    for v in c.vehicles:
        if v["display_name"] == car:
            d = v.data_request("drive_state")
            if d["speed"] is None:
                return 0;
            odometer = int(round(d["speed"] * mile))
    return speed


def get_range(c, car):
    charge = None
    for v in c.vehicles:
        if v["display_name"] == car:
            d = v.data_request("charge_state")
            charge =  int(round(d["ideal_battery_range"] * mile))
    return charge


def get_wall_wattage(charge_state):
    watt = 0
    if charge_state["charger_actual_current"] is not None and charge_state["charger_voltage"] is not None:
        watt = int(charge_state["charger_actual_current"]) * int(charge_state["charger_voltage"])
    return watt


def get_battery_wattage(charge_state):
    watt = 0
    if charge_state["charger_actual_current"] is not None:
        watt = int(charge_state["charger_actual_current"] * 400)
    return watt


def get_amps(charge_state):
    amps = 0
    if charge_state["charger_actual_current"] is not None:
        amps = int(charge_state["charger_actual_current"])
    return amps


def get_numberValueFrom(listOfStates, parameterName):
    result = 0
    if listOfStates[parameterName] is not None:
        result = int(listOfStates[parameterName])
    return result


def get_ValueFrom(listOFStates, parameterName):
    result = 0
    if listOFStates[parameterName] is not None:
        result = listOFStates[parameterName]
    return result


def lambda_handler(event, context):    
    import sys

    def get_all_drivestate_info(c, car):
        for v in c.vehicles:
            if v["display_name"] == car:
                return v.data_request("drive_state")
                
    def get_all_vehicle_info(c, car):
        for v in c.vehicles:
            if v["display_name"] == car:
                return v.data_request("vehicle_state")

    def get_all_charge_info(c, car):
        for v in c.vehicles:
            if v["display_name"] == car:
                return v.data_request("charge_state")
    
    def get_car_data(c, user, mailpwd, receiver, charge, drive, vehiclestate):
        #header = 'To:' + receiver + '\n' + 'From: ' + user + '\n' + 'Subject: Tesla {0:3d}'.format(get_range(c, "Tello")) + ' {0:3d}'.format(get_amps(charge))
        #print (header)
        try:
            body = '\n\n' + '<KmRangeLeft>{0}</KmRangeLeft>'.format(get_range(c, "Tello")) + '\n<CurrentIn>{0}</CurrentIn>'.format(get_amps(charge)) + '\n<InputW>{0}</InputW>'.format(get_wall_wattage(charge)) + '\n<BatteryW>{0}</BatteryW>'.format(get_battery_wattage(charge)) + '\n<BatteryLevel>{0}</BatteryLevel>'.format(get_numberValueFrom(charge, "battery_level")) + '\n<UsableBatteryLevel>{0}</UsableBatteryLevel>'.format(get_numberValueFrom(charge, "usable_battery_level")) + '\n<BatteryHeater>{0}</BatteryHeater>'.format(get_ValueFrom(charge, "battery_heater_on")) + '\n<Latitude>{0}</Latitude>'.format(get_ValueFrom(drive, "latitude")) + '\n<Longitude>{0}</Longitude>'.format(get_ValueFrom(drive, "longitude")) + '\n<WallCurrent>{0}</WallCurrent>'.format(get_ValueFrom(charge, "charger_pilot_current")) + '\n<Odometer>{0}</Odometer>'.format(int(round(get_ValueFrom(vehiclestate, "odometer") * mile))) + '\n<Speed>{0}</Speed>'.format(int(round((get_ValueFrom(drivestate, "speed")) * 1.609344)))
            print(body)
        except Exception as e:
            print (e)
        print ('done!')
        return body





    try:
        f = open("rainflow.txt")
        user = f.readline().rstrip('\n')
        pwd = f.readline().rstrip('\n')
        mailsender = f.readline().rstrip('\n')
        mailpwd = f.readline().rstrip('\n')
        receiver = f.readline().rstrip('\n')
    except:
        print ("Could not read credentials file.")
        sys.exit(1)
    
    try:
        c = establish_connection(user, pwd)
    except:
        try:
            c = establish_connection(user, pwd)
        except:
            print ("Could not access car.")
            sys.exit(1)
    
    if is_offline(c, "Tello"):
        print ('sorry your car is offline')
        sys.exit(1)
    
    print('Reading drive state')
    drivestate = get_all_drivestate_info(c, "Tello")
    for p in drivestate:
        print(p, drivestate[p])
    
    print('Reading charge state')
    chargestate = get_all_charge_info(c, "Tello")
    for p in chargestate:
        print(p, chargestate[p])
    
    print('Reading vehicle state')
    vehiclestate = get_all_vehicle_info(c, "Tello")
    for p in vehiclestate:
        print(p, vehiclestate[p])
    
    rangeForResponse = get_range(c, "Tello")
    amps = get_amps(chargestate)

    try:
        print('Getting data from car:')
        mailBody = get_car_data(c, mailsender, mailpwd, receiver, chargestate, drivestate, vehiclestate)
    except:
        print ("Could not get car data.")
        sys.exit(1)
    try:
        subject = 'Tesla {0:3d}'.format(rangeForResponse)
        print(subject)        
        try:
            print('Connect to S3')
            s3 = boto3.resource('s3')
            print('Connected')
            #s3://mathiasschulttesla/tesla.csv
            s3.Bucket('mathiasschulttesla').download_file('tesla.csv', '/tmp/tesla.csv')
            print('File downloaded')
            dt = datetime.datetime.now()
            linetoappend = '{0:3d},{1:4d}-{2:02d}-{3:02d} {4:02d}:{5:02d},1,{6},{7:3.3f},{8:3.3f},{9},{10}'.format(rangeForResponse, dt.year, dt.month, dt.day, dt.hour, dt.minute, amps, get_ValueFrom(drivestate, "longitude"), get_ValueFrom(drivestate, "latitude"),int(round((get_ValueFrom(drivestate, "speed")) * 1.609344)), int(round(get_ValueFrom(vehiclestate, "odometer") * mile)))
            print('Append this: ' + linetoappend)
            with open('/tmp/tesla.csv', "a") as teslafile:
                teslafile.write(linetoappend + os.linesep)
            print('/tmp/tesla.csv')
            s3.Bucket('mathiasschulttesla').upload_file('/tmp/tesla.csv', 'tesla.csv')
        except Exception as e:
            print(e)
    except:
        print ("Could not add to bucket.")
        sys.exit(1)
    #response = open(os.environ['res'], 'w')
    #response.write(mailBody)
    #response.close()
    
    return {
        'statusCode': 200,
        'body': json.dumps(mailBody)
    }
