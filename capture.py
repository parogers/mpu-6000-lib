#!/usr/bin/env python3
#
# mpu-6000-lib - A library for interfacing with the MPU6000 accelerometer module
# Copyright (C) 2025  Peter Rogers
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import sys
import argparse
import time
import statistics
from smbus import SMBus
from mpu6000 import (
    MPU6000,
    ACCEL_RANGE_2G,
    ACCEL_RANGE_4G,
    ACCEL_RANGE_8G,
    ACCEL_RANGE_16G,
    MAX_VALUE,
    is_out_of_range,
    DEFAULT_ADDRESS,
    ALTERNATE_ADDRESS,
)


# Maps the accel range CLI argument to device config
RANGE_MAPPING = {
    '2g' : ACCEL_RANGE_2G,
    '4g' : ACCEL_RANGE_4G,
    '8g' : ACCEL_RANGE_8G,
    '16g' : ACCEL_RANGE_16G,
}


def format_bar(value, chars=20, full_scale=MAX_VALUE, scale=1):
    if is_out_of_range(value):
        char = 'R'
    elif value >= 0:
        char = '+'
    else:
        char = '-'

    scaled = min(scale*(value/full_scale), 1)
    bar = round(abs(scaled)*chars)*char
    if len(bar) == 0:
        bar = '0'
    bar += ' '*(chars - len(bar))
    return bar


def format_bars(vector, chars):
    bx = format_bar(vector.x.average, chars=chars)
    by = format_bar(vector.y.average, chars=chars)
    bz = format_bar(vector.z.average, chars=chars)
    return f'X:{bx} Y:{by} Z:{bz}'


class SlidingWindow:
    def __init__(self, size):
        self.values = []
        self.size = size

    def add(self, value):
        self.values.append(value)
        self.values = self.values[-self.size:]

    @property
    def average(self):
        return statistics.mean(self.values)


class VectorSlidingWindow:
    def __init__(self, size):
        self.x = SlidingWindow(size)
        self.y = SlidingWindow(size)
        self.z = SlidingWindow(size)

    def add(self, vector):
        self.x.add(vector.x)
        self.y.add(vector.y)
        self.y.add(vector.z)


def configure_devices(
    bus,
    accel_range=None,
    lpf_config=None,
    num_devices=1,
):
    addresses = (
        DEFAULT_ADDRESS,
        ALTERNATE_ADDRESS,
    )
    assert num_devices in (1, 2)
    devices = []
    for n in range(num_devices):
        device = MPU6000(
            bus,
            accel_only=True,
            accel_range=RANGE_MAPPING.get(accel_range),
            lpf_config=lpf_config,
            address=addresses[n],
        )
        devices.append(device)
    return devices


def capture(
    show_live_preview=True,
    preview_char_width=30,
    accel_range=None,
    lpf_config=None,
    note=None,
    preview_avg_window=1,
    preview_period=None,
    num_devices=1,
    dest=None,
):
    bus = SMBus(1)
    devices = configure_devices(
        bus,
        accel_range=accel_range,
        lpf_config=lpf_config,
        num_devices=num_devices,
    )

    if dest:
        dest_file = open(dest, 'w')
        if note:
            dest_file.write(f'# NOTE = {note}\n')
        dest_file.write(f'# LPF = {lpf_config}\n')
        dest_file.write(f'# ACCEL_RANGE = {accel_range}\n')
        dest_file.write(f'# NUM_DEVICES = {num_devices}\n')
        dest_file.write('\n')
        print('Capturing...')
    else:
        dest_file = None

    averages = [
        VectorSlidingWindow(size=preview_avg_window)
        for device in devices
    ]
    start_time = time.time()
    last_time = None
    while True:
        readings = [
            device.read_sensor()
            for device in devices
        ]
        tm = readings[0].timestamp - start_time # not quite right...
        if show_live_preview and (
            not last_time or
            not preview_period or
            tm - last_time > preview_period/1000
        ):
            for average, reading in zip(averages, readings):
                average.x.add(reading.accel.x)
                average.y.add(reading.accel.y)
                average.z.add(reading.accel.z)
            if num_devices == 2:
                print(
                    format_bars(averages[0], chars=preview_char_width) + ' ' +
                    format_bars(averages[1], chars=preview_char_width)
                )
            else:
                print(format_bars(averages[0], chars=preview_char_width))
            last_time = tm

        if dest_file:
            if num_devices == 2:
                fmt = '{tm} {x1} {y1} {z1} {x2} {y2} {z2}'
                dest_file.write(
                   fmt.format(
                       tm=tm,
                       x1=readings[0].accel.x,
                       y1=readings[0].accel.y,
                       z1=readings[0].accel.z,
                       x2=readings[1].accel.x,
                       y2=readings[1].accel.y,
                       z2=readings[1].accel.z,
                   ) + '\n'
                )
            else:
                fmt = '{tm} {x} {y} {z}'
                dest_file.write(
                   fmt.format(
                       tm=tm,
                       x=reading.accel.x,
                       y=reading.accel.y,
                       z=reading.accel.z,
                   ) + '\n'
                )


def main():
    parser = argparse.ArgumentParser(
        description='Capture data from the MPU6000 accelerometer via I2C',
    )
    parser.add_argument(
        '--disable-live-preview',
        action='store_const',
        const=[True],
        default=[None],
        help='Whether to disable a live preview of the data captured',
    )
    parser.add_argument(
        '--enable-live-preview',
        action='store_const',
        const=[True],
        default=[None],
        help='Whether to enable a live preview of the data captured',
    )
    parser.add_argument(
        '--preview-char-width',
        type=int,
        nargs=1,
        default=[30],
        help='The number of characters to use in the preview graph (per axis)',
    )
    parser.add_argument(
        '--preview-averaging',
        type=int,
        nargs=1,
        default=[1],
        help='The number of samples in the sliding window when averaging preview data',
    )
    parser.add_argument(
        '--preview-period',
        type=int,
        nargs=1,
        default=[0],
        help='How often the preview graph is updated (milli-seconds)',
    )
    parser.add_argument(
        '--accel-range',
        type=str,
        nargs=1,
        default=['2g'],
        choices=['2g', '4g', '8g', '16g'],
        help='The accelerometer range to configure',
    )
    parser.add_argument(
        '--lpf',
        type=int,
        nargs=1,
        default=[0],
        choices=[0, 1, 2, 3, 4, 5, 6],
        help='The low-pass filter config (0=no filtering)',
    )
    parser.add_argument(
        '--note',
        type=str,
        nargs=1,
        default=[None],
        help='The note to include in the log file output',
    )
    parser.add_argument(
        '--num-devices',
        type=int,
        nargs=1,
        default=[1],
        choices=[1, 2],
        help='Whether to capture from 1 or 2 accelerometer devices (I2C address 0x68 and 0x69)',
    )
    parser.add_argument(
        'dest',
        type=str,
        nargs='?',
        default='',
        help='Where to log the captured data',
    )
    args = parser.parse_args(sys.argv[1:])
    enable_live_preview = args.enable_live_preview[0]
    disable_live_preview = args.disable_live_preview[0]
    preview_char_width = args.preview_char_width[0]
    accel_range = args.accel_range[0]
    lpf_config = args.lpf[0]
    note = args.note[0]
    preview_avg_window = args.preview_averaging[0]
    preview_period = args.preview_period[0]
    num_devices = args.num_devices[0]
    dest = args.dest
    show_live_preview = (
        enable_live_preview is True or
        not dest and disable_live_preview is not True
    )
    capture(
        show_live_preview=show_live_preview,
        preview_char_width=preview_char_width,
        accel_range=accel_range,
        lpf_config=lpf_config,
        note=note,
        preview_avg_window=preview_avg_window,
        preview_period=preview_period,
        num_devices=num_devices,
        dest=dest,
    )


if __name__ == '__main__':
    main()
