"""
Harp timestamp clock class.
"""

from micropython import const
import time


class HarpClock:
    """
    A system tick counter that follows the Harp timestamp format.
    """
    # The value that system tick wraps around after 30-bits"""
    TICK_MAX = const(0x3FFFFFFF)

    def __init__(self):
        self.tick_offset = 0

    def read(self):
        """
        Returns a tuple of Harp timestamp (Seconds, Microseconds/32)
        The full Timestamp(s) = [Seconds] + [Microseconds] * 32 * 1e-6
        """
        temp_us = time.ticks_ms() * 1_000
        # Merge two ticks into long ticks_us with overflow checking
        tick_us = (
            temp_us + time.ticks_us() - (temp_us % self.TICK_MAX) + self.tick_offset
        )
        return (tick_us // 1_000_000, (tick_us % 1_000_000) // 32)

    def write(self, value):
        """
        Overwriting the Harp timestamp in microsecond
        """
        current_tick = self.read()
        self.tick_offset = value - (current_tick[0] * 1_000_000) + current_tick[1]
