"""Harp datatype class."""
from micropython import const


class HarpTypes():
    """Harp datatype encodings and helper functions."""
    _SINT = const(0x80)
    U8 = const(1)
    S8 = const(U8 | _SINT)
    U16 = const(2)
    S16 = const(U16 | _SINT)
    U32 = const(4)
    S32 = const(U32 | _SINT)
    U64 = const(8)
    S64 = const(U64 | _SINT)
    FLOAT = const(0x44)
    HAS_TIMESTAMP = const(0x10)

    @staticmethod
    def size(typ):
        """Return the size, in bytes, of a Harp datatype."""
        return typ & 0x0f
