
from dataclasses import dataclass
import time
from .device import (
    ACCEL_RANGE_MAPPING,
    convert_temp_reading_to_celsius,
    SensorData,
    Vector,
)


@dataclass
class Capabilities:
    lpf: int = 0
    accel_range: int = 0
    num_devices: int = 0


def read_caps(src_path):
    caps = Capabilities()
    with open(src_path) as file:
        for line in file.readlines():
            if not line.startswith('#'):
                break
            try:
                key, value = line[1:].split('=')
            except ValueError:
                continue
            key = key.strip()
            value = value.strip()
            if key == 'LPF':
                caps.lpf = int(value)
            elif key == 'ACCEL_RANGE':
                caps.accel_range = ACCEL_RANGE_MAPPING[value]
            elif key == 'NUM_DEVICES':
                caps.num_devices = int(value)
    return caps


class MPU6000Dummy:
    def __init__(self, src_path, index=0):
        self.src_path = src_path
        self.file = open(src_path, 'r')
        self.last_time = 0
        self.start_time = None
        self.index = index
        self.capabilities = read_caps(src_path)
        if index >= self.capabilities.num_devices:
            raise ValueError(f'file contains data for only {self.capabilities.num_devices} device(s)')

    @property
    def accel_range(self):
        return self.capabilities.accel_range

    @property
    def lpf_config(self):
        return self.capabilities.lpf

    def check_alive(self):
        return bool(self.file)

    def wake_up(self, **kwargs):
        pass

    def read_sensor(self):
        if self.start_time is None:
            self.start_time = time.time()

        while True:
            line = self.file.readline()
            if not line:
                return None
            line = line.strip()
            if not line:
                continue
            if not line.startswith('#'):
                break
        args = line.split()
        try:
            tm = float(args[0])
            x, y, z = args[1+self.index*3:1+self.index*3+3]
            tm = float(tm)
            x = int(x)
            y = int(y)
            z = int(z)
        except ValueError:
            raise Exception(f'unexpected line: {line}')

        real_time = time.time() - self.start_time
        delay = tm - real_time
        if delay > 0:
            time.sleep(delay)

        return SensorData(
            timestamp=float(tm),
            accel=Vector(x, y, z),
            temp=convert_temp_reading_to_celsius(0),
            gyro=Vector(0, 0, 0),
        )
