#Copyright 2016-2017 OSIsoft, LLC
#
#Licensed under the Apache License, Version 2.0 (the "License")
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#<http:#www.apache.org/licenses/LICENSE-2.0>
#
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.

# ************************************************************************

# Note: this code was built against the OSIsoft Relay Beta version 1.2.000.0000  and OMF v1.0
#OMF Specifications http://omf-docs.osisoft.com/en/v1.0/index.html

# Import packages
import sys, json, random, time, platform, requests, socket, datetime, linux_metrics
from gps import *
import threading

# Specify the number of seconds to sleep in between value messages
number_of_seconds_between_value_messages = 5

# This name will be automatically populated (or you can hard-code it) this is the name
# of the PI AF Element that will be created, and it'll be included in the names
# of PI Points that get created as well
device_name = (socket.gethostname())+ ""

# ************************************************************************

# Specify the address of the destination endpoint
target_url = "https://59051njsjwss.cloudapp.net:8881/ingress/messages"

# Specify the producer token this will be the parent AF element beneath which the new AF element will appear,
# and it will be part of the prefix of all PI Points that are created by this script
producer_token = "OMF" + ""

# Specify a device type (optional) 
# This will be added as a static string attribute to the AF Element that is created
device_type = "Qualcomm DragonBoard"

# If self-signed certificates are used (true by default), do not verify HTTPS SSL certificates
verify_SSL = False

# Suppress insecure HTTPS warnings, if an untrusted certificate is used by the target endpoint
if verify_SSL == False:
    requests.packages.urllib3.disable_warnings()

# ************************************************************************    
# Initialize the GPS polling class

# Initialize a global variable
gpsd = None 
class GpsPoller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        global gpsd 
        gpsd = gps(mode=WATCH_ENABLE) 
        self.current_value = None
        self.running = True

    def run(self):
        global gpsd
        while gpsp.running:
            gpsd.next()

# ************************************************************************
# Below is where you can initialize any global variables that are needed by your application
# certain sensors, for example, will require global interface or sensor variables

# The following function is where you can insert specific initialization code to set up
# sensors for a particular IoT module or platform
def initialize_sensors() :
    print("--- Sensors initializing...")
    try: 
        #For a Raspberry Pi, for example, to set up pins 4 and 5, you would add 
        #GPIO.setmode(GPIO.BCM)
        #GPIO.setup(4, GPIO.IN)
        #GPIO.setup(5, GPIO.IN)
        print("--- Sensors initialized!")    
    except Exception as e:
        # Log any error, if it occurs
        print((str(datetime.datetime.now())) + " An error has occurred when initializing sensors: " + str(e))


# ************************************************************************
# The following function you can customize to allow this script to send along any
# number of different data values, as long as the values that you send here match
# up with the values defined in the "DataValuesType" OMF message type (see the next section)
# In this example, dataFromDevice is an array defined in the device code

def create_data_values_container_message(target_container_id, dataFromDevice):
    # Get the current timestamp
    d = str(datetime.datetime.now())
    timestamp = datetime.datetime.utcnow().isoformat() + 'Z'
    # Assemble a JSON object containing the container Id and any data values
    data_values_JSON = [
        {
            "containerid": target_container_id,
            "values": [
                {
                    "Time": timestamp,
                    "Machine Type": str(dataFromDevice[0]),
                    "Platform Type": str(dataFromDevice[1]),
                    #"Processor Type": dataFromDevice[2],
                    "CPU Usage": float(dataFromDevice[3]),
                    "Disk Busy Time": float(dataFromDevice[4]),
                    "Memory Used": float(dataFromDevice[5]),
                    "Total Memory": float(dataFromDevice[6]),
                    "Wi-Fi Bits Received": float(dataFromDevice[7]),
                    "Wi-Fi Bits Sent": float(dataFromDevice[8]),
                    "Latitude": float(dataFromDevice[9]),
                    "Longitude": float(dataFromDevice[10])
                }
            ]
        }
    ]
    return data_values_JSON

# ************************************************************************

# Define a helper function to allow easily sending web request messages
# this function can later be customized to allow you to port this script to other languages.
# All it does is take in a data object and a message type, and it sends an HTTPS
# request to the target OMF endpoint
def sendOMFMessageToEndPoint(message_type, OMF_data):
        try:  
                # Assemble headers that contain the producer token and message type
                msg_header = {"producertoken": producer_token, "messagetype": message_type, "action": "create", "messageformat": "JSON", 'omfversion': '1.0'}
                # Send the request, and collect the response
                response = requests.post(target_url, headers=msg_header, data=json.dumps(OMF_data), verify=verify_SSL, timeout=30)
                # Print a debug message, if desired
                print('Response from relay from the "{0}" message: {1} {2}'.format(message_type, response.status_code, response.text))
        except Exception as e:
                # Log any error, if it occurs
                print((str(datetime.datetime.now())) + " An error occurred during web request: " + str(e))    
                    

# ************************************************************************

def sendInitialOMFMessages(deviceId):
    # Update the global variable that contains the unique device ID
    device_name = deviceId
    
    # Update the names
    data_values_type_name        = device_name + "_" + "data_values_type"

    # This will also end up becoming part of the PI Points names;
    global data_values_container_name
    data_values_container_name   = device_name + "_" + "data_values_container"
    
    # This will also end up becoming part of the Element template name
    # You will want to make this different for each general class of IoT module that you use
    assets_message_type_name     = "Type" + "_DragonBoard"
    
    # Create a JSON packet to define the the message types that will be used
    
    # ************************************************************************
    #OMF messages fall into three categories: Type, Container, and Data messages. 
    #Within each category, three types of actions can be specified: Create, Update, and Delete.
    #Each message bulks individual JSON objects into a JSON array. 
    #Within a given array, all objects must be of the same message type: Type, Container, or Data. 
    
    types = [    
        {
            #This will be dynamic (pi points) attributes in the element template
            "id": data_values_type_name,
            "type": "object",
            "classification": "dynamic",
            "properties": {
                "Time": {
                    "format": "date-time",
                    "type": "string",
                    "isindex": True
                },
                "Machine Type": {
                    "type": "string"
                },
                "Platform Type": {
                    "type": "string"
                },
                #"Processor Type": {
                #    "type": "string"
                #},
                "CPU Usage": {
                    "type": "number"
                },
                "Disk Busy Time": {
                    "type": "number"
                },
                "Memory Used": {
                    "type": "number"
                },
                "Total Memory": {
                    "type": "number"
                },
                "Wi-Fi Bits Received": {
                    "type": "number"
                },
                "Wi-Fi Bits Sent": {
                    "type": "number"
                },
                "Latitude": {
                    "type": "number"
                },
                "Longitude": {
                    "type": "number"
                }
            }
        },
        {
            #This will be static attributes in the element template
            "id": assets_message_type_name,
            "type": "object",
            "classification": "static",
            "properties": {
                "Name": {
                    "type": "string",
                    "isindex": True
                },
                "Device Type": {
                    "type": "string"
                },
                "Data Ingress Method": {
                    "type": "string"
                }
                # For example, to add a number-type static attribute for the device model, you would add
                #"Model": {
                #   "type": "number"
                #}
            }
        }    
    ]
    
    # Create a JSON packet containing the data container for the values defined indata_values_type_name;
    # in this case, we're auto-populating the Device Type, but you can manually hard-code in values if you wish;
    
    containers = [
        {
        "id": data_values_container_name,
        "typeid": data_values_type_name
        }
    ]
    
    assets = [
        {
            "typeid": assets_message_type_name,
            "values": [
                {
                    "Name": device_name,
                    "Device Type": device_type,
                    "Data Ingress Method": "OMFv1.0"
                }
            ]
        }
    ]
    
    # Create a JSON packet containing the links to be made, which will both position the new PI AF
    # Element, so it will show up in AF, and will associate the PI Points that will be created with that Element
    # A Link is a pre-defined type with the typeid __Link, therefore we did not define it in the types above
    
    links = [
        {
            "typeid": "__Link",
            "values": [ {
                    "source": {
                            "typeid": assets_message_type_name,
                            "index": "_ROOT"
                    },
                    "target": {
                            "typeid": assets_message_type_name,
                            "index": device_name
                    }
            },{
                    "source": {
                            "typeid": assets_message_type_name,
                            "index": device_name
                    },
                    "target": {
                            "containerid": data_values_container_name
                    }
            }]
        }
    ]
    # Send the messages to create the types, containers, static data and links, which will finish making the AF element and will set up links for PI Points
    sendOMFMessageToEndPoint("Type", types)
    sendOMFMessageToEndPoint("Container", containers)
    sendOMFMessageToEndPoint("Data", assets)
    sendOMFMessageToEndPoint("Data", links)
    
    # Initialize sensors prior to sending data (if needed), using the function defined earlier
    initialize_sensors()

# ************************************************************************

def sendDataValueMessage(dataFromDevice):
    # Call the custom function that builds a JSON object that contains new data values see the beginning of this script
    values = create_data_values_container_message(data_values_container_name, dataFromDevice)
    # Send the data to the relay it will be stored in a point called <producer_token>.<stream Id>
    sendOMFMessageToEndPoint("Data", values)

# ************************************************************************

# Define the main program
if __name__ == '__main__':
    # Start the GPS polling thread
    gpsp = GpsPoller() 
    gpsp.start()
    
    # Instruct the device to run the init code
    sendInitialOMFMessages(device_name)

    # Loop indefinitely, sending events conforming to the value type that we defined earlier
    print("--- Next sending live data every " + str(number_of_seconds_between_value_messages) + " second(s) for device " + device_name + "...")
    while (1):
        # Wait for the sensors to initialize
        time.sleep(0.01)
        
        # Build a data object
        # Include metadata and all analog readings
        dataFromDevice = [
            # Gather general information about the device
            platform.machine(),
            platform.platform(),
            platform.processor(),
            str(100 - (linux_metrics.cpu_stat.cpu_percents(sample_duration=1))['idle']),
            str(linux_metrics.disk_stat.disk_busy('mmcblk0', sample_duration=1)),
            str(linux_metrics.mem_stat.mem_stats()[0]),
            str(linux_metrics.mem_stat.mem_stats()[1]),
            str(linux_metrics.net_stat.rx_tx_bits('wlan0')[0]),
            str(linux_metrics.net_stat.rx_tx_bits('wlan0')[1]),
            # Gather readings from gps
            str(gpsd.fix.latitude),
            str(gpsd.fix.longitude)
        ]
    
        # Send the message with realtime data
        sendDataValueMessage(dataFromDevice)    
        
        # Wait until the next send
        time.sleep(number_of_seconds_between_value_messages)
