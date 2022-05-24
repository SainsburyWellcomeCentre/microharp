"""Harp protocol event class."""
from machine import Timer

from microharp.types import HarpTypes
from microharp.message import HarpMessage, HarpTxMessage


class HarpEvent():
    """Abstract base class, creates the event message and provides message queue binding.

    Event classes should sublcass this class and call __init__.

    The register read operation associated with a HarpEvent occurs in interrupt context, in
    order to minimise trigger latency, lengthy computation should therefore be avoided. This
    behavior may be modified by overloading _callback(), see RecurringEvent for an example.
    """

    def __init__(self, address, register, sync, queue):
        length = len(register) * HarpTypes.size(register.typ) + \
            HarpMessage.offset(HarpTypes.HAS_TIMESTAMP) - 1
        self.message = HarpTxMessage(HarpMessage.EVENT, length, address, register.typ, (0, 0))
        self.register = register
        self.sync = sync
        self.queue = queue

    def _callback(self, ins):
        self.message.timestamp = self.sync.read()
        self.message.payload = self.register.read(self.register.typ)
        self.message.calc_set_checksum()
        self.queue.append(self.message)


class PinEvent(HarpEvent):
    """Pin event.

    Triggers a read of register at address, generating an event message, on a pin event.
    """

    def __init__(self, address, register, sync, queue, trigger):
        super().__init__(address, register, sync, queue)
        register.pin.irq(handler=self._callback, trigger=trigger)


class PeriodicEvent(HarpEvent):
    """Periodic event.

    Triggers a read of register at address, generating an event message, every period milliseconds.
    """

    def __init__(self, address, register, sync, queue, period):
        super().__init__(address, register, sync, queue)
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


class RecurringEvent(PeriodicEvent):
    """Recurring event.

    Triggers a read of register at address, generating a status message, every period milliseconds.

    The register read operation associated with a RecurringEvent occurs in foreground context,
    allowing for lengthy computation at the expense of trigger latency.
    """

    def __init__(self, address, register, queue, period):
        self.message = HarpTxMessage(HarpMessage.EVENT,
            HarpMessage.offset(~HarpTypes.HAS_TIMESTAMP) - 1, address, register.typ)
        self.message.calc_set_checksum()
        self.queue = queue
        self.period = period
        self.timer = Timer()
        self._enabled = False

    def _callback(self, ins):
        self.queue.append(self.message)
