#!/usr/bin/python

import yaml
import os
import urllib.request
import requests
import time

def downloadFirmware(version, type):
    #Compose download url
    file_url = 'https://github.com/arendst/Tasmota/releases/download/v' + version + '/tasmota-' + type + '.bin'

    #Create folder
    path = 'firmware/' + version
    if not os.path.exists(path):
        os.makedirs(path)

    #Download file
    filename = 'tasmota-' + type + '.bin'
    save_path = path + '/' + filename

    if not os.path.isfile(path + '/' + filename):
        print('Download ' + filename)
        urllib.request.urlretrieve (file_url, save_path)

def bulkUpdate(devices, version, type):
    for device, settings in devices.items():
        if type == '':
            type = settings['type']
        downloadFirmware(version, type)
        sendUpdate(settings["host"], type, version)

def sendUpdate(host, type, version):
    url = 'http://' + host + '/u2'

    firmware_path = 'firmware' + '/' + version + '/' + 'tasmota-' + type + '.bin'

    try:
        files = {'file': open(firmware_path, 'rb')}
    except FileNotFoundError:
        raise FileNotFoundError("Please make sure that firmware file {0} exists.".format(firmware))

    for attempt in range(5):
        try:
            r = requests.post(url, files=files)
        except:
            print("Something went wrong with device %s. Retry. Attempt %s/5" % (host, attempt))
        else:
            break
    else:
        raise (ConnectionError, "Something went wrong with device {0}!".format(host))

def getStatus(device):
	host = 'http://' + device["host"] + '/cm'
	payload = {
		'user'    : device["username"],
		'password': device["password"],
		'cmnd'    : "status 0"
	}

	for attempt in range(5):
		try:
			r = requests.get(host, params=payload)
			return r.json()
		except:
			print("Something went wrong with device %s. Retry. Attempt %s/5" % (credential["host"], attempt))
	else:
		print("Something went completely wrong with device %s" % device["host"])
		print("It was not possible to etablish a connection to the device. Please check the devices.yaml and your firewall.")
		return False

def readDevices():
    try:
        with open("devices.yaml", 'r') as stream:
            try:
                devices = yaml.safe_load(stream)
                return devices
            except yaml.YAMLError as exc:
                print(exc)
    except FileNotFoundError:
        raise FileNotFoundError("Could not find devices.yaml")

def printStatus(devices):
    print("Host\t\t\tName\tVersion")

    for device, settings in devices.items():
        status = getStatus(settings)

        if status:
            print("%s\t%s\t%s" % (
                settings["host"],
                status["Status"]["FriendlyName"],
                status["StatusFWR"]["Version"]
            ))
        else:
            print("%s\t%s\t%s" % (
            device["host"],
                '-',
                '-'
            ))

#Ask for operation
print('Welcome to the tasmota-updater, what do you want to do?')
print('1. Bulk update all devices to a specific version')
print('2. Get device infos for all devices')
operation = int(input('Your choice: '))

#Read devices from devices.yaml
devices = readDevices()

if operation == 1:
    #Ask for version to be installed
    version = input ("Enter version to be installed (e.g. 7.2.0): ")

    #Show status
    printStatus(devices)

    #Flash Minimal Version
    print("Let's start with the minimal firmware. This may take a few minutes.")
    bulkUpdate(devices, version, 'minimal')

    #Show Status
    time.sleep(15)
    printStatus(devices)
    input("Is everything correct? If you want to continue press ENTER.")

    #Flash Regular Version
    print("Let's start with the regular firmware. This may take a few minutes.")
    bulkUpdate(devices, version, '')

    #Show Status
    time.sleep(15)
    printStatus(devices)
    input("Press Enter to finish...")
elif operation == 2:
    #Show status
    printStatus(devices)
