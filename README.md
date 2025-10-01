# MPU-6000

Module for interfacing with the MPU-60X0 I2C accelerometer. This module is written with the Raspberry PI in mind, using the default smbus module. Other setups should be possible with the use of some adapter code.

On a Raspberry PI B+ (v1.2), with default I2C settings, I'm able to average about 750 samples per second.

# License

The code and example scripts are released under the [GPLv3 license](LICENSE).

# CLI Usage

You can use the capture script if you just want to log data directly:

```python
capture.py --accel-range 4g --lpf 3
```

The script allows you to configure the MPU package (eg. full sensor range, low-pass filter config) plot the data live:

```bash
capture.py --preview-averaging 5 --preview-period 50 --preview-char-width 15
```

This is useful for getting a feel for what's happening to the sensor. The length of each bar corresponds to the reading as a portion of the full value range, and the sign is indicated by either '+' or '-'. A special value 'R' is used to indicate the reading is out of range. Example output:

```
X:0               Y:0               Z:++++++++       
X:0               Y:0               Z:++++++++       
X:+               Y:0               Z:+++++++        
X:++              Y:0               Z:+++++++        
X:+++             Y:0               Z:+++++++        
X:++++            Y:0               Z:++++++         
X:+++++           Y:-               Z:+++++          
X:+++++           Y:-               Z:+++++          
X:++++++          Y:-               Z:++++           
X:+++++++         Y:-               Z:++++           
X:++++++          Y:-               Z:++++           
X:++++++          Y:-               Z:++++           
X:+++++           Y:-               Z:++++++         
X:+++             Y:-               Z:++++++         
X:++              Y:-               Z:+++++++        
X:+               Y:-               Z:+++++++        
X:0               Y:-               Z:++++++++       
X:-               Y:-               Z:+++++++        
X:--              Y:-               Z:+++++++        
X:---             Y:-               Z:+++++++        
X:---             Y:-               Z:++++++         
X:----            Y:-               Z:++++++         
X:-----           Y:-               Z:+++++          
X:-----           Y:-               Z:+++++          
X:------          Y:-               Z:++++           
X:------          Y:-               Z:++++           
X:------          Y:-               Z:++++           
```

Or save to a log file for later processing:

```bash
capture.py out.log --note "This is a short note" --accel-range 4g --lpf 5
```

Data is saved in a gnuplot friendly format, with configuration arguments and optional note included as a comment block at the top of the file. Each data line includes a timestamp, followed by the reading from each axis.

```
# NOTE = This is a short note
# LPF = 5
# ACCEL_RANGE = 4g

0.0013861656188964844 -114 -59 2192
0.003231048583984375 -154 -80 2984
0.005839109420776367 -201 -109 3997
0.007378101348876953 -214 -118 4290
```

# Python Usage

You can import and use the device class directly in your python code:

```python
# Note it should work with smbus2 too
from smbus import SMBus
from mpu6000 import MPU6000, ACCEL_RANGE_4G

bus = SMBus(1)
device = MPU6000(
    bus,
    # Speed up capture by just grabbing accelerometer data
    # accel_only=True,
    accel_range=ACCEL_RANGE_4G,
    lpf_config=3,
)
reading = device.read_sensor()
print(reading.timestamp)
print(reading.accel.x)
print(reading.temperature)
print(reading.gyro.x)
```
