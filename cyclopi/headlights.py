import microio
import microio.io
import microio.io.neopixel
import microio.animatrix.blend
import microio.animatrix.tx.fade
import microio.animatrix.gx.chase
import microio.animatrix.gx.alphanum
import microio.animatrix.gx.static
import microio.animatrix.gx.mod
import microio.animatrix.control
import microio.http.static_directory
import microio.http.websocket
import microio.wifi.station

import config

import machine
from lib import lis3dh


C_leds_square = 25
C_leds_circle = 24

i2c = machine.I2C(sda=machine.Pin(21), scl=machine.Pin(22))
iomap = microio.io.IOMap({
    'pixels': microio.io.neopixel.factory(16, 64),
    'acceleration': lis3dh.LIS3DH_I2C(i2c, address=0x19)
})

def output_pixels(offset=0, map_pixel=None):
    def inner(colors):
        for i, color in enumerate(colors):
            if map_pixel:
                i = map_pixel(i)
            iomap['pixels'][i+offset] = color
        iomap['pixels'].write()
    return inner

symbols = {
    '<': 0b01000_01100_01110_01100_01000,
    '>': 0b00010_00110_01110_00110_00010,
    '.': 0b11111_10001_10101_10001_11111,
    '!': 0b00100_00100_00100_00000_00100,
    # '<': 0b00010001_00110011_01110111_11111111_11111111_01110111_00110011_00010001,
    # '>': 0b10001000_11001100_11101110_11111111_11111111_11101110_11001100_10001000,
    # '.': 0b11111111_10000001_10111101_10111101_10111101_10111101_10000001_11111111,
    # # '!': 0b00011000_00100100_00100100_01011010_01011010_11011011_11000011_11111111,
    # '!': 0b00011000_00011000_00011000_00011000_00011000_00000000_00011000_00011000,
}
# tx = {
#     'fade': ('fade', microio.animatrix.tx.fade.Ratio(3), microio.animatrix.tx.apply_iterative())
# }
# gx = {
#     'letter': microio.animatrix.gx.alphanum.Letter(
#         text='! >>  ! >>  ! >>  ! >>',
#         on=(6,9,3),
#         side=8),
# }
matrices = {
    'circle': microio.animatrix.Matrix(
        values=[(10,10,10)] * C_leds_circle,
        output=output_pixels(offset=C_leds_square),
        blend=microio.animatrix.blend.iterative(microio.animatrix.blend.add, lower=0, upper=255),
        fx=[
            # tx['fade'],
            ('fade', microio.animatrix.tx.fade.Ratio(1.25), microio.animatrix.tx.apply_iterative()),
            ('chase-right',
                microio.animatrix.gx.mod.Loop(
                    fx=microio.animatrix.gx.mod.Step(
                        # fx=microio.animatrix.gx.chase.Chase(C_leds_circle, value_on=(200,10,1), value_off=None)))),
                        # fx=microio.animatrix.gx.chase.Chase(C_leds_circle, value_on=(150,30,5), value_off=None)))),
                        factor=2,
                        leap=1,
                        fx=microio.animatrix.gx.chase.Chase(C_leds_circle, value_on=(255,20,0))))),
            ('chase-left',
                microio.animatrix.gx.mod.Loop(
                    fx=microio.animatrix.gx.mod.Step(
                        factor=2,
                        leap=1,
                        fx=microio.animatrix.gx.chase.Chase(C_leds_circle, value_on=(255,0,3), reverse=True)))),
            ('stop',
                microio.animatrix.gx.mod.Step(
                    factor=0,
                    fx=microio.animatrix.gx.static.Loop(
                        ((255,0,0),) * C_leds_circle))),
                        # *(((0,0,0),) * C_leds_circle,) * 1))),
        ]),
    'square': microio.animatrix.Matrix(
        values=[(10,10,10)] * C_leds_square,
        output=output_pixels(offset=0, map_pixel=microio.io.neopixel.map2D(5, 5, [[(0,'north')]])),
        blend=microio.animatrix.blend.iterative(microio.animatrix.blend.add, lower=0, upper=255),
        fx=[
            # tx['fade'],
            ('fade', microio.animatrix.tx.fade.Ratio(1.25), microio.animatrix.tx.apply_iterative()),
            ('symbol',
                microio.animatrix.gx.mod.Step(
                    factor=2,
                    fx=microio.animatrix.gx.mod.Loop(
                        fx=microio.animatrix.gx.alphanum.Letter(
                            text=' '*30 + '♥  ♡  ',
                            on=(200,100,10),
                            off=(-255,-255,-255),
                            side=5)))),
            ('stop',
                microio.animatrix.gx.mod.Step(
                    factor=0,
                    fx=microio.animatrix.gx.static.Loop(((255,0,0),)*C_leds_square))),
        ])
}

# # TODO:
# ble = microio.ble.Peripheral(services={
#     'service-uuid': {
#         'characteristic-uuid': {
#             'initial': '{"json":1}',
#             'write': True,
#             'read': True,
#             'notify':True}
#     }
# })
# ble.services['service-uuid']['characteristic-uuid'].read()
# ble.services['service-uuid']['characteristic-uuid'].write()

import math
def vector(x, y, z):
    magnitude = math.sqrt(x**2 + y**2 + z**2)
    elevation = math.atan2(math.sqrt(x**2 + y**2), z)  # Polar angle theta (elevation angle)
    azimuth = math.atan2(y, x)                         # Azimuthal angle phi (azimuth angle)
    return magnitude, math.degrees(elevation), math.degrees(azimuth)

import uasyncio as asyncio
# class Motion:
#     pass  # FIXME: Re-implement BrakeDetection in Motion.

class BrakeDetection:
    
    STANDARD_GRAVITY=9.806

    def __init__(self, imu, threshold=0.25, poll_interval=0.1):
        self.imu = imu
        self.poll_interval = poll_interval
        self.threshold = threshold
        self.acceleration = [0.0, 0.0, 0.0]
        self.acceleration_delta = [0.0, 0.0, 0.0]
        # self.acceleration_history = []
        self.magnitude = 0
        self.magnitude_delta = 0
        self.velocity = [0.0, 0.0, 0.0]
        self.velocity_delta = [0.0, 0.0, 0.0]
        # self.speed = 0
        # self.speed_delta = 0
        self.brake = False
        # if imu.device_check():
        #     imu.range = lis3dh.RANGE_2_G  # set range of accelerometer (can be RANGE_2_G, RANGE_4_G, RANGE_8_G or RANGE_16_G).

    def read(self):
        new_acceleration = list(self.imu.acceleration)
        self.acceleration_delta = [new_acceleration[i] - self.acceleration[i] for i in range(3)]
        self.acceleration = new_acceleration
        # self.acceleration_history = [self.acceleration] + self.acceleration_history[:2]
        new_magnitude = math.sqrt(sum(a**2 for a in self.acceleration))
        self.magnitude_delta =  new_magnitude - self.magnitude
        self.magnitude = new_magnitude
        # Compute velocity and speed
        new_velocity = [self.velocity[axis] + (self.acceleration[axis] * self.STANDARD_GRAVITY * self.poll_interval) for axis in range(3)]
        self.velocity_delta = [new_velocity[axis] - self.velocity[axis] for axis in range(3)]
        self.velocity = new_velocity
        # Detect break
        self.brake = self.acceleration_delta[2] < -self.threshold  # self.magnitude_delta < -self.threshold
        # FIXME: Compute vector
        magnitude, elevation, azimuth = vector(*self.acceleration)
        print(f'Vector: {self.acceleration_delta} magnitude={magnitude:.2f}G, elevation={elevation:.2f}°, azimuth={azimuth:.2f}°')

#         # Display info to console
#         print(f'''
# {self.brake}, values in ㎨:
# a = {[round(a, 2) for a in self.acceleration]},
# magnitude = {self.magnitude:.2f},
# magnitude_delta = {self.magnitude_delta:.2f},
# velocity = {[round(x, 2) for x in self.velocity]}
# velocity_delta = {[round(x, 2) for x in self.velocity_delta]}''')
#         # print(f'History: {self.acceleration_history}')
        
    async def start(self):
        while True:
            last_break = self.brake
            self.read()
            # Display brake signal if deceleration is detected
            if self.brake != last_break:
                control.handle_request(json.dumps({"fx": {
                    "circle.stop.mod-Step": {"factor": 2 if self.brake else 0},
                    "square.stop.mod-Step": {"factor": 1 if self.brake else 0},
                    "circle.chase-left.mod-Loop.mod-Step": {"factor": 0 if self.brake else 2},
                    "circle.chase-right.mod-Loop.mod-Step": {"factor": 0 if self.brake else 2},
                }}))
            await asyncio.sleep(.1)

import json
def display_ip(wlan):
    async def inner():
        original_text = matrices['square'].fx[1][1].fx.fx.text
        original_speed = matrices['square'].fx[1][1].factor
        control.handle_request(json.dumps({"fx":{"square.symbol.mod-Step.mod-Loop.alphanum-Letter": {"text": ' IP= ' + wlan.ifconfig()[0]}}}))
        control.handle_request(json.dumps({"fx":{"square.symbol.mod-Step": {"factor": 10}}}))
        await microio.asyncio.sleep(24)
        control.handle_request(json.dumps({"fx":{"square.symbol.mod-Step.mod-Loop.alphanum-Letter": {"text": original_text}}}))
        control.handle_request(json.dumps({"fx":{"square.symbol.mod-Step": {"factor": original_speed}}}))
    loop.create_task(inner())

iomap['pixels'].fill((10,10,10))
iomap['pixels'].write()

anima = microio.animatrix.Anima(matrices, fps=20)
anima_log = microio.animatrix.AnimaLog(anima, fps=1)
control = microio.animatrix.control.Control(anima)
http = microio.http.factory(
    port=80,
    mounts=(
        microio.http.static_directory.app(
            route='/',
            file='headlights.html',
            mime='text/html; charset=utf-8'),
        microio.http.websocket.app(
            route='/ws',
            request_handler=control.handle_request,
            error_handler=control.handle_error)))

loop = microio.asyncio.get_event_loop()
loop.create_task(microio.wifi.station.start_multi(
    configs=getattr(config, 'wifi', []),
    rescan=False,
    on_connected=display_ip))
loop.create_task(anima.start())
loop.create_task(anima_log.start())
loop.create_task(http.start())

brake = BrakeDetection(iomap['acceleration'])
loop.create_task(brake.start())

loop.run_forever()
