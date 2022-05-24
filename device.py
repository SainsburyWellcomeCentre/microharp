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
    implementation. It is not recommended, nor should it be necessary, to overload other member
    functions of this class.
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
            HarpDevice.R_OPERATION_CTRL: OperationalCtrlReg(HarpTypes.U8, (0x60,)),
            HarpDevice.R_DEVICE_NAME: ReadWriteReg(HarpTypes.U8, tuple(b'SWC-IRFL Harp Device')),
            HarpDevice.R_SERIAL_NUMBER: ReadWriteReg(HarpTypes.U16)
        }

        self.aliveEvent = PeriodicEvent(
            HarpDevice.R_TIMESTAMP_SECOND, self.registers[HarpDevice.R_TIMESTAMP_SECOND],
            self.sync, self.txMessages, 1000)

    async def _read_co(self, buf, nbytes=1):
        """Private member co-routine.

        Reads nbytes from stream into buf in the largest blocks available, whilst playing nicely.
        """
        while nbytes > 0:
            n = min(nbytes, self.stream.any())
            if n > 0:
                buf.extend(self.stream.read(n))
                nbytes = nbytes - n
            await uasyncio.sleep(0)

    async def _stream_rx_task(self):
        """Private member co-operative task.

        Reads and validates complete messages from stream and posts them to the rxMessages queue.
        """
        print('HarpDevice._stream_rx_task()')
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

    async def _stream_tx_task(self):
        """Private member co-operative task.
        Polls for messages in the txMessages queue and writes them to stream when available.
        """
        print('HarpDevice._stream_tx_task()')
        while True:
            if len(self.txMessages) > 0:
                txMessage = self.txMessages.popleft()
                if self.trace:
                    print('TX message: ' + txMessage.to_string())
                self.stream.write(txMessage.buffer)
            await uasyncio.sleep(0)

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
        uasyncio.create_task(self._stream_rx_task())
        uasyncio.create_task(self._stream_tx_task())
        uasyncio.create_task(self._blink_task())

        while True:
            # Process message queue.
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

            # Update device state.
            if not self.registers[HarpDevice.R_OPERATION_CTRL].OPLEDEN:
                self.led.off()
            if self.registers[HarpDevice.R_OPERATION_CTRL].ALIVE_EN and not self.aliveEvent.enabled:
                self.aliveEvent.enabled = True
            elif not self.registers[HarpDevice.R_OPERATION_CTRL].ALIVE_EN and self.aliveEvent.enabled:
                self.aliveEvent.enabled = False

            await uasyncio.sleep(0)
