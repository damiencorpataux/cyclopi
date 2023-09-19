import microio
import microio.io
import config
import microio.http.static
import microio.http.websocket
import microio.wifi.station
import aioweb
import lis3dh
import json
import machine

# Notes:
# See the jerk, snap, etc: https://en.wikipedia.org/wiki/Fourth,_fifth,_and_sixth_derivatives_of_position

i2c = machine.I2C(sda=machine.Pin(21), scl=machine.Pin(22))
iomap = microio.io.IOMap({
    'acceleration': lis3dh.LIS3DH_I2C(i2c, address=0x19)
})

app = aioweb.App()

@app.route('/')
async def websocket(r, w):
    await microio.http.static.handler(r, w, file='index.html')

ws_clients = set()
@app.route('/ws')
async def websocket(r, w):
    ws = await aioweb.WebSocket.upgrade(r, w)
    ws_clients.add(ws)
    print(f'\nReceived websocket connection {ws} ({len(ws_clients)} clients)')
    try:
        while True:
            await microio.asyncio.sleep(1)
    finally:
        ws_clients.discard(ws)
        print(f'\nClosed websocket connection {ws} ({len(ws_clients)} clients)')

import sys
async def broadcast(poll_period=1/3, print_period=1):
    i = 0
    while True:
        if True:#ws_clients:
            acceleration = list(iomap['acceleration'].acceleration)
            if 0 == i % (print_period/poll_period):
                print(f'\nAcceleration: {acceleration} (i={i})')
            for ws in ws_clients:
                try:
                    await ws.send(json.dumps(acceleration))
                    sys.stdout.write('.')
                except Exception as e:
                    ws_clients.discard(ws)
                    print(f'\nClosed websocket connection {ws} ({len(ws_clients)} clients): {e.__class__.__name__}: {e}')

        await microio.asyncio.sleep(poll_period)
        i += 1

loop = microio.asyncio.get_event_loop()
loop.create_task(app.serve())
loop.create_task(broadcast())
loop.create_task(microio.wifi.station.start_multi(
    configs=getattr(config, 'wifi', []),
    rescan=True))
loop.run_forever()
