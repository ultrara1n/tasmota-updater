#!/usr/bin/python

import yaml
import json
import os
import urllib.request
import requests
import time
from tabulate import tabulate

def downloadFirmware(version, filename):
    #Compose download url
    file_url = 'https://github.com/arendst/Tasmota/releases/download/v' + version + '/' + filename

    #Create folder
    path = 'firmware/' + version
    if not os.path.exists(path):
        os.makedirs(path)

    #Download file
    save_path = path + '/' + filename

    if not os.path.isfile(path + '/' + filename):
        print('Download ' + filename)
        urllib.request.urlretrieve (file_url, save_path)

def sendUpdate(host, filename, version):
    url = 'http://' + host + '/u2'

    firmware_path = 'firmware' + '/' + version + '/' + filename

    try:
        files = {'file': open(firmware_path, 'rb')}
    except FileNotFoundError:
        raise FileNotFoundError("Please make sure that firmware file {0} exists.".format(firmware_path))

    for attempt in range(5):
        try:
            r = requests.post(url, files=files)
        except:
            print("Something went wrong with device %s. Retry. Attempt %s/5" % (host, attempt))
        else:
            break
    else:
        raise ConnectionError("Something went wrong with device {0}!".format(host))

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
			print("Something went wrong with device %s. Retry. Attempt %s/5" % (device["host"], attempt+1))
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
    status_array = []
    counter = 1
    for settings in devices.items():
        status = getStatus(settings)
        iteration_array = []
        iteration_array.append(counter)
        iteration_array.append(settings["name"])
        iteration_array.append(settings["host"])

        if status:
            iteration_array.append(status["Status"]["FriendlyName"][0])
            iteration_array.append(status["StatusFWR"]["Version"])
        else:
            iteration_array.append('-')
            iteration_array.append('-')
        status_array.append(iteration_array)
        counter += 1

    print("\n"+tabulate(status_array, headers=["#","Name","Host","Tasmota Name","Tasmota Version"]))

def determineFilename(type):
    if type is None:
        return 'tasmota.bin'
    else:
        return 'tasmota-' + type + '.bin.gz'

def bulkUpdate(devices, version, type):
    for settings in devices.items():
        if type == '':
            type = settings['type']
        downloadFirmware(version, determineFilename(type))
        sendUpdate(settings["host"], determineFilename(type), version)

def updateProcedure(version):
    #Show status
    printStatus(devices)
    input("\nThese devices will be updated, proceed with ENTER")

    #Flash Minimal Version
    print("\nLet's start with the minimal firmware. This may take a few minutes.")
    bulkUpdate(devices, version, 'minimal')

    #Show Status
    time.sleep(15)
    printStatus(devices)
    input("\nIs everything correct? If you want to continue press ENTER.")

    #Flash Regular Version
    print("\nLet's start with the regular firmware. This may take a few minutes.")
    bulkUpdate(devices, version, '')

    #Show Status
    time.sleep(15)
    printStatus(devices)
    input("Press ENTER to finish...")

def getNewestVersion():
    latest_release = requests.get('https://api.github.com/repos/arendst/Tasmota/releases/latest')

    release_json = json.loads(latest_release.text)

    return { 'release_name': release_json["name"], 'version': release_json["tag_name"].replace('v','')}

def checkDeviceExistence(devices, selectedDevices):
    print('Hi')

#Ask for operation
print('Welcome to the tasmota-updater, what do you want to do?')
print('1. Bulk update all devices to the newest version available')
print('2. Bulk update all devices to a specific version')
print('3. Update one device to newest version')
print('4. Update one device to specific version')
print('5. Update selected devices to newest version')
print('6. Get device infos for all devices')
print('7. Show newest Tasmota version\n')
operation = int(input("Your choice: "))

#Read devices from devices.yaml
devices = readDevices()

if operation == 1:
    newestVersion = getNewestVersion()

    input("\n" + newestVersion['release_name'] + " looks like the latest release. Press ENTER to confirm.")

    #Start update
    updateProcedure(newestVersion['version'])
elif operation == 2:
    #Ask for version to be installed
    version = input ("Enter version to be installed (e.g. 7.2.0): ")

    #Start update
    updateProcedure(version)

elif operation == 3:
    printStatus(devices)

    number = int(input("\nEnter number of device to be updated: "))

    counter = 1
    for device, settings in devices.items():
        if counter == number:
            devices = {device: settings},
            break
        counter += 1

    devices = devices[0]
    newestVersion = getNewestVersion()

    input("\n" + newestVersion['release_name'] + " looks like the latest one. Press ENTER to start update.")

    updateProcedure(newestVersion['version'])
elif operation == 4:
    printStatus(devices)

    number = int(input("\nEnter number of device to be updated: "))

    counter = 1
    for device, settings in devices.items():
        if counter == number:
            devices = {device: settings},
            break
        counter += 1

    devices = devices[0]

    version = input ("Enter version to be installed (e.g. 7.2.0): ")

    updateProcedure(version)

elif operation == 5:
    printStatus(devices)

    concatDevices = str(input('\nChose devices to be updated (comma separated): '))
    concatDevices.replace(" ", "")
    deviceIndexList = concatDevices.split(',')

    counter = 1
    chosenDevices = {}
    for device, settings in devices.items():
        if str(counter) in deviceIndexList:
            chosenDevices[device] = settings
        counter += 1

    devices = chosenDevices
    newestVersion = getNewestVersion()

    input("\n" + newestVersion['release_name'] + " looks like the latest one. Press ENTER to start update.")

    updateProcedure(newestVersion['version'])

elif operation == 6:
    #Show status
    printStatus(devices)

elif operation == 7:
    newestVersion = getNewestVersion()
    print('Release name: ' + newestVersion['release_name'])
    print('Version number: ' + newestVersion['version'])
    # print(getNewestVersion())
