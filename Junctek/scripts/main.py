from bleak import BleakScanner
from bleak import BleakClient
from bleak import BleakError
import asyncio
import logger
import sys
import requests
import os
import json
import mqtt
import sensors
from datetime import datetime, timezone
import atexit

lgr                 = logger.Logger('info')

charging            = False

params = {
    "voltage":          "c0",       
    "current":          "c1",       # Amps
    "cur_soc":          "d0",       # %
    "dir_of_current":   "d1",   
    "ah_remaining":     "d2",
    "discharge":        "d3",		# todays total in kWh
    "charge":           "d4",       # todays total in kWh
    "accum_charge_cap": "d5",       # accumulated charging capacity Ah (/1000)
    "mins_remaining":   "d6",
    "power":            "d8",       # Watt
    "temp":             "d9",       # C
    "full_charge_volt": "e6",
    "zero_charge_volt": "e7",
}

params_keys         = list(params.keys())
params_values       = list(params.values())

if len(sys.argv) == 2:
    running_local       = sys.argv[1]
else:
    running_local       = False

if not running_local:
    # Get Options
    with open("/data/options.json", mode="r") as data_file:
        config = json.load(data_file)
    debug               = config.get('debug')
    mac_address         = config.get('macaddress')
    battery_capacity    = config.get('battery capacity')
    battery_voltage     = config.get('voltage')
else:
    debug               = True
    mac_address         = '38:3b:26:79:6f:c5' #38:3b:26:79:6f:c5
    battery_capacity    = 400
    battery_voltage     = 48

MqqtToHa            = mqtt.MqqtToHa(lgr)

class DeviceNotFoundError(Exception):
    pass

async def discover():
    try:
        devices    = await BleakScanner.discover()

        lgr.debug("Found Devices")
        for device in devices:
            lgr.info(f"BT Device found:\nName: {device.name}\nAddress: {device.address}")
            lgr.debug(device)

        lgr.debug("Finished discovery")
    except Exception as e:
        lgr.error(f" {str(e)} on line {sys.exc_info()[-1].tb_lineno}")

async def process_data(_, value):
    global charging
    
    try:
        data = str(value.hex())

        # split bs into a list of all values and hex keys
        bs_list             = [data[i:i+2] for i in range(0, len(data), 2)]

        # reverse the list so that values come after hex params
        bs_list_rev         = list(reversed(bs_list))

        values      = {}
        # iterate through the list and if a param is found,
        # add it as a key to the dict. The value for that key is a
        # concatenation of all following elements in the list
        # until a non-numeric element appears. This would either
        # be the next param or the beginning hex value.
        for i in range(len(bs_list_rev)-1):
            if bs_list_rev[i] in params_values:
                value_str = ''
                j = i + 1
                while j < len(bs_list_rev) and bs_list_rev[j].isdigit():
                    value_str = bs_list_rev[j] + value_str
                    j += 1

                position    = params_values.index(bs_list_rev[i])

                key         = params_keys[position]
                
                values[key] = value_str
                
        if debug:
            if not values: 
                lgr.warning(f"Nothing found for {data}")
            else:
                lgr.debug(f"Raw values: {values}")

        # now format to the correct decimal place, or perform other formatting
        for key,value in list(values.items()):
            if not value.isdigit():
                del values[key]

            val_int = int(value)                
            if key == "voltage":
                voltage   = val_int / 100 

                # Only keep valid values leave out unrealistically values
                if voltage > ( battery_voltage - (battery_voltage * 0.2)):
                    values[key] = voltage               
            elif key == "current":
                values[key] = val_int / 100
                
                if charging == False:
                    values["current"] *= -1
            elif key == "discharge":
                values[key] = val_int / 100000
                charging = False
            elif key == "charge":
                values[key] = val_int / 100000
                charging = True
            elif key == "dir_of_current":
                if value == "01":
                    charging = True
                else:
                    charging = False
            elif key == "ah_remaining":
                values[key] = val_int / 1000
            elif key == "mins_remaining":
                values[key] = val_int
            elif key == "power":
                values[key] = val_int / 100
                
                if charging == False:
                    values["power"] *= -1
            elif key == "temp":
                temp    = val_int - 100

                if temp > 10:
                    values[key] = temp
            elif key == "accum_charge_cap":
                values[key] = val_int / 1000    

        # Calculate percentage
        if "ah_remaining" in values:
            values["soc"] = values["ah_remaining"] / battery_capacity * 100

        # Now it should be formatted corrected, in a dictionary
        if debug:
            lgr.debug(f"Final values: {values}")

        await send_to_ha(values)

    except Exception as e:
        lgr.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")

async def send_to_ha(values):
    try:           
        for key, value in values.items():
            if not key in sensors.sensors:
                continue

            if key == "ah_remaining" or key == "cap" or key == "accum_charge_cap" or key == "discharge" or key == "charge":
                val   = round(value * 48 , 2)
            elif key == "mins_remaining":
                val   = round(value , 0)
            else:
                val   = round(value , 1)

            if val > -99:
                MqqtToHa.send_value(key, val)
                
        # https://www.home-assistant.io/docs/configuration/templating/#time
        # 2023-07-30T20:03:49.253717+00:00
        timestring  = str(datetime.now(datetime.now().astimezone().tzinfo).isoformat())
        if debug:
            lgr.debug(f"Sending time: {timestring}") 

        MqqtToHa.send_value('last_message', timestring, False)
    except Exception as e:
        lgr.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")

disconnect_event    = asyncio.Event()

def disconnected_callback(client):
    lgr.debug(f"Disconnected {client}")
    disconnect_event.set()

async def main(device_mac):
    global disconnect_event

    #target_name_prefix = "BTG"
    read_characteristic_uuid = "0000fff1-0000-1000-8000-00805f9b34fb"
    #send a message to get all the measurement values 
    #send_characteristic_uuid = "0000fff2-0000-1000-8000-00805f9b34fb"
    #message = ":R50=1,2,1,\n"
    #interval_seconds = 60

    while True:
        device = None
        while device is None:
            device = await BleakScanner.find_device_by_address( device_mac )
            if device is None:
                lgr.error(f"Could not find device with address '{device_mac}'")
                #raise DeviceNotFoundError

        try:
            async with BleakClient(device, disconnected_callback=disconnected_callback) as client:
                lgr.info(f"Connected to {device_mac}")
                await client.start_notify(read_characteristic_uuid, process_data)

                await disconnect_event.wait()
        except BleakError as e:
            lgr.error(f"Error: {e}")
            #continue  # continue in error case 
        except TimeoutError as e:
            pass
        except Exception as e:
            lgr.error(f" {str(e)} on line {sys.exc_info()[-1].tb_lineno}")

def on_finish():
    lgr.debug(f"Exiting")

atexit.register(on_finish)

if __name__ == "__main__":
    try:
        if mac_address == '':
            lgr.debug("Starting discovery")
            asyncio.run(discover())
        else:
            lgr.debug("Starting connection")
            asyncio.run(main(mac_address))
    except KeyboardInterrupt:
        lgr.debug("ctrl+c pressed")
    except Exception as e:
        lgr.error(f" {str(e)} on line {sys.exc_info()[-1].tb_lineno}")
        """         async with BleakClient(device) as client:
            lgr.debug("connected")
            await client.stop_notify(read_characteristic_uuid) """