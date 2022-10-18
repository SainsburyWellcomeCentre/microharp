# microharp

A Harp protocol and device application framework micropython package.

Implements the functionality described in the [Harp Device](https://github.com/harp-tech/protocol/blob/master/Device%201.1%201.6%2020220524.pdf), [Harp Binary Protocol](https://github.com/harp-tech/protocol/blob/master/Binary%20Protocol%201.0%201.3%2020220621.pdf), and [Harp Synchronisation Clock](https://github.com/harp-tech/protocol/blob/master/Synchronization%20Clock%201.0%201.0%2020200712.pdf) specification documents.

## Dependencies

The target must be running firmware built from the [SWC fork](https://github.com/SainsburyWellcomeCentre/micropython/tree/v1.18-swc) of the micropython project. The image firmware.uf2 for Raspberry Pi Pico targets is included here for convenience.

## Usage

To get started using MicroHarp, copy the .py files in this repository to a directory named microharp on the file system of your device. Then create a Python file containing the code below and copy it to the root directory your device.

```
# Import standard library modules.
import uasyncio
from machine import Pin

# Import SWC library modules.
import usbcdc
import harpsync
from microharp.device import HarpDevice

# Instance a CDC and harpsync interface and an LED.
stream = usbcdc.usbcdc(1)
sync = harpsync.harpsync(0)
led = Pin(25, Pin.OUT)

# Instance a Harp device object and launch its application.
theDevice = HarpDevice(stream, sync, led)
uasyncio.run(theDevice.main())
```

Run the code and the LED should blink every 2 seconds.

Launch Bonsai, create a Harp device and select the correct COM port (this will be numbered one higher than your device REPL COM port). Once selected you will see the following output in the Bonsai console window, the Timestamp value will differ and is the time elapsed since your device booted.

```
Serial Harp device.
WhoAmI: 26354-0000
Hw: 1.0
Fw: 0.1
Timestamp (s): 7753
DeviceName: Microharp Device
```

The Harp device name displayed in the Bonsai GUI will also update once clicked. Running and stopping the Bonsai workflow will put the device into active and standby modes respectively, which will be reflected by the blink rate of the LED.

You now have a device which implements the Harp common registers and operational behavior. Application specific Harp devices may be developed by subclassing the framework and adding hardware driver functionality. Examples may be found in the [Virtual Hunting](https://github.com/SainsburyWellcomeCentre/virt-hunt-drv), [Pertubation Treadmill](https://github.com/SainsburyWellcomeCentre/pert-tread-drv), and [Responsive Joystick](https://github.com/SainsburyWellcomeCentre/resp-joystick) projects.
