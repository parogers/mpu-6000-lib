
import time
from .device import (
    convert_temp_reading_to_celsius,
    SensorData,
    Vector,
)

class MPU6000Dummy:
    def __init__(self, src_path, index=0):
        self.src_path = src_path
        self.file = open(src_path, 'r')
        self.last_time = 0
        self.start_time = None
        self.index = index

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

        delay = tm - (time.time() - self.start_time)
        if delay > 0:
            time.sleep(delay)

        return SensorData(
            timestamp=float(tm),
            accel=Vector(x, y, z),
            temp=convert_temp_reading_to_celsius(0),
            gyro=Vector(0, 0, 0),
        )
