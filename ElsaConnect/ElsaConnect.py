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

try:  # Python 3
    from urllib.parse import urlencode
    from urllib.request import Request, urlopen
except:  # Python 2
    from urllib import urlencode
    from urllib2 import Request, urlopen
import json


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


# import teslajson


def establish_connection(token=None):
    c = Connection(email="mathias.schult@dnvgl.com", password=pwd, access_token=token)
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
            odometer = int(round(d["odometer"] * 1.609))
    return odometer


def get_range(c, car):
    charge = None
    for v in c.vehicles:
        if v["display_name"] == car:
            d = v.data_request("charge_state")
            charge =  int(round(d["ideal_battery_range"] * 1.609))
    return charge


def get_wall_wattage(charge_state):
    watt = 0
    if charge_state["charger_actual_current"] is not None and charge_state["charger_voltage"] is not None:
        watt = int(charge_state["charger_actual_current"]) * int(charge_state["charger_voltage"])
    return watt


def get_battery_wattage(charge_state):
    watt = 0
    if charge_state["battery_current"] is not None:
        watt = int(charge_state["battery_current"] * 400)
    return watt


def get_amps(charge_state):
    amps = 0
    if charge_state["battery_current"] is not None:
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

def get_all_charge_info(c, car):
    for v in c.vehicles:
        if v["display_name"] == car:
            return v.data_request("charge_state")

def get_all_drivestate_info(c, car):
    for v in c.vehicles:
        if v["display_name"] == car:
            return v.data_request("drive_state")

def send_tesla_mail(c, user, pwd, receiver, charge, drive):
    import smtplib
        
    smtpserver = smtplib.SMTP("smtp.mail.yahoo.com", 587)
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo()  # extra characters to permit edit
    smtpserver.login(user, pwd)
    header = 'To:' + receiver + '\n' + 'From: ' + user + '\n' + 'Subject: Tesla {0:3d}'.format(get_range(c, "Elsa")) + ' {0:3d}'.format(get_amps(charge))
    print (header)
    body = '\n\n' + '<InputW>{0}</InputW>'.format(get_wall_wattage(charge)) + '\n<BatteryW>{0}</BatteryW>'.format(get_battery_wattage(charge)) + '\n<BatteryLevel>{0}</BatteryLevel>'.format(get_numberValueFrom(charge, "battery_level")) + '\n<UsableBatteryLevel>{0}</UsableBatteryLevel>'.format(get_numberValueFrom(charge, "usable_battery_level")) + '\n<BatteryHeater>{0}</BatteryHeater>'.format(get_ValueFrom(charge, "battery_heater_on")) + '\n<Latitude>{0}</Latitude>'.format(get_ValueFrom(drive, "latitude")) + '\n<Longitude>{0}</Longitude>'.format(get_ValueFrom(drive, "longitude"))
    print(body)
    msg = header + body
    smtpserver.sendmail(user, receiver, msg)
    print ('done!')
    smtpserver.close()


import sys
try:
    f = open("rainflow.txt")
    user = f.readline().rstrip('\n')
    pwd = f.readline().rstrip('\n')
    receiver = f.readline().rstrip('\n')
except:
    print ("Could not read credentials file.")
    sys.exit(1)
    
try:
    c = establish_connection()
except:
    print ("Could not access car.")
    sys.exit(1)
        
if is_offline(c, "Elsa"):
    print ('sorry your car is offline')
    sys.exit(1)

chargestate = get_all_charge_info(c, "Elsa")
for p in chargestate:
    print(p, chargestate[p])

drivestate = get_all_drivestate_info(c, "Elsa")
for p in drivestate:
    print(p, drivestate[p])

print ('Range   {0:6d}km'.format(get_range(c, "Elsa")))
print ('Current {0:6d}A'.format(get_amps(chargestate)))
print ('WallW   {0:6d}W'.format(get_wall_wattage(chargestate)))
print ('BatW    {0:6d}W'.format(get_battery_wattage(chargestate)))
print ('Odo     {0:6d}km'.format(get_odometer(c, "Elsa")))

try:
    send_tesla_mail(c, user, pwd, receiver, chargestate, drivestate)
except:
    print ("Could not send mail.")
    sys.exit(1)

