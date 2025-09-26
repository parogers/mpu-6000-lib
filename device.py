
from dataclasses import dataclass
import struct

MAX_VALUE = 2**15 - 1
MIN_VALUE = -2**15

ACCEL_RANGE_2G = 0
ACCEL_RANGE_4G = 1
ACCEL_RANGE_8G = 2
ACCEL_RANGE_16G = 3

DEFAULT_ADDRESS = 0x68
ALTERNATE_ADDRESS = 0x69

# Internal addresses:
ADDR_CONFIG = 0x1a
ADDR_ACCEL_CONFIG = 0x1c
ADDR_PWR_MGMT_1 = 0x6b
ADDR_ACCEL_XOUT = 0x3b


def convert_temp_reading_to_celsius(value):
    # Directly from the datasheet
    return value/340 + 36.53


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
            self.accel.x <= MIN_VALUE or self.accel.x >= MAX_VALUE or
            self.accel.y <= MIN_VALUE or self.accel.y >= MAX_VALUE or
            self.accel.z <= MIN_VALUE or self.accel.z >= MAX_VALUE
        )


class MPU6000:
    def __init__(self, bus, address=DEFAULT_ADDRESS, accel_only=False, **kwargs):
        self.bus = bus
        self.address = address
        self.woken_up = False
        self.accel_only = accel_only
        self.configure(**kwargs)

    def configure(
        self,
        accel_range=None,
        lpf_config=None,
    ):
        if accel_range is not None:
            assert type(accel_range) == int and accel_range in (0, 1, 2, 3)
            self.bus.write_byte_data(self.address, ADDR_ACCEL_CONFIG, accel_range << 3)

        if lpf_config is not None:
            assert type(lpf_config) == int and lpf_config >= 0 and lpf_config < 7
            self.bus.write_byte_data(self.address, ADDR_CONFIG, lpf_config)

    def check_alive(bus):
        try:
            self.bus.read_byte_data(self.address, 0)
        except IOError:
            return False
        return True

    def wake_up(self):
        self.bus.write_byte_data(self.address, ADDR_PWR_MGMT_1, 0)

    def read_sensor(self):
        if not self.woken_up:
            self.wake_up()
            self.woken_up = True

        num_bytes = 6 if self.accel_only else 14
        data = self.bus.read_i2c_block_data(self.address, ADDR_ACCEL_XOUT, num_bytes)
        data = bytes(data)
        accel = make_vector(data[0:6])
        if self.accel_only:
            temp = 0
            gyro = Vector(0, 0, 0)
        else:
            temp = make_short(data[6:8])
            gyro = make_vector(data[8:14])

        return SensorData(
            accel=accel,
            temp=convert_temp_reading_to_celsius(temp),
            gyro=gyro,
        )
