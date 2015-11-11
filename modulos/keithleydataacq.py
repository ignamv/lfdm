import lantz
import asyncio
import ctypes
from ctypes import wintypes
import numpy as np
import functools
import queue

def ctypes_pair(type):
    return (type, ctypes.POINTER(type))

class DtLib(object):
    class Types(object):
        wt = wintypes
        class TodoType(ctypes.c_void_p):
            def __init__(self, value):
                raise NotImplementedError()
        HDEV, PHDEV = ctypes_pair(wt.HWND)
        HBUF, PHBUF = ctypes_pair(wt.HWND)
        HDASS, PHDASS = ctypes_pair(wt.HWND)
        DABRDPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.LPSTR, wt.LPSTR, wt.LPARAM)
        CAPSPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.UINT, wt.DOUBLE, wt.DOUBLE, wt.LPARAM)
        OLNOTIFYPROC = ctypes.WINFUNCTYPE(TodoType, wt.UINT, HDASS, wt.LPARAM)
        ECODE, PECODE = ctypes_pair(wt.ULONG)
        BOOL, PBOOL = ctypes_pair(wt.BOOL)
        BRIDGE_SENSOR_TEDS, PBRIDGE_SENSOR_TEDS = TodoType, TodoType 
        BUFPROC = TodoType
        CHAR, PCHAR = ctypes_pair(wt.CHAR)
        COUPLING_TYPE, PCOUPLING_TYPE = TodoType, TodoType 
        DABRDPROCEX = TodoType 
        DASSINFO, PDASSINFO = TodoType, TodoType 
        DASSPROC = TodoType 
        DBL, PDBL = ctypes_pair(wt.DOUBLE)
        DWORD, PDWORD = ctypes_pair(wt.DWORD)
        EXCITATION_CURRENT_SRC, PEXCITATION_CURRENT_SRC = TodoType, TodoType 
        FLOAT, PFLOAT = ctypes_pair(wt.FLOAT)
        HLIST, PHLIST = ctypes_pair(TodoType )
        HSSLIST, PHSSLIST = TodoType, TodoType 
        HWND = wt.HWND
        INT, PINT = ctypes_pair(wt.INT)
        LISTPROC = TodoType 
        LNG, PLNG = ctypes_pair(wt.LONG)
        LPARAM = wt.LPARAM
        PCSTR = wt.LPCSTR
        LPSTR = wt.LPSTR
        PSTR = wt.LPSTR
        LPTDS = TodoType 
        LPVOID = wt.LPVOID
        PVOID = wt.LPVOID
        OLDC = TodoType 
        OLSS = TodoType 
        OLSSC = TodoType 
        POWER_SOURCE, PPOWER_SOURCE = TodoType, TodoType 
        SSLISTPROC = TodoType 
        STRAIN_EXCITATION_VOLTAGE_SRC = TodoType 
        STRAIN_EXCITATION_VOLTAGE_SRC, PSTRAIN_EXCITATION_VOLTAGE_SRC = (TodoType,
                TodoType) 
        STRAIN_GAGE_CONFIGURATION = TodoType 
        STRAIN_GAGE_CONFIGURATION, PSTRAIN_GAGE_CONFIGURATION = TodoType, TodoType 
        STRAIN_GAGE_TEDS, PSTRAIN_GAGE_TEDS = TodoType, TodoType 
        PTSTR = wt.LPSTR
        PTDS = TodoType
        UINT, PUINT = ctypes_pair(wt.UINT)
        ULNG, PULNG = ctypes_pair(wt.ULONG)

    def __init__(self, library_file):
        self.function_names = dict()
        self.lib = ctypes.windll.LoadLibrary(library_file)

    def _register_function(self, name, argtypes, restype=Types.ECODE,
            errcheck=None):
        try:
            function = getattr(self.lib, name)
        except AttributeError as e:
            return
        self.function_names[bytes(function)] = name
        function.argtypes = argtypes
        function.restype = restype
        if restype is DtLib.Types.ECODE:
            function.errcheck = self.ecodeCheck
        else:
            function.errcheck = errcheck

    errorcodes = {
        0: ('OLSUCCESS', 'No Error'),
        1: ('OLBADCAP', 'Invalid capability specified'),
        2: ('OLBADELEMENT', 'Invalid element specified'),
        3: ('OLBADSUBSYSTEM', 'Invalid subsystem specified'),
        4: ('OLNOTENOUGHDMACHANS', 'Not Enough DMA Channels'),
        5: ('OLBADLISTSIZE', 'Invalid List Size'),
        6: ('OLBADLISTENTRY', 'Invalid List Entry'),
        7: ('OLBADCHANNEL', 'Invalid Channel'),
        8: ('OLBADCHANNELTYPE', 'Invalid Channel Type'),
        9: ('OLBADENCODING', 'Invalid Encoding'),
        10: ('OLBADTRIGGER', 'Invalid Trigger'),
        11: ('OLBADRESOLUTION', 'Invalid Resolution'),
        12: ('OLBADCLOCKSOURCE', 'Invalid Clock source'),
        13: ('OLBADFREQUENCY', 'Invalid Frequency'),
        14: ('OLBADPULSETYPE', 'Invalid Pulse Type'),
        15: ('OLBADPULSEWIDTH', 'Invalid Pulse Width'),
        16: ('OLBADCOUNTERMODE', 'Invalid Counter Mode'),
        17: ('OLBADCASCADEMODE', 'Invalid Cascade Mode'),
        18: ('OLBADDATAFLOW', 'Invalid Data Flow'),
        19: ('OLBADWINDOWHANDLE', 'Invalid Window Handle'),
        20: ('OLSUBSYSINUSE', 'Subsystem in use'),
        21: ('OLSUBSYSNOTINUSE', 'Subsystem not in use'),
        22: ('OLALREADYRUNNING', 'Subsystem already running'),
        23: ('OLNOCHANNELLIST', 'No channel list'),
        24: ('OLNOGAINLIST', 'No gain list'),
        25: ('OLNOFILTERLIST', 'No filter list'),
        26: ('OLNOTCONFIGURED', 'Subsystem Not configured'),
        27: ('OLDATAFLOWMISMATCH', 'Data flow mismatch'),
        28: ('OLNOTRUNNING', 'Subsystem not running'),
        29: ('OLBADRANGE', 'Invalid Range'),
        30: ('OLBADSSCAP', 'Invalid Subsystem Capability'),
        31: ('OLBADDEVCAP', 'Invalid DtDevice Capability'),
        32: ('OLBADRANGEINDEX', 'Invalid Range Index'),
        33: ('OLBADFILTERINDEX', 'Invalid Filter Index'),
        34: ('OLBADGAININDEX', 'Invalid Gain Index'),
        35: ('OLBADWRAPMODE', 'Invalid Wrap Mode'),
        36: ('OLNOTSUPPORTED', 'Not Supported'),
        37: ('OLBADDIVIDER', 'Invalid Divider Value'),
        38: ('OLBADGATE', 'Invalid Gate'),
        39: ('OLBADDEVHANDLE', 'Invalid DtDevice Handle'),
        40: ('OLBADSSHANDLE', 'Invalid Subsystem Handle'),
        41: ('OLCANNOTALLOCDASS', 'Cannot allocate DASS'),
        42: ('OLCANNOTDEALLOCDASS', 'Cannot Deallocate DASS'),
        43: ('OLBUFFERSLEFT', 'Transfer list not empty'),
        44: ('OLBOARDRUNNING', 'Another Subsystem on board is already running'),
        45: ('OLINVALIDCHANNELLIST', 'Channel list has been filled incorrectly'),
        46: ('OLINVALIDCLKTRIGCOMBO', 'Selected clock & trigger source may not be used together'),
        47: ('OLCANNOTALLOCLUSERDATA', 'Driver could not allocate needed memory'),
        48: ('OLCANTSVTRIGSCAN', 'Triggered Scan not available in single value mode'),
        49: ('OLCANTSVEXTCLOCK', 'External Clock is not available in single value mode'),
        50: ('OLBADRESOLUTIONINDEX', 'Bad Resolution Selected'),
        60: ('OLADTRIGERR', 'A/D Trigger Error'),
        61: ('OLADOVRRN', 'A/D Overrun Error'),
        62: ('OLDATRIGERR', 'D/A Trigger Error'),
        63: ('OLDAUNDRRN', 'D/A Underrun Error'),
        64: ('OLNOREADYBUFFERS', 'No Ready Buffers'),
        65: ('OLBADCPU', 'Library Requires i386 or i486'),
        66: ('OLBADWINMODE', 'Library Requires Windows 3.x Enhanced mode'),
        67: ('OLCANNOTOPENDRIVER', 'Driver cannot be initialized'),
        68: ('OLBADENUMCAP', 'Cannot enumerate this capability'),
        69: ('OLBADDASSPROC', 'Dass Proc CallBack NUL'),
        70: ('OLBADENUMPROC', 'Enum Proc CallBack NULL'),
        71: ('OLNOWINDOWHANDLE', 'No Window Handle'),
        72: ('OLCANTCASCADE', 'Subsystem cannot be cascaded'),
        73: ('OLINVALIDCONFIGURATION', 'Invalid configuration in SYSTEM.INI'),
        74: ('OLCANNOTALLOCJUMPERS', 'Cannot allocate memory for jumpers'),
        75: ('OLCANNOTALLOCCHANNELLIST', 'Cannot allocate channel list'),
        76: ('OLCANNOTALLOCGAINLIST', 'Cannot allocate gain list'),
        77: ('OLCANNOTALLOCFILTERLIST', 'Cannot allocate filter list'),
        78: ('OLNOBOARDSINSTALLED', 'No DT-Open Layers boards installed'),
        79: ('OLINVALIDDMASCANCOMBO', 'Invalid DMA / Scan combination'),
        80: ('OLINVALIDPULSETYPE', 'Invalid pulse type'),
        81: ('OLINVALIDGAINLIST', 'Invalid gain list'),
        82: ('OLWRONGCOUNTERMODE', 'Wrong counter mode'),
        83: ('OLLPSTRNULL', 'LPSTR passed as a parameter was NULL'),
        84: ('OLINVALIDPIODFCOMBO', 'Invalid Polled I/O combination'),
        85: ('OLINVALIDSCANTRIGCOMBO', 'Invalid Scan / Trigger combo'),
        86: ('OLBADGAIN', 'Invalid Gain'),
        87: ('OLNOMEASURENOTIFY', 'No window handle specified for frequency measurement'),
        88: ('OLBADCOUNTDURATION', 'Invalid count duration for frequency measurement'),
        89: ('OLBADQUEUE', 'Invalid queue type specified'),
        90: ('OLBADRETRIGGERRATE', 'Invalid Retrigger Rate for channel list size'),
        91: ('OLCOMMANDTIMEOUT', 'No Command Response from Hardware'),
        92: ('OLCOMMANDOVERRUN', 'Hardware Command Sequence Error'),
        93: ('OLDATAOVERRUN', 'Hardware Data Sequence Error'),
        94: ('OLCANNOTALLOCTIMERDATA', 'Cannot allocate timer data for driver'),
        95: ('OLBADHTIMER', 'Invalid Timer handle'),
        96: ('OLBADTIMERMODE', 'Invalid Timer mode'),
        97: ('OLBADTIMERFREQUENCY', 'Invalid Timer frequency'),
        98: ('OLBADTIMERPROC', 'Invalid Timer callback procedure'),
        99: ('OLBADDMABUFFERSIZE', 'Invalid Timer DMA buffer size'),
        100: ('OLBADDIGITALIOLISTVALUE', 'Illegal synchronous digital I/O value requested.'),
        101: ('OLCANNOTALLOCSSLIST', 'Cannot allocate simultaneous start list'),
        102: ('OLBADSSLISTHANDLE', 'Illegal simultaneous start list handle specified.'),
        103: ('OLBADSSHANDLEONLIST', 'Invalid subsystem handle on simultaneous start list.'),
        104: ('OLNOSSHANDLEONLIST', 'No subsystem handles on simultaneous start list.'),
        105: ('OLNOCHANNELINHIBITLIST', 'The subsystem has no channel inhibit list.'),
        106: ('OLNODIGITALIOLIST', 'The subsystem has no digital I/O list.'),
        107: ('OLNOTPRESTARTED', 'The subsystem has not been prestarted.'),
        108: ('OLBADNOTIFYPROC', 'Invalid notification procedure'),
        109: ('OLBADTRANSFERCOUNT', 'Invalid DT-Connect transfer count'),
        110: ('OLBADTRANSFERSIZE', 'Invalid DT-Connect transfer size'),
        111: ('OLCANNOTALLOCINHIBITLIST', 'Cannot allocate channel inhibit list'),
        112: ('OLCANNOTALLOCDIGITALIOLIST', 'Cannot allocate digital I/O list'),
        113: ('OLINVALIDINHIBITLIST', 'Channel inhibit list has been filled incorrectly'),
        114: ('OLSSHANDLEALREADYONLIST', 'Dass handle is already on simultaneous start list'),
        115: ('OLCANNOTALLOCRANGELIST', 'Cannot allocate range list'),
        116: ('OLNORANGELIST', 'No range list'),
        117: ('OLNOBUFFERINPROCESS', 'No buffers in process'),
        118: ('OLREQUIREDSUBSYSINUSE', 'Additional required sub system in use'),
        119: ('OLWRAPMODEMISMATCH', 'Wrap mode mismatch'),
        120: ('OLVXDNOTINSTALLED', 'VDTDAD virtual device driver not loaded'),
        121: ('OLBADRETRIGGERMODE', 'Invalid Retrigger Mode'),
        122: ('OLBADCOUNT', 'Invalid count.  Count exceeds maximum # of scans of the CGL.'),
        123: ('OLBADRETRIGGER', 'Invalid Retrigger'),
        124: ('OLBADPRETRIGGER', 'Invalid Pretrigger'),
        125: ('OLGENERALFAILURE', 'General Failure'),
        126: ('OLREQUESTPENDING', 'Defer Completion of Open Layers call'),
        127: ('OLUNSUPPORTEDSYSTEM', 'Operating System not supported'),
        128: ('OLBADEDGE', 'Invalid counter edge specified'),
        129: ('OLHALFCTR', 'Only half of 32 bit count value read via CGL'),
        130: ('OLBADINDEX', 'Invalid Index'),
        131: ('OLINVALIDX4INDEXCOMBO', 'Invalid combination of Index and X4Scaling'),
        132: ('OLBADCOUPLINGTYPE', 'Invalid coupling type'),
        133: ('OLBADEXCITATIONCURRENTSRC', 'Invalid current source'),
        134: ('OLBADVALUE', 'Invalid value set'),
        135: ('OLINVALIDWHENADRUNNING', 'Operation is prohibited while A/D is running'),
        136: ('OLBADTHERMOCOUPLETYPE', 'Invalid thermocouple type was specified'),
        137: ('OLNOMEMORY', 'Internal memory allocation failed'),
        138: ('OLBADRETURNPOINTER', 'The return value pointer is not valid'),
        139: ('OLBADRTDTYPE', 'Invalid RTD type was specified'),
        140: ('OLBADSYNCMODE', 'Invalid synchronization mode specified'),
        141: ('OLBADDATAFILTERTYPE', 'Invalid data filter type was specified'),
        142: ('OLINVALIDWHENDARUNNING', 'Operation is prohibited while D/A is running'),
        143: ('OLCANNOTALLOCSTRAINLIST', 'Cannot allocate strain config list'),
        144: ('OLTEDSERROR', 'an error encountered while parsing TEDS'),
        200: ('OLCANNOTALLOCBCB', 'Cannot allocate a buffer control block for the requested data buffer.'),
        201: ('OLCANNOTALLOCBUFFER', 'Cannot allocate the requested data buffer.'),
        202: ('OLBADBUFFERHANDLE', 'Invalid buffer handle (HBUF) passed to a library from an application.'),
        203: ('OLBUFFERLOCKFAILED', 'The data buffer cannot be put to a section because it cannot be properly locked.'),
        204: ('OLBUFFERLOCKED', 'Buffer Locked'),
        205: ('OLBUFFERONLIST', 'Buffer on List'),
        206: ('OLCANNOTREALLOCBCB', 'Reallocation of a buffer control block was unsuccessful.'),
        207: ('OLCANNOTREALLOCBUFFER', 'Reallocation of the data buffer was unsuccessful.'),
        208: ('OLBADSAMPLESIZE', 'Bad Sample Size'),
        209: ('OLCANNOTALLOCLIST', 'Cannot Allocate List'),
        210: ('OLBADLISTHANDLE', 'Bad List Handle'),
        211: ('OLLISTNOTEMPTY', 'List Not Empty'),
        212: ('OLBUFFERNOTLOCKED', 'Bufffer Not Locked'),
        213: ('OLBADDMACHANNEL', 'Invalid DMA Channel specified'),
        214: ('OLDMACHANNELINUSE', 'Specified DMA Channel in use'),
        215: ('OLBADIRQ', 'Invalid IRQ specified'),
        216: ('OLIRQINUSE', 'Specififed IRQ in use'),
        217: ('OLNOSAMPLES', 'Buffer has no valid samples'),
        218: ('OLTOOMANYSAMPLES', 'Valid Samples cannot be larger than buffer'),
        219: ('OLBUFFERTOOSMALL', 'Specified buffer too small for requested copy operation'),
        220: ('OLODDSIZEDBUFFER', 'Num buffer points must be multiple 2 for this operation')
    }
    def ecodeCheck(self, ecode, function, args):
        if ecode != 0:
            raise Exception('Calling {} with arguments {}: {} {}'.format(
                self.function_names[bytes(function)], args,
                *DtLib.errorcodes[ecode]))

class LibDacq(DtLib):
    class Encoding(object):
        BINARY = 200
        TWOSCOMP = 201
    class Differential(object):
        SINGLEENDED = 100
        DIFFERENTIAL = 101

    def __init__(self):
        super().__init__('oldaapi32.dll')
        f = self._register_function
        T = DtLib.Types
        f('olDaInitialize', [T.PTSTR, T.PHDEV])
        f('olDaTerminate', [T.HDEV])
        f('olDaGetVersion', [T.PTSTR, T.UINT])
        f('olDaGetDriverVersion', [T.HDEV, T.PTSTR, T.UINT])
        f('olDaPutBuffer', [T.HDASS, T.HBUF])
        f('olDaGetBuffer', [T.HDASS, T.PHBUF])
        f('olDaGetDeviceName', [T.HDEV, T.PTSTR, T.UINT])
        f('olDaEnumBoards', [T.DABRDPROC, T.LPARAM])
        f('olDaEnumBoardsEx', [T.DABRDPROCEX, T.LPARAM])
        f('olDaEnumSubSystems', [T.HDEV, T.DASSPROC, T.LPARAM])
        f('olDaGetDASS', [T.HDEV, T.OLSS, T.UINT, T.PHDASS])
        f('olDaReleaseDASS', [T.HDASS])
        f('olDaGetDASSInfo', [T.HDASS, T.PDASSINFO])
        f('olDaGetDevCaps', [T.HDEV, T.OLDC, T.PUINT])
        f('olDaGetSSCaps', [T.HDASS, T.OLSSC, T.PUINT])
        f('olDaGetSSCapsEx', [T.HDASS, T.OLSSC, T.PDBL])
        f('olDaEnumSSCaps', [T.HDASS, T.UINT, T.CAPSPROC, T.LPARAM])
        f('olDaSetDmaUsage', [T.HDASS, T.UINT])
        f('olDaGetDmaUsage', [T.HDASS, T.PUINT])
        f('olDaSetTriggeredScanUsage', [T.HDASS, T.BOOL])
        f('olDaGetTriggeredScanUsage', [T.HDASS, T.PBOOL])
        f('olDaSetChannelType', [T.HDASS, T.UINT])
        f('olDaGetChannelType', [T.HDASS, T.PUINT])
        f('olDaSetChannelListSize', [T.HDASS, T.UINT])
        f('olDaGetChannelListSize', [T.HDASS, T.PUINT])
        f('olDaSetChannelListEntry', [T.HDASS, T.UINT, T.UINT])
        f('olDaGetChannelListEntry', [T.HDASS, T.UINT, T.PUINT])
        f('olDaSetGainListEntry', [T.HDASS, T.UINT, T.DBL])
        f('olDaGetGainListEntry', [T.HDASS, T.UINT, T.PDBL])
        f('olDaSetChannelFilter', [T.HDASS, T.UINT, T.DBL])
        f('olDaGetChannelFilter', [T.HDASS, T.UINT, T.PDBL])
        f('olDaSetEncoding', [T.HDASS, T.UINT])
        f('olDaGetEncoding', [T.HDASS, T.PUINT])
        f('olDaSetTrigger', [T.HDASS, T.UINT])
        f('olDaGetTrigger', [T.HDASS, T.PUINT])
        f('olDaSetResolution', [T.HDASS, T.UINT])
        f('olDaGetResolution', [T.HDASS, T.PUINT])
        f('olDaSetRange', [T.HDASS, T.DBL, T.DBL])
        f('olDaGetRange', [T.HDASS, T.PDBL, T.PDBL])
        f('olDaSetClockSource', [T.HDASS, T.UINT])
        f('olDaGetClockSource', [T.HDASS, T.PUINT])
        f('olDaSetClockFrequency', [T.HDASS, T.DBL])
        f('olDaGetClockFrequency', [T.HDASS, T.PDBL])
        f('olDaSetRetriggerFrequency', [T.HDASS, T.DBL])
        f('olDaGetRetriggerFrequency', [T.HDASS, T.PDBL])
        f('olDaSetExternalClockDivider', [T.HDASS, T.ULNG])
        f('olDaGetExternalClockDivider', [T.HDASS, T.PULNG])
        f('olDaSetGateType', [T.HDASS, T.UINT])
        f('olDaGetGateType', [T.HDASS, T.PUINT])
        f('olDaSetPulseType', [T.HDASS, T.UINT])
        f('olDaGetPulseType', [T.HDASS, T.PUINT])
        f('olDaSetPulseWidth', [T.HDASS, T.DBL])
        f('olDaGetPulseWidth', [T.HDASS, T.PDBL])
        f('olDaSetCTMode', [T.HDASS, T.UINT])
        f('olDaGetCTMode', [T.HDASS, T.PUINT])
        f('olDaSetCascadeMode', [T.HDASS, T.UINT])
        f('olDaGetCascadeMode', [T.HDASS, T.PUINT])
        f('olDaReadEvents', [T.HDASS, T.PULNG])
        f('olDaConfig', [T.HDASS])
        f('olDaStart', [T.HDASS])
        f('olDaStop', [T.HDASS])
        f('olDaContinue', [T.HDASS])
        f('olDaReset', [T.HDASS])
        f('olDaFlushBuffers', [T.HDASS])
        f('olDaSetWndHandle', [T.HDASS, T.HWND, T.LPARAM])
        f('olDaPutSingleValue', [T.HDASS, T.LNG, T.UINT, T.DBL])
        f('olDaPutSingleValues', [T.HDASS, T.PLNG, T.DBL])
        f('olDaGetSingleValue', [T.HDASS, T.PLNG, T.UINT, T.DBL])
        f('olDaGetSingleValues', [T.HDASS, T.PLNG, T.DBL])
        f('olDaGetDataFlow', [T.HDASS, T.PUINT])
        f('olDaSetDataFlow', [T.HDASS, T.UINT])
        f('olDaGetWrapMode', [T.HDASS, T.PUINT])
        f('olDaSetWrapMode', [T.HDASS, T.UINT])
        f('olDaPause', [T.HDASS])
        f('olDaAbort', [T.HDASS])
        f('olDaMeasureFrequency', [T.HDASS, T.HWND , T.DBL])
        f('olDaGetQueueSize', [T.HDASS, T.UINT, T.PUINT])
        f('olDaDTConnectBurst', [T.HDASS, T.UINT, T.UINT])
        f('olDaSetChannelListEntryInhibit', [T.HDASS, T.UINT, T.BOOL])
        f('olDaGetChannelListEntryInhibit', [T.HDASS, T.UINT, T.PBOOL])
        f('olDaSetDigitalIOListEntry', [T.HDASS, T.UINT, T.UINT])
        f('olDaGetDigitalIOListEntry', [T.HDASS, T.UINT, T.PUINT])
        f('olDaSetSynchronousDigitalIOUsage', [T.HDASS, T.BOOL])
        f('olDaGetSynchronousDigitalIOUsage', [T.HDASS, T.PBOOL])
        f('olDaGetSSList', [T.PHSSLIST])
        f('olDaReleaseSSList', [T.HSSLIST])
        f('olDaPutDassToSSList', [T.HSSLIST, T.HDASS])
        f('olDaSimultaneousPrestart', [T.HSSLIST])
        f('olDaSimultaneousStart', [T.HSSLIST])
        f('olDaEnumSSList', [T.HSSLIST, T.SSLISTPROC, T.LPARAM])
        f('olDaFlushFromBufferInprocess', [T.HDASS, T.HBUF, T.ULNG])
        f('olDaSetNotificationProcedure', [T.HDASS, T.OLNOTIFYPROC, T.LPARAM])
        f('olDaSetDTConnectTransferSize', [T.HDASS, T.UINT])
        f('olDaGetDTConnectTransferSize', [T.HDASS, T.PUINT])
        f('olDaSetDTConnectTransferCount', [T.HDASS, T.UINT])
        f('olDaGetDTConnectTransferCount', [T.HDASS, T.PUINT])
        f('olDaSetChannelRange', [T.HDASS, T.UINT, T.DBL, T.DBL])
        f('olDaGetChannelRange', [T.HDASS, T.UINT, T.PDBL, T.PDBL])
        f('olDaSetRetriggerMode', [T.HDASS, T.UINT])
        f('olDaGetRetriggerMode', [T.HDASS, T.PUINT])
        f('olDaGetSystemMetrics', [T.HDASS, T.PDWORD, T.PDWORD])
        f('olDaEnableSystemMetrics', [T.HDASS, T.BOOL, T.BOOL])
        f('olDaEnableHighResolutionTiming', [T.BOOL])
        f('olDaSetPretriggerSource', [T.HDASS, T.UINT])
        f('olDaGetPretriggerSource', [T.HDASS, T.PUINT])
        f('olDaSetMultiscanCount', [T.HDASS, T.UINT])
        f('olDaGetMultiscanCount', [T.HDASS, T.PUINT])
        f('olDaSetRetrigger', [T.HDASS, T.UINT])
        f('olDaGetRetrigger', [T.HDASS, T.PUINT])
        f('olDaGetSingleValueEx', [T.HDASS, T.UINT, T.BOOL, T.PDBL, T.PLNG, T.PDBL])
        f('olDaSetMeasureStartEdge', [T.HDASS, T.UINT])
        f('olDaGetMeasureStartEdge', [T.HDASS, T.PUINT])
        f('olDaSetMeasureStopEdge', [T.HDASS, T.UINT])
        f('olDaGetMeasureStopEdge', [T.HDASS, T.PUINT])
        f('olDaSetCouplingType', [T.HDASS, T.UINT, T.COUPLING_TYPE])
        f('olDaGetCouplingType', [T.HDASS, T.UINT, T.PCOUPLING_TYPE])
        f('olDaSetExcitationCurrentSource', [T.HDASS, T.UINT, T.EXCITATION_CURRENT_SRC])
        f('olDaGetExcitationCurrentSource', [T.HDASS, T.UINT, T.PEXCITATION_CURRENT_SRC])
        f('olDaSetExcitationCurrentValue', [T.HDASS, T.UINT, T.DBL])
        f('olDaGetExcitationCurrentValue', [T.HDASS, T.UINT, T.PDBL])
        f('olDaSetThermocoupleType', [T.HDASS, T.UINT, T.UINT])
        f('olDaGetThermocoupleType', [T.HDASS, T.UINT, T.PUINT])
        f('olDaSetReturnCjcTemperatureInStream', [T.HDASS, T.BOOL])
        f('olDaGetReturnCjcTemperatureInStream', [T.HDASS, T.PBOOL])
        f('olDaGetSingleFloat', [T.HDASS, T.PFLOAT, T.UINT, T.DBL])
        f('olDaGetSingleFloats', [T.HDASS, T.PFLOAT, T.DBL])
        f('olDaGetCjcTemperature', [T.HDASS, T.PFLOAT, T.UINT])
        f('olDaGetCjcTemperatures', [T.HDASS, T.PFLOAT])
        f('olDaIsRunning', [T.HDASS, T.PBOOL])
        f('olDaAutoCalibrate', [T.HDASS])
        f('olDaSetRtdType', [T.HDASS, T.UINT, T.UINT])
        f('olDaGetRtdType', [T.HDASS, T.UINT, T.PUINT])
        f('olDaSetChanVoltageRange', [T.HDASS, T.UINT, T.UINT])
        f('olDaGetChannelVoltageRange', [T.HDASS, T.UINT, T.PUINT])
        f('olDaSetSyncMode', [T.HDASS, T.UINT])
        f('olDaGetSyncMode', [T.HDASS, T.PUINT])
        f('olDaSetDataFilterType', [T.HDASS, T.UINT])
        f('olDaGetDataFilterType', [T.HDASS, T.PUINT])
        f('olDaSetStaleDataFlagEnabled', [T.HDASS, T.BOOL])
        f('olDaGetStaleDataFlagEnabled', [T.HDASS, T.PBOOL])
        f('olDaSetEdgeType', [T.HDASS, T.UINT])
        f('olDaGetEdgeType', [T.HDASS, T.PUINT])
        f('olDaGetPowerSource', [T.HDEV, T.PPOWER_SOURCE])
        f('olDaSetTriggerThresholdLevel', [T.HDASS, T.DBL])
        f('olDaGetTriggerThresholdLevel', [T.HDASS, T.PDBL])
        f('olDaSetTriggerThresholdChannel', [T.HDASS, T.INT])
        f('olDaGetTriggerThresholdChannel', [T.HDASS, T.PINT])
        f('olDaSetReferenceTrigger', [T.HDASS, T.UINT])
        f('olDaGetReferenceTrigger', [T.HDASS, T.PUINT])
        f('olDaSetReferenceTriggerThresholdLevel', [T.HDASS, T.DBL])
        f('olDaGetReferenceTriggerThresholdLevel', [T.HDASS, T.PDBL])
        f('olDaSetReferenceTriggerThresholdChannel', [T.HDASS, T.INT])
        f('olDaGetReferenceTriggerThresholdChannel', [T.HDASS, T.PINT])
        f('olDaSetReferenceTriggerPostScanCount', [T.HDASS, T.INT])
        f('olDaGetReferenceTriggerPostScanCount', [T.HDASS, T.PINT])
        f('olDaSetStrainExcitationVoltageSource', [T.HDASS, T.STRAIN_EXCITATION_VOLTAGE_SRC])
        f('olDaGetStrainExcitationVoltageSource', [T.HDASS, T.PSTRAIN_EXCITATION_VOLTAGE_SRC])
        f('olDaSetStrainExcitationVoltage', [T.HDASS, T.DBL])
        f('olDaGetStrainExcitationVoltage', [T.HDASS, T.PDBL])
        f('olDaSetStrainBridgeConfiguration', [T.HDASS, T.UINT, T.STRAIN_GAGE_CONFIGURATION])
        f('olDaGetStrainBridgeConfiguration', [T.HDASS, T.UINT, T.PSTRAIN_GAGE_CONFIGURATION])
        f('olDaSetStrainShuntResistor', [T.HDASS, T.UINT, T.BOOL])
        f('olDaReadBridgeSensorVirtualTeds', [T.PCHAR, T.PBRIDGE_SENSOR_TEDS])
        f('olDaReadBridgeSensorHardwareTeds', [T.HDASS, T.UINT, T.PBRIDGE_SENSOR_TEDS])
        f('olDaReadStrainGageVirtualTeds', [T.PCHAR, T.PSTRAIN_GAGE_TEDS])
        f('olDaReadStrainGageHardwareTeds', [T.HDASS, T.UINT, T.PSTRAIN_GAGE_TEDS])
        f('olDaMute', [T.HDASS])
        f('olDaUnMute', [T.HDASS])
dacq = LibDacq()

class LibMem(DtLib):
    def __init__(self):
        super().__init__('OLMEM32.dll')
        f = self._register_function
        T = DtLib.Types
        f('olDmAllocBuffer', [T.UINT, T.DWORD, T.PHBUF])
        f('olDmFreeBuffer', [T.HBUF])
        f('olDmReAllocBuffer', [T.UINT, T.DWORD, T.PHBUF])
        f('olDmGetTimeDateStamp', [T.HBUF, T.PTDS])
        f('olDmGetBufferPtr', [T.HBUF, ctypes.POINTER(T.PVOID)])
        f('olDmGetBufferECode', [T.HBUF, T.PECODE])
        f('olDmGetBufferSize', [T.HBUF, ctypes.POINTER(T.PDWORD)])
        f('olDmGetVersion', [T.PSTR])
        f('olDmCopyBuffer', [T.HBUF, T.PVOID])
        f('olDmCopyToBuffer', [T.HBUF, T.PVOID, T.ULNG])
        f('olDmCallocBuffer', [T.UINT, T.UINT, T.DWORD, T.UINT, T.PHBUF])
        f('olDmMallocBuffer', [T.UINT, T.UINT, T.DWORD, T.PHBUF])
        f('olDmLockBuffer', [T.HBUF])
        f('olDmUnlockBuffer', [T.HBUF])
        f('olDmReCallocBuffer', [T.UINT, T.UINT, T.DWORD, T.UINT, T.PHBUF])
        f('olDmReMallocBuffer', [T.UINT, T.UINT, T.DWORD, T.PHBUF])
        f('olDmGetDataBits', [T.HBUF, T.UINT])
        f('olDmSetDataWidth', [T.HBUF, T.UINT])
        f('olDmGetDataWidth', [T.HBUF, T.UINT])
        f('olDmGetMaxSamples', [T.HBUF, T.PDWORD])
        f('olDmSetValidSamples', [T.HBUF, T.DWORD])
        f('olDmGetValidSamples', [T.HBUF, T.PDWORD])
        f('olDmCopyFromBuffer', [T.HBUF, T.PVOID, T.ULNG])
        f('olDmSetExtraBytes', [T.HBUF, T.ULNG, T.ULNG])
        f('olDmLockBufferEx', [T.HBUF, T.BOOL])
        f('olDmUnlockBufferEx', [T.HBUF, T.BOOL])
        f('drvDmSetCurrentTDS', [T.HBUF])
        f('drvDmSetDataBits', [T.HBUF, T.UINT])
        f('drvDmPutBufferToListForDriver', [T.HLIST, T.HBUF])
        f('drvDmGetBufferFromListForDriver', [T.HLIST, T.PHBUF])
        f('olDmCreateList', [T.PHLIST, T.UINT, T.PCSTR, T.PCSTR])
        f('olDmEnumLists', [T.LISTPROC, T.LPARAM])
        f('olDmEnumBuffers', [T.HLIST, T.BUFPROC, T.LPARAM])
        f('olDmFreeList', [T.HLIST])
        f('olDmPutBufferToList', [T.HLIST, T.HBUF])
        f('olDmGetBufferFromList', [T.HLIST, T.PHBUF])
        f('olDmPeekBufferFromList', [T.HLIST, T.PHBUF])
        f('olDmGetListCount', [T.HLIST, T.PUINT])
        f('olDmGetListHandle', [T.HBUF, T.PHLIST])
        f('olDmGetListIds', [T.HLIST, T.PSTR, T.UINT, T.PSTR, T.UINT])
        f('olDmLockBufferEx', [T.HBUF, T.BOOL])
        f('olDmUnLockBufferEx', [T.HBUF, T.BOOL])
mem = LibMem()

class DtDevice(object):
    class Capabilities():
        ADELEMENTS = 0
        DAELEMENTS = 1
        DINELEMENTS = 2
        DOUTELEMENTS = 3
        SRLELEMENTS = 4
        CTELEMENTS = 5
        TACHELEMENTS = 6
        SUP_INTERNAL_EXTERNAL_POWER = 7

    def __init__(self, name):
        self.handle = DtLib.Types.HDEV(0)
        dacq.lib.olDaInitialize(name, ctypes.byref(self.handle))
        self.open_subsystems = []
        count = ctypes.c_uint()
        dacq.lib.olDaGetDevCaps(self.handle, DtDevice.Capabilities.ADELEMENTS,
                ctypes.byref(count))
        self.ad = []
        for ii in range(count.value):
            self.ad.append(ADSubsystem(self, ii))
        dacq.lib.olDaGetDevCaps(self.handle, DtDevice.Capabilities.DAELEMENTS,
                ctypes.byref(count))
        self.da = []
        for ii in range(count.value):
            self.da.append(DASubsystem(self, ii))
        dacq.lib.olDaGetDevCaps(self.handle, DtDevice.Capabilities.DOUTELEMENTS,
                ctypes.byref(count))
        self.dout = []
        for ii in range(count.value):
            self.dout.append(DOutSubsystem(self, ii))
        dacq.lib.olDaGetDevCaps(self.handle, DtDevice.Capabilities.CTELEMENTS,
                ctypes.byref(count))
        self.ct = []
        for ii in range(count.value):
            self.ct.append(CounterTimerSubsystem(self, ii))

    def getSubsystem(self, type, index):
        handle = DtLib.Types.HDASS()
        dacq.lib.olDaGetDASS(self.handle, type, index, ctypes.byref(handle))
        self.open_subsystems.append(handle)
        return handle

    def __del__(self):
        for ad in self.ad:
            ad.close()
        for handle in self.open_subsystems:
            dacq.lib.olDaReleaseDASS(handle)
        dacq.lib.olDaTerminate(self.handle)

    @staticmethod
    def open_first():
        name = None
        def callback(boardName, driverName, param):
            nonlocal name
            name = boardName
            return False
        dacq.lib.olDaEnumBoards(DtLib.Types.DABRDPROC(callback), 0)
        if name is None:
            raise IndexError('No boards')
        return DtDevice(name)


class Subsystem(lantz.Driver):
    class DataFlow():
        CONTINUOUS = 800
        SINGLEVALUE = 801
        DTCONNECT_CONTINUOUS = 802
        DTCONNECT_BURST = 803
        CONTINUOUS_PRETRIG = 804
        CONTINUOUS_ABOUTTRIG = 805

    class Messages(object):
        TRIGGER_ERROR = 0x400+100
        UNDERRUN_ERROR = 0x400+101
        OVERRUN_ERROR = 0x400+102
        BUFFER_DONE = 0x400+103
        QUEUE_DONE = 0x400+104
        BUFFER_REUSED = 0x400+105
        QUEUE_STOPPED = 0x400+106
        EVENT_ERROR = 0x400+107
        MEASURE_DONE = 0x400+108
        DTCONNECT_DONE = 0x400+109
        DTCONNECT_STOPPED = 0x400+110
        EVENT_DONE = 0x400+111
        PRETRIGGER_BUFFER_DONE = 0x400+112
        DEVICE_REMOVAL = 0x400+113
        IO_COMPLETE = 0x400+114
    class Types(object):
        AD = 0
        DA = 1
        DIN = 2
        DOUT = 3
        SRL = 4
        CT = 5
        TACH = 6
    capabilities = dict(
        MAXSECHANS = 0,
        MAXDICHANS = 1,
        CGLDEPTH = 2,
        NUMFILTERS = 3,
        NUMGAINS = 4,
        NUMRANGES = 5,
        NUMDMACHANS = 6,
        NUMCHANNELS = 7,
        NUMEXTRACLOCKS = 8,
        NUMEXTRATRIGGERS = 9,
        NUMRESOLUTIONS = 10,
        SUP_INTERRUPT = 11,
        SUP_SINGLEENDED = 12,
        SUP_DIFFERENTIAL = 13,
        SUP_BINARY = 14,
        SUP_2SCOMP = 15,
        SUP_SOFTTRIG = 16,
        SUP_EXTERNTRIG = 17,
        SUP_THRESHTRIGPOS = 18,
        SUP_THRESHTRIGNEG = 19,
        SUP_ANALOGEVENTTRIG = 20,
        SUP_DIGITALEVENTTRIG = 21,
        SUP_TIMEREVENTTRIG = 22,
        SUP_TRIGSCAN = 23,
        SUP_INTCLOCK = 24,
        SUP_EXTCLOCK = 25,
        SUP_SWCAL = 26,
        SUP_EXP2896 = 27,
        SUP_EXP727 = 28,
        SUP_FILTERPERCHAN = 29,
        SUP_DTCONNECT = 30,
        SUP_FIFO = 31,
        SUP_PROGRAMGAIN = 32,
        SUP_PROCESSOR = 33,
        SUP_SWRESOLUTION = 34,
        SUP_CONTINUOUS = 35,
        SUP_SINGLEVALUE = 36,
        SUP_PAUSE = 37,
        SUP_WRPMULTIPLE = 38,
        SUP_WRPSINGLE = 39,
        SUP_POSTMESSAGE = 40,
        SUP_CASCADING = 41,
        MAX_DIGITALIOLIST_VALUE = 46,
        SUP_DTCONNECT_CONTINUOUS = 47,
        SUP_DTCONNECT_BURST = 48,
        SUP_CHANNELLIST_INHIBIT = 49,
        SUP_SYNCHRONOUS_DIGITALIO = 50,
        SUP_SIMULTANEOUS_START = 51,
        SUP_INPROCESSFLUSH = 52,
        SUP_RANGEPERCHANNEL = 53,
        SUP_SIMULTANEOUS_SH = 54,
        SUP_RANDOM_CGL = 55,
        SUP_SEQUENTIAL_CGL = 56,
        SUP_ZEROSEQUENTIAL_CGL = 57,
        SUP_GAPFREE_NODMA = 58,
        SUP_GAPFREE_SINGLEDMA = 59,
        SUP_GAPFREE_DUALDMA = 60,
        MAXTHROUGHPUT = 61,
        MINTHROUGHPUT = 62,
        MAXRETRIGGER = 63,
        MINRETRIGGER = 64,
        MAXCLOCKDIVIDER = 65,
        MINCLOCKDIVIDER = 66,
        BASECLOCK = 67,
        RANGELOW = 68,
        RANGEHIGH = 69,
        FILTER = 70,
        GAIN = 71,
        RESOLUTION = 72,
        SUP_PLS_HIGH2LOW = 73,
        SUP_PLS_LOW2HIGH = 74,
        SUP_GATE_NONE = 75,
        SUP_GATE_HIGH_LEVEL = 76,
        SUP_GATE_LOW_LEVEL = 77,
        SUP_GATE_HIGH_EDGE = 78,
        SUP_GATE_LOW_EDGE = 79,
        SUP_GATE_LEVEL = 80,
        SUP_GATE_HIGH_LEVEL_DEBOUNCE = 81,
        SUP_GATE_LOW_LEVEL_DEBOUNCE = 82,
        SUP_GATE_HIGH_EDGE_DEBOUNCE = 83,
        SUP_GATE_LOW_EDGE_DEBOUNCE = 84,
        SUP_GATE_LEVEL_DEBOUNCE = 85,
        OLSS_SUP_RETRIGGER_INTERNAL = 86,
        OLSS_SUP_RETRIGGER_SCAN_PER_TRIGGER = 87,
        MAXMULTISCAN = 88,
        SUP_CONTINUOUS_PRETRIG = 89,
        SUP_CONTINUOUS_ABOUTTRIG = 90,
        SUP_BUFFERING = 91,
        SUP_RETRIGGER_EXTRA = 92,
        NONCONTIGUOUS_CHANNELNUM = 93,
        SUP_SINGLEVALUE_AUTORANGE = 94,
        SUP_CTMODE_UP_DOWN = 95,
        SUP_CTMODE_MEASURE = 96,
        SUP_WRPWAVEFORM = 97,
        FIFO_SIZE_IN_K = 98,
        SUP_SIMULTANEOUS_CLOCKING = 99,
        SUP_FIXED_PULSE_WIDTH = 100,
        SUP_QUADRATURE_DECODER = 101,
        SUP_CTMODE_CONT_MEASURE = 102,
        SUP_AC_COUPLING = 103,
        SUP_DC_COUPLING = 104,
        SUP_EXTERNAL_EXCITATION_CURRENT_SOURCE = 105,
        SUP_INTERNAL_EXCITATION_CURRENT_SOURCE = 106,
        EXCITATION_CURRENT_VALUE = 107,
        NUM_EXCITATION_CURRENT_VALUES = 108,
        SUP_WRPWAVEFORM_ONLY = 109,
        SUP_INTERLEAVED_CJC_IN_STREAM = 110,
        SUP_THERMOCOUPLES = 111,
        SUP_TEMPERATURE_DATA_IN_STREAM = 112,
        SUP_CJC_SOURCE_CHANNEL = 113,
        SUP_CJC_SOURCE_INTERNAL = 114,
        CJC_MILLIVOLTS_PER_DEGREE_C = 115,
        RETURNS_FLOATS = 116,
        CURRENT_OUTPUTS = 117,
        SUP_PUT_SINGLE_VALUES = 118,
        SUP_SV_POS_EXTERN_TTLTRIG = 119,
        SUP_SV_NEG_EXTERN_TTLTRIG = 120,
        SUP_AUTO_CALIBRATE = 121,
        SUP_RTDS = 122,
        RETURNS_OHMS = 123,
        SUP_SYNCHRONIZATION = 124,
        SUP_DATA_FILTERS = 125,
        SUP_NO_RAW_DATA = 126,
        SUP_VOLTAGE_RANGES = 127,
        SUP_STALE_DATA_FLAG = 128,
        SUP_EXTERNTTLPOS_REFERENCE_TRIG = 129,
        SUP_EXTERNTTLNEG_REFERENCE_TRIG = 130,
        SUP_THRESHPOS_REFERENCE_TRIG = 131,
        SUP_THRESHNEG_REFERENCE_TRIG = 132,
        SUP_POST_REFERENCE_TRIG_SCANCOUNT = 133,
        SUP_STRAIN_GAGE = 134,
        SUP_INTERNAL_EXCITATION_VOLTAGE_SOURCE = 135,
        SUP_EXTERNAL_EXCITATION_VOLTAGE_SOURCE = 136,
        MIN_EXCITATION_VOLTAGE = 137,
        MAX_EXCITATION_VOLTAGE = 138,
        SUP_SHUNT_CALIBRATION = 139,
        SUP_REMOTE_SENSE = 140,
        SUP_SYNCBUS_REFERENCE_TRIG = 141,
        SUP_MUTE = 142)
    # for OLDRV_SETCHANNELTYPE
    # for OLDRV_SETENCODING            
    ENC_BINARY = 200
    ENC_2SCOMP = 201

    # for OLDRV_SETTRIGGER             
    TRG_SOFT = 300
    TRG_EXTERN = 301
    TRG_THRESH = 302
    TRG_ANALOGEVENT = 303
    TRG_DIGITALEVENT = 304
    TRG_TIMEREVENT = 305
    TRG_EXTRA = 306

    # for OLDRV_SETCLOCKSOURCE         
    CLK_INTERNAL = 400
    CLK_EXTERNAL = 401
    CLK_EXTRA = 402

    # for OLDRV_SETGATETYPE            
    GATE_NONE = 500
    GATE_HIGH_LEVEL = 501
    GATE_LOW_LEVEL = 502
    GATE_HIGH_EDGE = 503
    GATE_LOW_EDGE = 504
    GATE_LEVEL = 505
    GATE_HIGH_LEVEL_DEBOUNCE = 506
    GATE_LOW_LEVEL_DEBOUNCE = 507
    GATE_HIGH_EDGE_DEBOUNCE = 508
    GATE_LOW_EDGE_DEBOUNCE = 509
    GATE_LEVEL_DEBOUNCE = 510


    # for OLDRV_SETPULSETYPE           
    PLS_HIGH2LOW = 600
    PLS_LOW2HIGH = 601


    # for OLDRV_SETMEASUREMENT			
    GATE_RISING = 750
    GATE_FALLING = 751
    CLOCK_RISING = 752
    CLOCK_FALLING = 753

    # for OLDRV_SETDATAFLOW 
    DF_CONTINUOUS = 800
    DF_SINGLEVALUE = 801
    DF_DTCONNECT_CONTINUOUS = 802
    DF_DTCONNECT_BURST = 803
    DF_CONTINUOUS_PRETRIG = 804
    DF_CONTINUOUS_ABOUTTRIG = 805

    # for OLDRV_SETCASCADEMODE
    CT_CASCADE = 900
    CT_SINGLE = 901

    # for OLDRV_SETWRAPMODE
    WRP_NONE = 1000
    WRP_MULTIPLE = 1001
    WRP_SINGLE = 1002

    # for OLDRV_GETQUEUESIZES
    QUE_READY = 1100
    QUE_DONE = 1101
    QUE_INPROCESS = 1102

    # NEW to OLDRV_SETTRIGGER             
    TRG_THRESHPOS = 1200
    TRG_THRESHNEG = 1201
    TRG_SYNCBUS = 1202

    # for OLDRV_GETRETTRIGGERMODE
    RETRIGGER_INTERNAL = 1300
    RETRIGGER_SCAN_PER_TRIGGER = 1301
    RETRIGGER_EXTRA = 1302

    INDEX_DISABLED = 1400
    INDEX_LOW = 1401
    INDEX_HIGH = 1402

    def __init__(self, device, type, index):
        self.handle = device.getSubsystem(type, index)
        self.device = device
        self.gains = dict()

    def close(self):
        try:
            self.stop()
        except:
            pass

    @lantz.Action()
    def start(self):
        dacq.lib.olDaStart(self.handle)

    @lantz.Action()
    def stop(self):
        dacq.lib.olDaStop(self.handle)

    @lantz.Feat(values={True: LibDacq.Differential.DIFFERENTIAL,
        False: LibDacq.Differential.SINGLEENDED}, fget=None)
    def differential(self, value):
        dacq.lib.olDaSetChannelType(self.handle, value)

    def ranges(self):
        return self.enumerate_capability(
                Subsystem.EnumerableCapabilities.RANGES)

    @lantz.Feat()
    def range(self):
        low = wintypes.DOUBLE()
        high = wintypes.DOUBLE()
        dacq.lib.olDaGetRange(self.handle, ctypes.byref(high),
                ctypes.byref(low))
        return (high.value, low.value)

    @lantz.Feat()
    def resolution(self):
        ret = wintypes.UINT()
        dacq.lib.olDaGetResolution(self.handle, ctypes.byref(ret))
        return ret.value

    @lantz.Feat(values={True: LibDacq.Encoding.BINARY,
        False: LibDacq.Encoding.TWOSCOMP})
    def offsetbinary_encoding(self):
        ret = wintypes.UINT()
        dacq.lib.olDaGetEncoding(self.handle, ctypes.byref(ret))
        return ret.value

    @lantz.Feat(values={True: DataFlow.CONTINUOUS,
        False: DataFlow.SINGLEVALUE}, fget=None)
    def continuousDataFlow(self, continuous):
        dacq.lib.olDaSetDataFlow(self.handle, continuous)

    @lantz.Feat(units='Hz')
    def maxSampleRate(self):
        return self.get_capability_double(Subsystem.capabilities['MAXTHROUGHPUT'])

    @lantz.Feat(units='Hz')
    def sampleRate(self):
        rate = wintypes.DOUBLE()
        dacq.lib.olDaGetClockFrequency(self.handle, ctypes.byref(rate))
        return rate.value

    @sampleRate.setter
    def sampleRate(self, rate):
        dacq.lib.olDaSetClockFrequency(self.handle, rate)       

    @lantz.Feat(fget=None)
    def dmaChannels(self, channels):
        dacq.lib.olDaSetDmaUsage(self.handle, channels)

    @lantz.Action()
    def configure(self):
        dacq.lib.olDaConfig(self.handle)

    def list_capabilities(self):
        ret = []
        result = wintypes.UINT(0)
        for name, code in Subsystem.capabilities.items():
            if not name.startswith('SUP'):
                continue
            dacq.lib.olDaGetSSCaps(self.handle, code, ctypes.byref(result))
            if result != 0:
                ret.append((name, code))
        return ret

    class EnumerableCapabilities(object):
        FILTERS = 100
        RANGES = 101
        GAINS = 102
        RESOLUTIONS = 103
        EXCITATION_CURRENT_VALUES = 104
        THRESHOLD_START_TRIGGER_CHANNELS = 105
        THRESHOLD_REFERENCE_TRIGGER_CHANNELS = 106

    def enumerate_capability(self, capability):
        ret = []
        twoparams = capability == Subsystem.EnumerableCapabilities.RANGES
        def callback(capability, param1, param2, param):
            nonlocal ret
            if twoparams:
                ret.append((param1, param2))
            else:
                ret.append(param1)
            return True
        dacq.lib.olDaEnumSSCaps(self.handle, capability, DtLib.Types.CAPSPROC(callback), 0)
        return ret

    def get_capability_int(self, capability):
        ret = wintypes.UINT()
        dacq.lib.olDaGetSSCaps(self.handle, capability, ctypes.byref(ret))
        return ret.value

    def get_capability_double(self, capability):
        ret = wintypes.DOUBLE()
        dacq.lib.olDaGetSSCapsEx(self.handle, capability, ctypes.byref(ret))
        return ret.value

class ADSubsystem(Subsystem):
    def __init__(self, device, index):
        super().__init__(device, Subsystem.Types.AD, index)
        self.buffers = 0
        self.futures = queue.Queue()
        self.loop = asyncio.get_event_loop()
        # Prevent garbage collection of callback pointer
        self.cb = DtLib.Types.OLNOTIFYPROC(ADSubsystem.callback)
        dacq.lib.olDaSetNotificationProcedure(self.handle, self.cb,
                int.from_bytes(ctypes.py_object(self), 'little'))

    def close(self):
        super().close()
        #dacq.lib.olDaFlushBuffers(self.handle)
        buf = DtLib.Types.HBUF()
        for ii in range(self.buffers):
            dacq.lib.olDaGetBuffer(self.handle, ctypes.byref(buf))
            mem.lib.olDmFreeBuffer(buf)

    @lantz.Action()
    def configure(self, samples):
        self.samples = samples
        dacq.lib.olDaSetChannelListSize(self.handle, len(samples))
        for ii, (channel, gain) in enumerate(samples):
            dacq.lib.olDaSetChannelListEntry(self.handle, ii, channel)
            dacq.lib.olDaSetGainListEntry(self.handle, ii, gain)
        super().configure()


    @lantz.DictFeat(units='V')
    def readOne(self, channel):
        gain = 1
        reading = ctypes.c_long()
        dacq.lib.olDaGetSingleValue(self.handle, ctypes.byref(reading), channel,
                gain)
        return self.codeToVoltage(reading)[0]


    def prepareBuffers(self, number, size):
        for ii in range(number):
            buf = DtLib.Types.HBUF()
            mem.lib.olDmCallocBuffer(0, 0, size, 2, ctypes.byref(buf))
            dacq.lib.olDaPutBuffer(self.handle, buf)
        self.buffers += number

    @asyncio.coroutine
    def read_async(self):
        ret = self.read()
        if not ret:
            # Wait for data
            future = asyncio.Future()
            self.futures.put(future)
            ret = yield from future
        return ret

    def read_blocking(self):
        return self.loop.run_until_complete(self.read_async())

    @staticmethod
    def callback(message, subsystem, param):
        self = ctypes.cast(ctypes.c_void_p(param), ctypes.py_object).value
        if message == Subsystem.Messages.BUFFER_DONE:
            try:
                future = self.futures.get(False)
            except queue.Empty:
                return
            self.loop.call_soon_threadsafe(functools.partial(
                future.set_result, self.read()))

    def read(self):
        buf = DtLib.Types.HBUF()
        dacq.lib.olDaGetBuffer(self.handle, ctypes.byref(buf))
        if buf.value is None:
            return dict()
        numsamples = wintypes.DWORD()
        mem.lib.olDmGetMaxSamples(buf, ctypes.byref(numsamples))
        data = wintypes.LPWORD()
        mem.lib.olDmGetBufferPtr(buf, ctypes.cast(ctypes.byref(data),
            ctypes.POINTER(ctypes.c_voidp)))
        raw = np.ctypeslib.as_array(data, (numsamples.value, ))
        voltages = self.codeToVoltage(raw)
        channels = {channel: voltages[ii::len(self.samples)]*gain
                for ii, (channel, gain) in enumerate(self.samples)}
        dacq.lib.olDaPutBuffer(self.handle, buf)
        channels['time'] = np.arange(numsamples.value / len(self.samples)) * \
                len(self.samples) / self.sampleRate.to('Hz').magnitude
        return channels

    def codeToVoltage(self, code):
        if isinstance(code, int):
            code = np.array([code])
        else:
            code = np.array(code)
        high, low = self.range
        resolution = self.resolution
        if not self.offsetbinary_encoding:
            ret = code.astype(np.uint) + 1 << (resolution - 1)
        else:
            ret = code.copy()
        ret = low + (high - low) / (1 << resolution) * ret
        return ret

class WriteableSubsystem(Subsystem):
    @lantz.Action()
    def write(self, channel, code, gain):
        dacq.lib.olDaPutSingleValue(self.handle, code, channel, gain)

class DASubsystem(WriteableSubsystem):
    def __init__(self, device, index):
        super().__init__(device, Subsystem.Types.DA, index)

    @lantz.Action()
    def writeVoltage(self, channel, voltage, gain):
        self.write(channel, self.voltageToCode(voltage), gain)

    def voltageToCode(self, voltage):
        if isinstance(voltage, float):
            voltage = np.array([voltage])
        high, low = self.range
        resolution = self.resolution
        if any(voltage < low) or any(voltage >= high):
            raise Exception('Voltage out of range', low, high)
        code = ((voltage - low) / (high - low) * (1 << resolution)).astype(
                np.uint)
        if self.offsetbinary_encoding:
            return (code ^ (1 << (resolution - 1))) & ((1 << resolution) - 1)
        else:
            return code
        ret = low + (high - low) / (1 << resolution) * ret
        return ret

class DOutSubsystem(WriteableSubsystem):
    def __init__(self, device, index):
        super().__init__(device, Subsystem.Types.DOUT, index)

class CounterTimerSubsystem(Subsystem):
    class Modes(object):
        COUNT = 700
        RATE = 701
        ONESHOT = 702
        ONESHOT_RPT = 703
        UP_DOWN = 704
        MEASURE = 705
        CONT_MEASURE = 706
    def __init__(self, device, index):
        super().__init__(device, Subsystem.Types.CT, index)

    @lantz.Feat(values={k:v for k,v in Modes.__dict__.items() if k[0] != '_'})
    def mode(self):
        ret = wintypes.UINT()
        dacq.lib.olDaGetCTMode(self.handle, ctypes.byref(ret))
        return ret.value

    @mode.setter
    def mode(self, value):
        dacq.lib.olDaSetCTMode(self.handle, value)

    @lantz.Feat(units='Hz')
    def clockFrequency(self):
        ret = wintypes.DOUBLE()
        dacq.lib.olDaGetClockFrequency(self.handle, ctypes.byref(ret))
        return ret.value

    @clockFrequency.setter
    def clockFrequency(self, value):
        dacq.lib.olDaSetClockFrequency(self.handle, value)

    @lantz.Feat()
    def pulseWidth(self):
        ret = wintypes.DOUBLE()
        dacq.lib.olDaGetPulseWidth(self.handle, ctypes.byref(ret))
        return ret.value

    @pulseWidth.setter
    def pulseWidth(self, value):
        dacq.lib.olDaSetPulseWidth(self.handle, value)
