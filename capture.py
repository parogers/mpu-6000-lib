#!/usr/bin/env python3

import sys
import argparse
import time
from smbus import SMBus
from device import (
    MPU6000,
    ACCEL_RANGE_2G,
    ACCEL_RANGE_4G,
    ACCEL_RANGE_8G,
    ACCEL_RANGE_16G,
    MAX_VALUE,
    is_out_of_range,
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


def capture(
    show_live_preview=True,
    preview_char_width=30,
    accel_range=None,
    lpf_config=None,
):
    bus = SMBus(1)
    device = MPU6000(
        bus,
        accel_only=True,
        accel_range=RANGE_MAPPING.get(accel_range),
        lpf_config=lpf_config,
    )
    assert device.check_alive()

    start_time = time.time()
    while True:
        reading = device.read_sensor()
        tm = reading.timestamp - start_time
        if show_live_preview:
            bx = format_bar(reading.accel.x, chars=preview_char_width, scale=1)
            by = format_bar(reading.accel.y, chars=preview_char_width, scale=1)
            bz = format_bar(reading.accel.z, chars=preview_char_width, scale=1)
            print(f'X:{bx} Y:{by} Z:{bz}')
        else:
            fmt = '{tm} {x} {y} {z}'
            print(
               fmt.format(
                   tm=tm,
                   x=reading.accel.x,
                   y=reading.accel.y,
                   z=reading.accel.z,
               )
            )


def main():
    parser = argparse.ArgumentParser(
        description='Capture data from the MPU6000 accelerometer via I2C',
    )
    parser.add_argument(
        '--live-preview',
        type=bool,
        nargs=1,
        default=[True],
        help='Whether to show a live preview of the data captured',
    )
    parser.add_argument(
        '--preview-char-width',
        type=int,
        nargs=1,
        default=[30],
        help='The number of characters to use in the preview graph (per axis)',
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
    args = parser.parse_args(sys.argv[1:])
    show_live_preview = args.live_preview[0]
    preview_char_width = args.preview_char_width[0]
    accel_range = args.accel_range[0]
    lpf_config = args.lpf[0]
    capture(
        show_live_preview=show_live_preview,
        preview_char_width=preview_char_width,
        accel_range=accel_range,
        lpf_config=lpf_config,
    )


if __name__ == '__main__':
    main()
