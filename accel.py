#!/usr/bin/env python3

from smbus import SMBus
from device import (
    MPU6000,
    ACCEL_RANGE_4G,
)

bus = SMBus(1)
device = MPU6000(
    bus,
    accel_range=ACCEL_RANGE_4G,
    lpf_config=6,
)
while True:
    data = device.read_sensor()
    if data.is_out_of_range:
        print('RANGE')
    else:
        print(data.accel)
