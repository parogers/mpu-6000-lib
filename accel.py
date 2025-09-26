#!/usr/bin/env python3

from dataclasses import dataclass
import time
import struct
from smbus import SMBus

MAX_RANGE = 2**15 - 1
ADDR = 0x68
LPF_CONFIG = 0b110 # 3 bits
ACCEL_RANGE = 0b01 # 2 bits


@dataclass
class Vector:
    x: int
    y: int
    z: int


@dataclass
class SensorData:
    accel: Vector
    temp: int
    gyro: Vector

    @property
    def is_out_of_range(self):
        return (
            abs(self.accel.x) >= MAX_RANGE or
            abs(self.accel.y) >= MAX_RANGE or
            abs(self.accel.z) >= MAX_RANGE
        )


def make_vector(data):
    assert len(data) == 6
    x = make_short(data[0:2])
    y = make_short(data[2:4])
    z = make_short(data[4:6])
    return Vector(
        x=x,
        y=y,
        z=z,
    )


def make_short(data):
    assert len(data) == 2
    return struct.unpack('>h', data)[0]


def read_sensor(bus):
    data = bus.read_i2c_block_data(ADDR, 0x3b, 14)
    data = bytes(data)
    accel = make_vector(data[0:6])
    temp = make_short(data[6:8])
    gyro = make_vector(data[8:14])
    return SensorData(
        accel=accel,
        temp=temp/340 + 36.53, # from the datasheet
        gyro=gyro,
    )


def check_alive(bus):
    try:
        bus.read_byte_data(ADDR, 0)
    except IOError:
        return False
    return True

bus = SMBus(1)
assert check_alive(bus)

bus.write_byte_data(ADDR, 0x6b, 0) # wake up
bus.write_byte_data(ADDR, 0x1c, ACCEL_RANGE << 3)
bus.write_byte_data(ADDR, 0x1a, LPF_CONFIG)

#start = time.time()
#for n in range(100):
#    data = bus.read_i2c_block_data(ADDR, 0x3b, 6)
#print(1/((time.time()-start)/100))
#    print(''.join([
#        '%02X' % b
#        for b in data
#    ]))

while True:
    data = read_sensor(bus)
    if data.is_out_of_range:
        print('RANGE')
    else:
        print(data.accel)
