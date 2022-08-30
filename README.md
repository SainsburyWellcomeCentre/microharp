# microharp

A Harp protocol and device application framework micropython package.

To get started using microharp create a python file containing the code below and copy it to your device along with this package.

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

Run the code and the LED should blink every 2 seconds.

Launch Bonsai, create a Harp device and select the correct COM port (this will be numbered one higher than your device REPL COM port). Once selected you will see the following output in the Bonsai console window, the Timestamp value will differ and is the time elapsed since your device booted.

	Serial Harp device.
	WhoAmI: 26354-0000
	Hw: 1.0
	Fw: 0.1
	Timestamp (s): 7753
	DeviceName: SWC Harp Device

The Harp device name displayed in the Bonsai GUI will also update once clicked. Running and stopping the Bonsai workflow will put the device into active and standby modes respectively, which will be reflected by the blink rate of the LED.

You now have a device which implements the functionality described in the Harp Binary Protocol, Harp Device, and Harp Synchronisation Clock specification documents. New Harp devices may be developed by importing the microharp package into your project and creating your own subclasses of HarpDevice and HarpRegister. An application specific device example will be added in due course, watch this space!
