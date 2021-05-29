 # 
 # Copyright (c) 2021 Scott Lamb.
 # 
 # This program is free software: you can redistribute it and/or modify  
 # it under the terms of the GNU General Public License as published by  
 # the Free Software Foundation, version 3.
 #
 # This program is distributed in the hope that it will be useful, but 
 # WITHOUT ANY WARRANTY; without even the implied warranty of 
 # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
 # General Public License for more details.
 #
 # You should have received a copy of the GNU General Public License 
 # along with this program. If not, see <http://www.gnu.org/licenses/>.
 #
 
import fcntl
import ioctl_opt
import ctypes
import struct
import os
import time

class kbdPickerErrorUnPlugged(Exception):
    pass

class kbdPicker:
    scanCodeToAnsi = {
        0x1e: 'a',
        0x30: 'b',
        0x2e: 'c',
        0x20: 'd',
        0x12: 'e',
        0x21: 'f',
        0x22: 'g',
        0x23: 'h',
        0x17: 'i',
        0x24: 'j',
        0x25: 'k',
        0x26: 'l',
        0x32: 'm',
        0x31: 'n',
        0x18: 'o',
        0x19: 'p',
        0x10: 'q',
        0x13: 'r',
        0x1f: 's',
        0x14: 't',
        0x16: 'u',
        0x2f: 'v',
        0x11: 'w',
        0x2d: 'x',
        0x15: 'y',
        0x2c: 'z',
        0xb: '0',
        0x2: '1',
        0x3: '2',
        0x4: '3',
        0x5: '4',
        0x6: '5',
        0x7: '6',
        0x8: '7',
        0x9: '8',
        0xa: '9',
        0xc: '-',
        0xd: '=',
        0x1a: '[',
        0x1b: ']',
        0x1c: '\n',
        0x39: ' ',
    }

    scanCodeToAnsiShifted = {
        0x1e: 'A',
        0x30: 'B',
        0x2e: 'C',
        0x20: 'D',
        0x12: 'E',
        0x21: 'F',
        0x22: 'G',
        0x23: 'H',
        0x17: 'I',
        0x24: 'J',
        0x25: 'K',
        0x26: 'L',
        0x32: 'M',
        0x31: 'N',
        0x18: 'O',
        0x19: 'P',
        0x10: 'Q',
        0x13: 'R',
        0x1f: 'S',
        0x14: 'T',
        0x16: 'U',
        0x2f: 'V',
        0x11: 'W',
        0x2d: 'X',
        0x15: 'Y',
        0x2c: 'Z',
        0xb: ')',
        0x2: '!',
        0x3: '@',
        0x4: '#',
        0x5: '$',
        0x6: '%',
        0x7: '^',
        0x8: '&',
        0x9: '*',
        0xa: '(',
        0xc: '_',
        0xd: '+',
        0x1a: '{',
        0x1b: '}',
        0x1c: '\n',
        0x39: ' ',
    }

    scanCodeShiftKeys = [
        0x2a, #left shift
        0x36  #right shift
    ]

    EVIOCGNAME = lambda self,len: ioctl_opt.IOC(ioctl_opt.IOC_READ, ord('E'), 0x06, len)
    EVIOCGRAB = lambda self,len: ioctl_opt.IOW(ord('E'), 0x90, ctypes.c_int)

    # also from input.h
    event_format = "llHHI"
    event_size = struct.calcsize(event_format)
    # from input-event-codes.h
    # type can be EV_SYN, EV_KEY or EV_MSC
    EV_KEY = 1
    KEY_DOWN = 1
    KEY_UP = 0

    fd = None
    device = None
    shifted = False

    def __init__(self, device:str=None):
        if device:
            self.setDeviceByPath(device)

    def __del__(self):
        if self.fd:
            self._grab(False)
            self.fd.close()
            self.fd = None

    def _grab(self, grab:bool):
        fcntl.ioctl(self.fd, self.EVIOCGRAB(1), grab)

    def getAllKdbDevices(self):
        list = []
        dev = {}
        with open('/proc/bus/input/devices', 'r') as devFd:
            for lineFull in devFd.readlines():
                if lineFull == '\n': #end of section
                    if 'kbd' in dev:
                        list.append(dev)
                    dev = {}
                else:
                    line = lineFull.split()
                    if line[0] == 'I:':
                        for id in line[1:]:
                            if 'Vendor' in id:
                                dev['vendor'] = id.split('=')[1]
                            if 'Product' in id:
                                dev['product'] = id.split('=')[1]
                    elif line[0] == 'N:':
                        dev['name'] = lineFull.split('"')[1]
                    elif line[0] == 'H:':
                        if 'kbd' in line[1:]:
                            dev['kbd'] = True
                        for handler in line[1:]:
                            if 'event' in handler:
                                if '=' in handler:
                                    handler = handler.split('=')[1]
                                dev['path'] = f'/dev/input/{handler}'
                    elif line[0] == 'P:':
                        dev['physicalPort'] = lineFull[lineFull.find('.usb-')+len('.usb-'):].split('/')[0]
            return list

    def setDeviceByPhysicalUsbPort(self, port:str):
        keyboards = self.getAllKdbDevices()
        for kbd in keyboards:
            if port == kbd['physicalPort']:
                path = kbd['path']
                self.setDeviceByPath(path)
                return True
        return False

    def setDeviceByName(self, name:str):
        keyboards = self.getAllKdbDevices()
        for kbd in keyboards:
            if name == kbd['name']:
                path = kbd['path']
                self.setDeviceByPath(path)
                return True
        return False

    def setDeviceByPath(self, device:str):
        if self.fd:
            close(self.fd)
            self.fd = None 
        if not os.path.exists(device):
            print(f"{device}: is not a file")
            return False
        self.device = device
        self.fd = open(self.device, 'rb')
        self.shifted = False # Whenever we open a device always assume the shift key is not being held down (this is a possable bug).
        self._grab(True) # Take controll of the device
        return True

    def waitForDeviceByName(self, name:str):
        while True:
            keyboards = self.getAllKdbDevices()
            time.sleep(1) #always do some sleeping after we take a snapshot to ensure the devices have time to enumerate
            for kbd in keyboards:
                if name == kbd['name']:
                    return

    def waitForDeviceByPhysicalUsbPort(self, port:str):
        while True:
            keyboards = self.getAllKdbDevices()
            time.sleep(1) #always do some sleeping after we take a snapshot to ensure the devices have time to enumerate
            for kbd in keyboards:
                if port == kbd['physicalPort']:
                    return

    #return the device's name or None if no device is found
    def getDeviceName(self, device:str = None):
        if device:
            dev = device
        elif self.device:
            dev = self.device
        else:
            return None
        with open(dev, 'rb') as fd:
            name = ctypes.create_string_buffer(256)
            fcntl.ioctl(fd, self.EVIOCGNAME(256), name, True)
            return name.value.decode('UTF-8')

    def getchar(self):
        if not self.fd:
            #no device is open
            raise IOError(f"No device open: call setDevice('filenameOfDevice') first.")
        while True:
            try:
                rawEvent = self.fd.read(self.event_size)
            except OSError as e:
                #print(f"except: {e}")
                self.fd = None
                raise kbdPickerErrorUnPlugged()
            _, _, e_type, e_code, e_val = struct.unpack(self.event_format, rawEvent)
            if e_type == self.EV_KEY and e_val == self.KEY_UP and e_code in self.scanCodeShiftKeys:
                self.shifted = False #let go of the shift key
            elif e_type == self.EV_KEY and e_val == self.KEY_DOWN: #only care about key down events
                if e_code in self.scanCodeShiftKeys:
                    self.shifted = True #holding down the shift key
                else:
                    if e_code in self.scanCodeToAnsi:
                        if self.shifted:
                            if e_code in self.scanCodeToAnsiShifted:
                                return self.scanCodeToAnsiShifted[e_code]
                            else:
                                pass # ignore unknown shifted codes
                        elif e_code in self.scanCodeToAnsi:
                            return self.scanCodeToAnsi[e_code]
                        else:
                            pass # ignore unknown codes

    def readline(self):
        while True:
            ch = self._getchar()
            if ch == '\n':
                print(f"{readLine}")
                line = self.readLine
                self.readLine = ''
                return line
            else:
                self.readLine += ch

if __name__ == "__main__":
    #tests
    print(f"************Running self tests************")
    assert kbdPicker().getDeviceName() == None
    keyboards = kbdPicker().getAllKdbDevices()
    print(f"{keyboards}")
    assert kbdPicker().setDeviceByPath('nope') == False
    assert kbdPicker().setDeviceByName('nope') == False
    assert kbdPicker().setDeviceByPhysicalUsbPort('nope') == False

    assert kbdPicker().setDeviceByPath(keyboards[0]['path']) == True
    assert kbdPicker().setDeviceByName(keyboards[0]['name']) == True
    kbd = kbdPicker()
    assert kbd.setDeviceByPhysicalUsbPort(keyboards[0]['physicalPort']) == True
    assert kbd.getDeviceName() == keyboards[0]['name']
    print(f"************All tests pass************")

    kbd = kbdPicker()
#    deviceName = 'WCM WCM Keyboard'
    usbPort = '1.4.3'
    while True:
        try:
            kbd.waitForDeviceByPhysicalUsbPort(usbPort)
            assert kbd.setDeviceByPhysicalUsbPort(usbPort) == True
            deviceConnected = True
            deviceName = kbd.getDeviceName()
            print(f"{deviceName}: Plugged in")
            while deviceConnected:
                ch = kbd.getchar()
                print(f"{ch}", end='')
        except kbdPickerErrorUnPlugged:
            print(f"{deviceName}: Unplugged")
            deviceConnected = False
        except KeyboardInterrupt:
            print(f"Cya")
            exit()

