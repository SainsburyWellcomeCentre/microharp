"""Harp protocol message classes."""
from struct import pack_into, unpack_from
from binascii import hexlify
from micropython import const

from microharp.types import HarpTypes


class HarpMessage():
    """Abstract base class, defines Harp message semantics and translates to/from native types."""
    READ = const(1)
    WRITE = const(2)
    EVENT = const(3)
    ERROR = const(0x08)
    messageTypes = (READ, WRITE, EVENT)

    LENGTH_BYTE = const(2)

    formats = {
        HarpTypes.U8: 'B',
        HarpTypes.S8: 'b',
        HarpTypes.U16: 'H',
        HarpTypes.S16: 'h',
        HarpTypes.U32: 'I',
        HarpTypes.S32: 'i',
        HarpTypes.U64: 'Q',
        HarpTypes.S64: 'q',
        HarpTypes.FLOAT: 'f'
    }

    @property
    def format(self):
        return self.formats[self.payloadType & ~HarpTypes.HAS_TIMESTAMP]

    @property
    def messageType(self):
        return self.buffer[0]

    @messageType.setter
    def messageType(self, value):
        self.buffer[0] = value

    @property
    def length(self):
        return self.buffer[1]

    @length.setter
    def length(self, value):
        self.buffer[1] = value

    @property
    def address(self):
        return self.buffer[2]

    @address.setter
    def address(self, value):
        self.buffer[2] = value

    @property
    def port(self):
        return self.buffer[3]

    @port.setter
    def port(self, value):
        self.buffer[3] = value

    @property
    def payloadType(self):
        return self.buffer[4]

    @payloadType.setter
    def payloadType(self, value):
        self.buffer[4] = value

    @property
    def timestamp(self):
        return unpack_from('IH', self.buffer, 5)

    @timestamp.setter
    def timestamp(self, value):
        pack_into('IH', self.buffer, 5, *value)

    @property
    def payload(self):
        ofs = HarpMessage.offset(self.payloadType)
        nof = (self.length - ofs + 1) // HarpTypes.size(self.payloadType)
        return unpack_from(f'{nof}{self.format}', self.buffer, ofs)

    @payload.setter
    def payload(self, value):
        ofs = HarpMessage.offset(self.payloadType)
        nof = len(value)
        pack_into(f'{nof}{self.format}', self.buffer, ofs, *value)

    @property
    def checksum(self):
        return self.buffer[-1]

    @checksum.setter
    def checksum(self, value):
        self.buffer[-1] = value

    def to_string(self):
        return str(hexlify(self.buffer, '-'))

    @staticmethod
    def offset(payloadType):
        return 5 if payloadType & HarpTypes.HAS_TIMESTAMP == 0 else 11


class HarpRxMessage(HarpMessage):
    """Receive message buffer and helper functions.

    Allocation is performed dynamically, by the caller, during messgae reception.
    """

    def __init__(self):
        self.buffer = bytearray()

    def has_valid_message_type(self):
        return self.messageType in HarpMessage.messageTypes

    def has_valid_checksum(self):
        return self.checksum == sum(self.buffer[:-1]) & 0xff


class HarpTxMessage(HarpMessage):
    """Transmit message buffer and helper functions.

    Allocation is performed statically on initialisation.
    """

    def __init__(self, messageType, length, address, payloadType, timestamp=None):
        self.buffer = bytearray(length + HarpMessage.LENGTH_BYTE)
        self.messageType = messageType
        self.length = length
        self.address = address
        self.port = 0xff
        if timestamp is None:
            self.payloadType = payloadType & ~HarpTypes.HAS_TIMESTAMP
        else:
            self.payloadType = payloadType | HarpTypes.HAS_TIMESTAMP
            self.timestamp = timestamp

    def calc_set_checksum(self):
        self.checksum = sum(self.buffer[:-1]) & 0xff
