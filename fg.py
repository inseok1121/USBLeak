import winreg

HKLMReg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
volumeNamePath = "SOFTWARE\\Microsoft\\Windows Portable Devices\\Devices"
key = winreg.OpenKey(HKLMReg, volumeNamePath)
val_key = winreg.EnumKey(key, 0)
print(val_key)