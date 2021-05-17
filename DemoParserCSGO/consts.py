PROFILE_NR = 76561197960265728

MAX_CUSTOM_FILES = 4
MAX_PATH = 260
MAX_SPLITSCREEN_CLIENTS = 2
MAX_PLAYER_NAME_LENGTH = 128
MAX_USERDATA_BITS = 14
SIGNED_GUID_LEN = 33
SUBSTRING_BITS = 5

CW_None = 0
CW_LowPrecision = 1
CW_Integral = 2

COORD_INTEGER_BITS = 14
COORD_FRACTIONAL_BITS = 5
COORD_DENOMINATOR = (1 << COORD_FRACTIONAL_BITS)
COORD_RESOLUTION = (1.0 / COORD_DENOMINATOR)

COORD_INTEGER_BITS_MP = 11
COORD_FRACTIONAL_BITS_MP_LOWPRECISION = 3
COORD_DENOMINATOR_LOWPRECISION = (1 << COORD_FRACTIONAL_BITS_MP_LOWPRECISION)
COORD_RESOLUTION_LOWPRECISION = (1.0 / COORD_DENOMINATOR_LOWPRECISION)

NORMAL_FRACTIONAL_BITS = 11
NORMAL_DENOMINATOR = (1 << NORMAL_FRACTIONAL_BITS) - 1
NORMAL_RESOLUTION = (1.0 / NORMAL_DENOMINATOR)

MAX_EDICT_BITS = 11
NETWORKED_EHANDLE_ENT_ENTRY_MASK = (1 << MAX_EDICT_BITS) - 1
NUM_NETWORKED_EHANDLE_SERIAL_NUMBER_BITS = 10
NUM_NETWORKED_EHANDLE_BITS = MAX_EDICT_BITS + NUM_NETWORKED_EHANDLE_SERIAL_NUMBER_BITS
INVALID_NETWORKED_EHANDLE_VALUE = (1 << NUM_NETWORKED_EHANDLE_BITS) - 1

# class DEM:
DEM_SIGNON = 1
DEM_PACKET = 2
DEM_SYNCTICK = 3
DEM_CONSOLECMD = 4
DEM_USERCMD = 5
DEM_DATATABLES = 6
DEM_STOP = 7
DEM_CUSTOMDATA = 8
DEM_STRINGTABLES = 9

# class PropTypes:
PT_Int = 0
PT_Float = 1
PT_Vector = 2
PT_VectorXY = 3
PT_String = 4
PT_Array = 5
PT_DataTable = 6
PT_Int64 = 7

DT_MAX_STRING_BITS = 9
DT_MAX_STRING_BUFFERSIZE = (1 << DT_MAX_STRING_BITS)


# class PropFlags:
SPROP_UNSIGNED = (1 << 0)
SPROP_COORD = (1 << 1)
SPROP_NOSCALE = (1 << 2)
SPROP_ROUNDDOWN = (1 << 3)
SPROP_ROUNDUP = (1 << 4)
SPROP_NORMAL = (1 << 5)
SPROP_EXCLUDE = (1 << 6)
SPROP_XYZE = (1 << 7)
SPROP_INSIDEARRAY = (1 << 8)
SPROP_PROXY_ALWAYS_YES = (1 << 9)
SPROP_IS_A_VECTOR_ELEM = (1 << 10)
SPROP_COLLAPSIBLE = (1 << 11)
SPROP_COORD_MP = (1 << 12)
SPROP_COORD_MP_LOWPRECISION = (1 << 13)
SPROP_COORD_MP_INTEGRAL = (1 << 14)
SPROP_CELL_COORD = (1 << 15)
SPROP_CELL_COORD_LOWPRECISION = (1 << 16)
SPROP_CELL_COORD_INTEGRAL = (1 << 17)
SPROP_CHANGES_OFTEN = (1 << 18)
SPROP_VARINT = (1 << 19)