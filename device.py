"""Harp device class."""
import uasyncio
from collections import deque
from micropython import const

from microharp.types import HarpTypes
from microharp.message import HarpMessage, HarpRxMessage, HarpTxMessage
from microharp.register import (ReadOnlyReg, ReadWriteReg,
                                TimestampSecondReg, TimestampMicroReg, OperationalCtrlReg)
from microharp.event import PeriodicEvent


class HarpDevice():
    """Harp device implementing the common registers and functionality.

    All Harp device classes should subclass this class, overload __init__ and call it from their
    implementation. Devices may overload _ctrl_hook(), but must call the base function. It is
    not recommended, nor should it be necessary, to overload other member functions of this class.
    """
    R_WHO_AM_I = const(0)
    R_HW_VERSION_H = const(1)
    R_HW_VERSION_L = const(2)
    R_ASSEMBLY_VERSION = const(3)
    R_HARP_VERSION_H = const(4)
    R_HARP_VERSION_L = const(5)
    R_FW_VERSION_H = const(6)
    R_FW_VERSION_L = const(7)
    R_TIMESTAMP_SECOND = const(8)
    R_TIMESTAMP_MICRO = const(9)
    R_OPERATION_CTRL = const(10)
    R_RESET_DEV = const(11)
    R_DEVICE_NAME = const(12)
    R_SERIAL_NUMBER = const(13)

    ledIntervals = (2.0, 1.0, 0.05, 0.5)

    def __init__(self, stream, sync, led, rxqlen=16, txqlen=16, trace=False):
        """Constructor.

        Connects the logical device to its physical interfaces and creates the register map.
        Sub-classes should extend (and update) the register dictionary with register classes
        which implement the required device specific functionality.
        """
        self.stream = stream
        self.sync = sync
        self.led = led
        self.trace = trace

        self.rxMessages = deque((), rxqlen, 1)
        self.txMessages = deque((), txqlen, 1)

        self.registers = {
            HarpDevice.R_WHO_AM_I: ReadOnlyReg(HarpTypes.U16, (26354,)),
            HarpDevice.R_HW_VERSION_H: ReadOnlyReg(HarpTypes.U8, (1,)),
            HarpDevice.R_HW_VERSION_L: ReadOnlyReg(HarpTypes.U8),
            HarpDevice.R_FW_VERSION_H: ReadOnlyReg(HarpTypes.U8),
            HarpDevice.R_FW_VERSION_L: ReadOnlyReg(HarpTypes.U8, (1,)),
            HarpDevice.R_TIMESTAMP_SECOND: TimestampSecondReg(sync),
            HarpDevice.R_TIMESTAMP_MICRO: TimestampMicroReg(sync),
            HarpDevice.R_OPERATION_CTRL: OperationalCtrlReg(self._ctrl_hook),
            HarpDevice.R_DEVICE_NAME: ReadWriteReg(HarpTypes.U8, tuple(b'Microharp Device')),
            HarpDevice.R_SERIAL_NUMBER: ReadWriteReg(HarpTypes.U16)
        }

        self.aliveEvent = PeriodicEvent(
            HarpDevice.R_TIMESTAMP_SECOND, self.registers[HarpDevice.R_TIMESTAMP_SECOND],
            self.sync, self.txMessages, 1000)

        self.tasks = [
            self._stream_task(),
            self._blink_task()
        ]

    def _ctrl_hook(self):
        """Private member function.

        Control register write hook, updates device state.
        """
        if not self.registers[HarpDevice.R_OPERATION_CTRL].OPLEDEN:
            self.led.off()

        if self.registers[HarpDevice.R_OPERATION_CTRL].OP_MODE != OperationalCtrlReg.STANDBY_MODE:
            self.aliveEvent.enabled = self.registers[HarpDevice.R_OPERATION_CTRL].ALIVE_EN
        else:
            self.aliveEvent.enabled = False

    async def _read_co(self, buf, nbytes=1):
        """Private member co-routine.

        Reads nbytes from stream into buf in the largest blocks available, whilst playing nicely.
        """
        while nbytes > 0:
            n = min(nbytes, self.stream.any())
            if n > 0:
                buf.extend(self.stream.read(n))
                nbytes -= n
            await uasyncio.sleep(0)

    async def _stream_task(self):
        """Private member co-operative task.

        Reads and validates complete messages from stream and posts them to the rxMessages queue.
        """
        print('HarpDevice._stream_task()')
        while True:
            try:
                rxMessage = HarpRxMessage()
                await self._read_co(rxMessage.buffer, HarpMessage.LENGTH_BYTE)
                if not rxMessage.has_valid_message_type():
                    raise ValueError('Invalid messageType: ' +
                                     rxMessage.to_string())
                await self._read_co(rxMessage.buffer, rxMessage.length)
                if not rxMessage.has_valid_checksum():
                    raise ValueError('Invalid checksum: ' +
                                     rxMessage.to_string())
                self.rxMessages.append(rxMessage)
            except (ValueError, IndexError) as e:
                print(e)

    async def _blink_task(self):
        """Private member co-operative task.

        Toggles the led to indicate the device operation mode.
        """
        print('HarpDevice._blink_task()')
        while True:
            if self.registers[HarpDevice.R_OPERATION_CTRL].OPLEDEN:
                self.led.toggle()
            interval = HarpDevice.ledIntervals[self.registers[HarpDevice.R_OPERATION_CTRL].OP_MODE]
            await uasyncio.sleep(interval)

    async def main(self):
        """Device main function, must be called using uasyncio.run().

        Creates and launches the device co-operative tasks and executes the main application loop.
        """
        print('HarpDevice.main()')
        for task in self.tasks:
            uasyncio.create_task(task)

        while True:
            # Process rx message queue.
            if len(self.rxMessages) > 0:
                try:
                    # Fetch next message.
                    rxMessage = self.rxMessages.popleft()
                    if self.trace:
                        print('RX message: ' + rxMessage.to_string())

                    # Perform write operation.
                    if rxMessage.messageType == HarpMessage.WRITE:
                        self.registers[rxMessage.address].write(rxMessage.payloadType, rxMessage.payload)

                    # Prepare response.
                    length = len(self.registers[rxMessage.address]) * HarpTypes.size(
                        rxMessage.payloadType) + HarpMessage.offset(HarpTypes.HAS_TIMESTAMP) - 1
                    txMessage = HarpTxMessage(
                        rxMessage.messageType, length, rxMessage.address, rxMessage.payloadType, self.sync.read())

                    # Perform read operation.
                    txMessage.payload = self.registers[rxMessage.address].read(
                        rxMessage.payloadType)

                except (TypeError, IndexError, KeyError):
                    # Prepare error response.
                    length = rxMessage.length + HarpMessage.resize(rxMessage.payloadType)
                    txMessage = HarpTxMessage(rxMessage.messageType | HarpMessage.ERROR,
                                              length, rxMessage.address, rxMessage.payloadType, self.sync.read())
                    if rxMessage.messageType == HarpMessage.WRITE:
                        txMessage.payload = rxMessage.payload

                # Format and post response to transmit queue.
                txMessage.calc_set_checksum()
                self.txMessages.append(txMessage)

            # Process tx message queue.
            if len(self.txMessages) > 0:
                txMessage = self.txMessages.popleft()
                if self.trace:
                    print('TX message: ' + txMessage.to_string())
                self.stream.write(txMessage.buffer)

            await uasyncio.sleep(0)
