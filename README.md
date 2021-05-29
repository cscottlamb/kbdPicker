# Keyboard picker
This keyboard picker class gives you a getchar() and getline() interface to a specific hid kdb device. You can specify the keyboard you want to interact with via USB port ID, device name or the device's path. It also let's you know when the device is unplugged and allows to you wait for a specific device to be plugged in.

# Use cases
This class is perfect anytime you have more than one keyboard plugged in and want to interact with them differently. For instance if you want to read from a bar code scanner. Or if you are building an application where two people can interact with one console but each one their own keyboard.

# APIs
## getAllKdbDevices()
This function returns a list of attached keyboards. For each keyboard a dict containing these fields will help you choose the keyboard you wish to interact with:
  * 'vendor': The USB vendor ID.
  * 'product': The USB product ID.
  * 'name': The USB device name.
  * 'physicalPort': The physical USB port the keyboard is plugged into.
  * 'path': The path to the keyboard's event handler.

## setDeviceByPhysicalUsbPort()
Opens a device referenced by the physical USB port it's plugged into. The format looks like "1.2.3". In that example the root hub is "1" and in port "2" is another hub and in that hub, your keyboard is plugged into port "3". So if your keyboard is plugged into port 1 of the root hub your physical USB port would be "1.1".

## setDeviceByName()
Opens a device referenced by the USB name issued by the vendor.

## setDeviceByPath()
Opens the device attached to the event input handler. They can normally be found here /dev/input/.

## waitForDeviceByName()
Waits forever for a device to be plugged in by a given name.

## waitForDeviceByPhysicalUsbPort()
Waits forever for a keyboard device to be plugged into a physical USB port.

## getDeviceName()
Returns a string representing the vendors name for the device. It can then be used with the setDeviceByName() method.

## getchar()
Reads one char from the keyboard. If the USB device is unplugged it will raise a kbdPickerErrorUnPlugged exception.

## readline()
Returns a full line of chars from the keyboard. If the USB device is unplugged it will raise a kbdPickerErrorUnPlugged exception.

