import aioble
import bluetooth
import uasyncio as asyncio
a = asyncio

device = aioble.Device(aioble.ADDR_PUBLIC, '560b10126280')

async def scan():
    async with aioble.scan(duration_ms=5000) as scanner:
        async for result in scanner:
            print('Scan:', result, result.name(), result.rssi, list(result.services()))

discovery = {}
async def start():
    while True:
        print('Connecting', device)
        try:
            connection = await device.connect(timeout_ms=2000)
            async for service in connection.services():
                print('Discover service', service)
                discovery[service] = []
            print('Discovered services', discovery)
            for service in discovery.keys():
                async for characteristic in service.characteristics():
                    print('Discover characteristic', characteristic)
                    discovery[service].append(characteristic)
            print('Discovered characteristics', discovery)
            # for service, characteristics in discovery.items():
            #     for characteristic in characteristics:
            #         async for descriptor in characteristic.descriptors():
            #             print('Discover descriptor', descriptor)
            for service, characteristics in discovery.items():
                for characteristic in characteristics:
                    print('Subscribe', characteristic)
                    asyncio.get_event_loop().create_task(listen(characteristic))
            while True:
                for service, characteristics in discovery.items():
                    for characteristic in characteristics:
                        try:
                            value = await characteristic.read()
                            print('Read:', characteristic, service, '\t', value)
                        except:
                            pass
                print()
                await asyncio.sleep(1)
            break
        except asyncio.TimeoutError:
            print('Timeout')
        # except Exception as e:
        #     print('Error', e.__class__.__name__, e)
        #     continue
        asyncio.sleep(1)

async def listen(characteristic):
    print('Subscribe', characteristic)
    characteristic.subscribe(notify=True, indicate=True)
    while True:
        try:
            data = await characteristic.notified()
            print('Data from characteristic', characteristic, data)
        except Exception as e:
            print('Error subscribing', characteristic, e.__class__.__name__, e)
            break


# asyncio.run(scan())
loop = asyncio.get_event_loop()
asyncio.get_event_loop().create_task(start())
loop.run_forever()
