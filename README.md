# MPU-6000

Module for interfacing with the MPU-60X0 I2C accelerometer. This module is written with the Raspberry PI in mind, using the default smbus module. Other setups should be possible with the use of some adapter code.

On a Raspberry PI B+ (v1.2), with default I2C settings, I'm able to average about 750 samples per second.

You can find more about interfacing with the MPU6000 in the [register map documentation](https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Register-Map1.pdf), and more about the hardware in the [datasheet](https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Datasheet1.pdf).

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

## Capturing from 2 devices

You can also capture data from two accelerometers on the same I2C bus. Tying pin AD0 high changes the device address from the default 0x68 to 0x69 meaning you can have two such devices on the same bus.

The capture script supports 2 devices in both data logging and preview modes:

```bash
./capture.py --num-devices=2 --preview-char-width 15
./capture.py --num-devices=2 out.log
```

Note in preview mode you'll either want to adjust your terminal size to fit both graphs, or reduce the width of each graph via CLI argument. As well, both devices are configured with the same options. (eg LPF config)

By default, in the logged data file the readings from each device will share a common timestamp, even though they are captured at different times. (since devices share a bus they must take turns reporting data) The output looks like:

```
# LPF = 0
# ACCEL_RANGE = 2g
# NUM_DEVICES = 2

0.0022187232971191406 3504 -32 16892 4904 48 18060
0.007876396179199219 3468 40 16968 4980 0 17948
0.012566328048706055 3548 0 17048 4884 32 17980
0.01695728302001953 3460 -76 17128 4908 4 17924
```

You can override this by specifying that timestamps should be split up between the two sensors:

```bash
./capture.py --num-devices 2 --split-times out.log
```

And the output looks like: (notice the two readings are milliseconds apart)

```
# LPF = 0
# ACCEL_RANGE = 2g
# NUM_DEVICES = 2

0.0017800331115722656 3548 -116 16900 0.0033211708068847656 4984 -68 18076
0.007280826568603516 3644 -172 17036 0.008597135543823242 4912 -12 17940
0.011837005615234375 3524 -128 17028 0.013272762298583984 4936 -60 17748
0.016381025314331055 3520 -88 17012 0.0177309513092041 4892 -16 18012
0.02048492431640625 3520 -40 16944 0.02170586585998535 4868 16 17904
0.02470088005065918 3556 -24 17108 0.025932788848876953 4940 -72 17876
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
