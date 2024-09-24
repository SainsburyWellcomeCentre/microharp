"""
Harp timestamp clock class.
"""

from micropython import const
from struct import unpack
import time


class HarpClock:
    """
    A system tick counter that follows the Harp timestamp format.
    """

    # The value that system tick wraps around after 30-bits"""
    TICK_MAX = const(0x3FFFFFFF)
    CLOCK_HEADER = bytearray([0xAA, 0xAF])
    READ_OFFSET = const(161)
    UART_OFFSET = const(170)

    def __init__(self):
        self.custom_offset = 0
        self._tick_offset = 0
        self._write_offset = 0

    def read(self):
        """
        Returns a tuple of Harp timestamp (Seconds, Microseconds/32)
        The full Timestamp(s) = [Seconds] + [Microseconds] * 32 * 1e-6
        """
        temp_us = time.ticks_ms() * 1_000
        # Merge two ticks into long ticks_us with overflow checking
        tick_us = temp_us + time.ticks_us() - (temp_us % self.TICK_MAX)
        # Add time offset
        tick_us += self._tick_offset + self.custom_offset + self.READ_OFFSET

        ts = tick_us // 1_000_000
        tu = tick_us % 1_000_000

        # if tu > 999_968:
        #     tu = 0
        #     return (ts + self._write_offset + 1, 0)
        return (ts + self._write_offset, (tu // 32))

    def write(self, buf):
        """
        Overwriting the Harp timestamp in microsecond
        """
        value_to_replace = self._decode_d(buf)
        current_tick, current_tick_us = self.read()
        self._write_offset -= current_tick - value_to_replace
        self._tick_offset -= current_tick_us * 32 + self.UART_OFFSET

    def _decode_d(self, buf):

        return unpack("i", buf[3 :] + buf[:1])[0]

    def _decode(self, buf):

        idx = self._find(buf, self.CLOCK_HEADER)
        if idx > -1:
            return unpack("i", buf[idx + 2 :] + buf[:idx])[0]
        return 0

    def _find(self, buf, target):
        for i in range(0, len(buf) - 2):
            if buf[i] == target[0] and buf[i + 1] == target[1]:
                return i
        return -1
