"""Harp protocol event class."""
from machine import Timer

from microharp.types import HarpTypes
from microharp.message import HarpMessage, HarpTxMessage


class HarpEvent():
    """Abstract base class, creates the event trigger message and provides message queue binding.

    All event classes must sublcass this class and call __init__.
    It is not recommended, nor should it be necessary, to overload _callback().
    """

    def __init__(self, address, typ, queue):
        self.message = HarpTxMessage(
            HarpMessage.EVENT, HarpMessage.offset(~HarpTypes.HAS_TIMESTAMP) - 1, address, typ)
        self.message.calc_set_checksum()
        self.queue = queue

    def _callback(self, ins):
        self.queue.append(self.message)


class PeriodicEvent(HarpEvent):
    """Periodic event.

    Triggers a read of register at address, generating a status message, every period milliseconds.
    """

    def __init__(self, address, typ, queue, period):
        super().__init__(address, typ, queue)
        self.period = period
        self.timer = Timer()
        self._enabled = False

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = value
        if self._enabled:
            self.timer.init(mode=Timer.PERIODIC,
                            period=self.period, callback=self._callback)
        else:
            self.timer.deinit()


class PinEvent(HarpEvent):
    """Pin event.

    Triggers a read of register at address, generating a status message, on a pin event.
    """

    def __init__(self, address, typ, queue, pin, trigger):
        super().__init__(address, typ, queue)
        self.pin = pin
        self.pin.irq(handler=self._callback, trigger=trigger)
