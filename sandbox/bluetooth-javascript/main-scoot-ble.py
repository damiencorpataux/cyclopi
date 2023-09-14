import bluetooth
import binascii

ble = bluetooth.BLE()
ble.active(True)

runtime = {
    'services': [],
    'service_index': None,
    'characteristics': [],
    'descriptors': [],
    'read_index': None,
    'values': {},
    'values_last': {},
    'diff': {},
}

map = {
    'addr_type': {
        0x00: ('PUBLIC', '...'),
        0x01: ('RANDOM', 'either static, RPA, or NRPA, the type is encoded in the address itself'),
    },
    'adv_type': {
        0x00: ('ADV_IND', 'connectable and scannable undirected advertising'),
        0x01: ('ADV_DIRECT_IND', 'connectable directed advertising'),
        0x02: ('ADV_SCAN_IND', 'scannable undirected advertising'),
        0x03: ('ADV_NONCONN_IND', 'non-connectable undirected advertising'),
        0x04: ('SCAN_RSP', 'scan response'),
    },
    'event': {
        1: 'IRQ_CENTRAL_CONNECT',
        2: 'IRQ_CENTRAL_DISCONNECT',
        3: 'IRQ_GATTS_WRITE',
        4: 'IRQ_GATTS_READ_REQUEST',
        5: 'IRQ_SCAN_RESULT',
        6: 'IRQ_SCAN_DONE',
        7: 'IRQ_PERIPHERAL_CONNECT',
        8: 'IRQ_PERIPHERAL_DISCONNECT',
        9: 'IRQ_GATTC_SERVICE_RESULT',
        10: 'IRQ_GATTC_SERVICE_DONE',
        11: 'IRQ_GATTC_CHARACTERISTIC_RESULT',
        12: 'IRQ_GATTC_CHARACTERISTIC_DONE',
        13: 'IRQ_GATTC_DESCRIPTOR_RESULT',
        14: 'IRQ_GATTC_DESCRIPTOR_DONE',
        15: 'IRQ_GATTC_READ_RESULT',
        16: 'IRQ_GATTC_READ_DONE',
        17: 'IRQ_GATTC_WRITE_DONE',
        18: 'IRQ_GATTC_NOTIFY',
        19: 'IRQ_GATTC_INDICATE',
        20: 'IRQ_GATTS_INDICATE_DONE',
        21: 'IRQ_MTU_EXCHANGED',
        22: 'IRQ_L2CAP_ACCEPT',
        23: 'IRQ_L2CAP_CONNECT',
        24: 'IRQ_L2CAP_DISCONNECT',
        25: 'IRQ_L2CAP_RECV',
        26: 'IRQ_L2CAP_SEND_READY',
        27: 'IRQ_CONNECTION_UPDATE',
        28: 'IRQ_ENCRYPTION_UPDATE',
        29: 'IRQ_GET_SECRET',
        30: 'IRQ_SET_SECRET',
    }
}

def decode_adv_data(adv_data):
    decoded_data = {'name': None}
    index = 0

    while index < len(adv_data):
        length = adv_data[index]
        index += 1
        if length == 0:  # End of advertisement data
            break

        type_code = adv_data[index]
        index += 1

        if type_code == 0x09:  # Complete local name
            name = bytes(adv_data[index:index + length - 1]).decode('utf-8')
            decoded_data['name'] = name
        elif type_code == 0xFF:  # Manufacturer-specific data
            decoded_data['manufacturer_id'] = binascii.hexlify(adv_data[index:index + 2]).decode('utf-8')
            decoded_data['manufacturer_data'] = binascii.hexlify(adv_data[index + 2:index + length]).decode('utf-8')

        index += length - 1

    return decoded_data

def irq_handler(event, data):
    # print('ble: IRQ Event', event, map['event'].get(event), tuple(bytes(d) if type(d) is memoryview else d for d in data))

    if event == 8: #IRQ_PERIPHERAL_DISCONNECT
        #print('ble: Disconnect. Reconnecting...')
        connect()

    if event == 5: #IRQ_SCAN_RESULT:
        try:
            addr_type, addr, adv_type, rssi, adv_data = data
            addr_decoded = binascii.hexlify(addr)
            adv = decode_adv_data(adv_data)
            print('ble: Scan results:',
                f'\n = addr_type={addr_type}, addr={bytes(addr)}, adv_type={adv_type}, rssi={rssi}, adv_data={bytes(adv_data)}')
            print(
                f'\n - addr_type: {map["addr_type"][addr_type]}',
                f'\n - addr (decoded): {addr} ({addr_decoded})',
                f'\n - adv_type: {adv_type}',
                f'\n - rssi: {rssi}',
                f'\n - adv_data (decoded): {bytes(adv_data)} ({adv})',
                '\n\n--8<----\n')
        except ValueError:
            #print('ble: IRQ Event data is empty:', event, data)
            pass

        if adv['name'] is not None and adv['name'].startswith('SN_00734560'):
            print(f'ble: Connecting to {adv["name"]}: {(addr_type, bytes(addr), addr_decoded)}')
            ble.gap_scan(None)
            ble.gap_connect(addr_type, addr)

    if event == 7: #IRQ_PERIPHERAL_CONNECT:
        conn_handle, addr_type, addr = data
        #print('ble: Discover services for addr', addr)
        ble.gattc_discover_services(conn_handle)

    if event == 9: #IRQ_GATTC_SERVICE_RESULT:
        conn_handle, start_handle, end_handle, uuid = data
        #print('ble: Add service', data)
        runtime['services'].append((conn_handle, start_handle, end_handle)) #, uuid)) #data)

    if event == 10: #IRQ_GATTC_SERVICE_DONE:
        conn_handle, status = data  # Note: Status will be zero on success, implementation-specific value otherwise.
        print('ble: Discover characteristics for services', runtime['services'])
        runtime['service_index'] = 0
        irq_handler(event=12, data=(conn_handle, status))

    if event == 11: #IRQ_GATTC_CHARACTERISTIC_RESULT:
        conn_handle, end_handle, value_handle, properties, uuid = data
        runtime['characteristics'].append((conn_handle, end_handle, value_handle, properties)) #, uuid))

    if event == 12: #IRQ_GATTC_CHARACTERISTIC_DONE
        conn_handle, status = data
        try:
            ble.gattc_discover_characteristics(*runtime['services'][runtime['service_index']])
            runtime['service_index'] += 1
        except IndexError:
            print(f'ble: Discovered {len(runtime["characteristics"])} characteristics:', runtime['characteristics'])
            pass  # Note: Characteristics discovery done.
            print('ble: Discover descriptors for services', runtime['services'])
            runtime['service_index'] = 0
            irq_handler(event=14, data=(conn_handle, status))

    if event == 13: #IRQ_GATTC_DESCRIPTOR_RESULT
        conn_handle, dsc_handle, uuid = data
        runtime['descriptors'].append((conn_handle, dsc_handle))  #, uuid))

    if event == 14: #IRQ_GATTC_DESCRIPTOR_DONE
        conn_handle, status = data
        try:
            # FIXME: Descriptors belong to services, not to characteristics.
            # ble.gattc_discover_descriptors(conn_handle, start_handle, end_handle)
            try:
                ble.gattc_discover_descriptors(*runtime['services'][runtime['service_index']])
                runtime['service_index'] += 1
            except Exception as e:
                print(f'ble: Error discovering descriptor for service {runtime["services"][runtime["service_index"]]}: {e.__class__.__name__}: {e}')
                runtime['service_index'] += 1
                irq_handler(event=14, data=(conn_handle, status))
        except IndexError:
            print(f'ble: Discovered {len(runtime["descriptors"])} descriptors:', runtime['descriptors'])
            pass  # Note: Descriptors discovery done.
            print('ble: Read values...')
            runtime['read_index'] = 0
            irq_handler(event=16, data=(conn_handle, None, status))

    if event == 15: #IRQ_GATTC_READ_RESULT
        conn_handle, value_handle, char_data = data
        runtime['values'][value_handle] = bytes(char_data)

    if event == 16: #IRQ_GATTC_READ_DONE
        conn_handle, value_handle, status = data
        try:
            # conn_handle, end_handle, value_handle, properties = runtime['characteristics'][runtime['read_index']]
            conn_handle, value_handle = runtime['descriptors'][runtime['read_index']]
            ble.gattc_read(conn_handle, value_handle)
            runtime['read_index'] += 1
        except IndexError:
            pass  # Reading characteristics done.
            print('ble: Reading values done.')
            diff = {k: (last, runtime['values'][k]) for k, last in runtime['values_last'].items() if last != runtime['values'][k]}
            print('\nValues:')
            for k, v in runtime['values'].items():
                print(f' - {k}: {v}')
                runtime['values_last'][k] = v
            print('\nDiff:')
            for k, v in diff.items():
                print(f' - {k}: {v[0]} -> {v[1]}')
            print('\n--8<----\n')
            print('ble: Reading again...')
            irq_handler(event=14, data=(conn_handle, status))  # Start reading again.


# User code.

ble.irq(irq_handler)

def scan():
    ble.gap_scan(0)#5000)

def connect(mac='560b10126280', addr_type=0):
    print(f'ble: Connecting to {mac} ({map["addr_type"]})')
    ble.gap_connect(addr_type, binascii.unhexlify(mac))

connect()
# try:
#     import time
#     scan()
#     time.sleep(float('inf'))
# except KeyboardInterrupt:
#     print('Stopping scan')
#     ble.gap_scan(None)
