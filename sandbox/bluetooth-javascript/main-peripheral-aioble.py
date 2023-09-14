import sys
sys.path.append("")

from micropython import const
import uasyncio as asyncio
import bluetooth
import aioble
import struct
import random
import json
import time


_ENV_SENSE_UUID = bluetooth.UUID("90D3D000-C950-4DD6-9410-2B7AEB1DD7D8")  # custom service definition
_ENV_SENSE_TEMP_UUID = bluetooth.UUID("90D3D001-C950-4DD6-9410-2B7AEB1DD7D8") # org.bluetooth.characteristic.temperature
_ENV_SENSE_RECV_UUID = bluetooth.UUID("90D3D002-C950-4DD6-9410-2B7AEB1DD7D8")
# _ENV_SENSE_IS_RECORDING_UUID = bluetooth.UUID("90D3D00B-C950-4DD6-9410-2B7AEB1DD7D8")

# org.bluetooth.characteristic.gap.appearance.xml
_ADV_APPEARANCE_GENERIC_THERMOMETER = const(768)

# How frequently to send advertising beacons.
_ADV_INTERVAL_US = 250_000


# Register GATT server.
device_service = aioble.Service(_ENV_SENSE_UUID)
temp_characteristic = aioble.Characteristic(device_service, _ENV_SENSE_TEMP_UUID, read=True, notify=True)
recv_characteristic = aioble.Characteristic(device_service, _ENV_SENSE_RECV_UUID, write=True, read=True, notify=True)

aioble.register_services(device_service)

_timer_start = time.ticks_ms()
_connected_timer_start = time.ticks_ms()

async def temp_sensor():
    # This would be periodically polling a hardware sensor.
    t = 24.5
    while True:
        # encoded_temp = struct.pack(">h", int(t * 100))  # big endian
        data = {'t': t}
        data_encoded = bytes(json.dumps(data), 'utf8')
        print(f'Total time: {int(time.ticks_diff(time.ticks_ms(), _timer_start) / 1000)}, Connected time: {int(time.ticks_diff(time.ticks_ms(), _connected_timer_start) / 1000)}, Temperature: {t}')
        temp_characteristic.write(data_encoded, send_update=True)
        t += random.uniform(-0.5, 0.5)
        await asyncio.sleep_ms(1000)

# FIXME: This is not working.
async def recv_actor():
    print('READING', recv_characteristic)
    while True:
        print('READ awaiting')
        data = await recv_characteristic.read()
        print('READ awaited', data)
        await asyncio.sleep(1)

# Serially wait for connections. Don't advertise while a central is connected.
async def peripheral_task():
    while True:
        async with await aioble.advertise(
            _ADV_INTERVAL_US,
            name="MicroIO_BLE",
            services=[_ENV_SENSE_UUID],
            appearance=_ADV_APPEARANCE_GENERIC_THERMOMETER,
        ) as connection:
            print("Connection from:", connection.device)
            global _connected_timer_start
            _connected_timer_start = time.ticks_ms()
            #await connection.disconnected() # Don't use this as it crashes everything after 60 seconds when timeout happens.
            while connection.is_connected() == True:
                #print(f'Connection status: {connection.is_connected()}')
                await asyncio.sleep_ms(1000)
            print('Connection lost. switching back to advertising mode')


async def main():
    print('Starting Bluetooth sensor example.')
    await asyncio.gather(
        asyncio.create_task(temp_sensor()),
        asyncio.create_task(recv_actor()),
        asyncio.create_task(peripheral_task()),
    )
    print('Example finished.')

asyncio.run(main())
