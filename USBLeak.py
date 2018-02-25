#-*- coding: euc-kr -*-
import _winreg
import USB
import os
import xml.etree.ElementTree as ET
import tempfile
import getpass
import csv
import lnk
import datetime
import shellbags
import evtx_dump

def main():
    serial = getSerial()

    
    getVolume(serial)

    
    drive = getDrive(serial)
    
    
    getInstallTime(serial)
    event = getEvent(serial)
    createShellbagFile(drive)
    getLnk(drive)

    createConnectCSV(serial, event)
    Merge()
    
def Merge():
    file_usb = open("usb.csv", "r")
    file_merge=open("merge_result.csv", "wb")

    rdr_usb = csv.reader(file_usb)
    wr_merge = csv.writer(file_merge, delimiter=',')

    for line_usb in rdr_usb:
        time_conn = line_usb[4]
        time_disconn = line_usb[5]
        name_drive = line_usb[1]
        
        file_shellbag = open("shellbag.csv", "r")
        rdr_sh = csv.reader(file_shellbag)

        for line_sh in rdr_sh:
            time_sh = line_sh[0]
            path_sh = line_sh[1]
            
            if time_conn <= time_sh and time_sh <= time_disconn and name_drive in path_sh:
                wr_merge.writerow([name_drive, path_sh, time_conn, time_disconn, time_sh])
        file_lnk = open("lnk.csv", "r")
        rdr_lnk = csv.reader(file_lnk)
        for line_lnk in rdr_lnk:
            time_lnk = line_lnk[3]
            path_lnk = line_lnk[0]
            fname_lnk = line_lnk[2]
            if time_conn <= time_lnk and time_lnk <= time_disconn and name_drive in path_lnk:
                wr_merge.writerow([name_drive, fname_lnk, time_conn, time_disconn, time_lnk])
     
    file_usb.close()
    file_shellbag.close()
    file_merge.close()


def getLnk(drive):
    path_rec = os.getenv("USERPROFILE") + "\\AppData\\Roaming\\Microsoft\\Windows\\Recent"

    fname = []
    pwd = path_rec

    for (path, dirs, files) in os.walk(pwd):
        for file in files:
            if os.path.splitext(file)[1].lower() == ".lnk":
                analy_file = path + "\\"+file
                fname.append(analy_file)



    with open('lnk.csv', 'wb') as csvfile:
        wr = csv.writer(csvfile, delimiter=',')
        for filepath in fname:
            fullpath = lnk.analy_lnk(filepath)
            drive_name = fullpath.split('\\')[0]
            filename = fullpath.split('\\')[-1]
            
            mtime = datetime.datetime.fromtimestamp(int(os.path.getmtime(filepath)))
            for dr in drive:
                if dr in drive_name:
                    wr.writerow([drive_name, filename, fullpath, mtime])
def init(info):
    info.serial = ""
    info.name_drive = ""
    info.name_volume = ""
    info.time_install = ""
    info.name = ""
    info.path = ""

def getSerial():
    HKLM_reg = _winreg.ConnectRegistry(None, _winreg.HKEY_LOCAL_MACHINE)
    path_USBSTOR = "SYSTEM\\ControlSet001\\Enum\\USBSTOR"
    key = _winreg.OpenKey(HKLM_reg, path_USBSTOR)
    i = 0
    dic_serial = {}
    while True:
        try:
            val_key = _winreg.EnumKey(key, i)
            path_Temp = path_USBSTOR + "\\" + val_key

            serial_key_handle = _winreg.OpenKey(HKLM_reg, path_Temp)
            serial_key = _winreg.EnumKey(serial_key_handle, 0)
            info_USB = USB.USBSTOR()
            init(info_USB)
            info_USB.serial = serial_key
            info_USB.name = val_key
            
            info_USB.path = "USBSTOR\\"+val_key+"\\"+serial_key
            dic_serial[serial_key] = info_USB
            i = i + 1
        except:
            break

    return dic_serial
def getVolume(dic_serial):
    HKLM_reg = _winreg.ConnectRegistry(None, _winreg.HKEY_LOCAL_MACHINE)
    path_Volume = "SOFTWARE\\Microsoft\\Windows Portable Devices\\Devices"
    key = _winreg.OpenKey(HKLM_reg, path_Volume)

    for serial in dic_serial.keys():
        i = 0
        while True:
            try:
                val_key = _winreg.EnumKey(key, i)
                if serial in val_key:
                    volumekey_path = path_Volume + "\\" + val_key
                    volumekey = _winreg.OpenKey(HKLM_reg, volumekey_path)
                    dic_serial[serial].name_volume = _winreg.EnumValue(volumekey, 0)[1]
                    break
                i = i + 1
            except:
                break

def getInstallTime(dic_serial):
    log_setupAPI = "C:\\Windows\\inf\\setupapi.dev.log"
    setup = open(log_setupAPI, "r")
    while True:
        line = setup.readline()
        if not line :
            break

        for key in dic_serial.keys():
            target_string = ">>>  [Device Install (Hardware initiated) - " + dic_serial[key].path

            if target_string in line:
                line_time = setup.readline()
                dic_serial[key].time_install = (line_time.split('start ')[1])[:-1]

    setup.close()
def getDrive(dic_serial):
    list_drive = []
    HKLM_reg = _winreg.ConnectRegistry(None, _winreg.HKEY_LOCAL_MACHINE)
    path_drive = "SYSTEM\\MountedDevices"
    key = _winreg.OpenKey(HKLM_reg, path_drive)
    i = 0
    for serial in dic_serial.keys():
        i = 1
        while True:
            try:
                val_keys = _winreg.EnumValue(key, i) 
                drivename = val_keys[0]
                
                if "DosDevices" in drivename:
                    val_key = val_keys[1]
                    if dic_serial[serial].name.encode("utf-16")[2:] in val_key:
                        
                        dic_serial[serial].name_drive = drivename.split('\\')[-1]
                        list_drive.append(drivename.split('\\')[-1])
                        break
                i =i + 1
            except:
                break
    return list_drive
def getEvent(dic_serial):
    path_evtx = "C:\\Windows\\System32\\winevt\\Logs\\Microsoft-Windows-DriverFrameworks-UserMode%4Operational.evtx"
    name_xml = createEvtxToXml(path_evtx)
    
    namespace = "http://schemas.microsoft.com/win/2004/08/events/event"
    namespace_prefix = "{" + namespace + "}"
    dev_namespace = "http://www.microsoft.com/DriverFrameworks/UserMode/Event"
    dev_namespace_prefix = "{" + dev_namespace + "}"

    ET.register_namespace('', namespace)
    tree = ET.parse(name_xml)
    evtx = tree.getroot()

    if evtx == None:
        return 0


    dic_pair = {}
    for evt in evtx.iter(namespace_prefix+"Event"):
        for evid in evt.iter(namespace_prefix+"EventID"):
            if evid.text == "2003":
                for time in evt.iter(namespace_prefix+"TimeCreated"):
                    evt_time_connect = time.attrib['SystemTime']
                    time_pair = USB.ConnectPair()
                    strtime = datetime.datetime.strptime(evt_time_connect.split('.')[0], "%Y-%m-%d %H:%M:%S")
                    time_gap = datetime.timedelta(hours=9)
                    strtime = strtime + time_gap
                    time_pair.time_conn = strtime
                    

                for val in evt.iter(dev_namespace_prefix+"UMDFHostDeviceArrivalBegin"):
                    evt_lifetime_prev = val.attrib['lifetime']
                    dic_pair[evt_lifetime_prev] = time_pair
                
                

            if evid.text == "2100":
                
                for val in evt.iter(dev_namespace_prefix+"UMDFHostDeviceRequest"):
                    evt_lifetime = val.attrib['lifetime']
                    if evt_lifetime in dic_pair.keys():
                        try:
                            dic_pair[evt_lifetime].serial = val.attrib['instance'].split('#')[-2]

                            for time in evt.iter(namespace_prefix+"TimeCreated"):
                                strtime = datetime.datetime.strptime(time.attrib['SystemTime'].split('.')[0], "%Y-%m-%d %H:%M:%S")
                                time_gap = datetime.timedelta(hours=9)
                                dic_pair[evt_lifetime].time_disconn = strtime + time_gap
                        except:
                            continue     
   
    return dic_pair

def createConnectCSV(serial, event):

    with open('usb.csv', 'wb') as csvfile:
        wr = csv.writer(csvfile, delimiter=',')
        for i in serial:
            for time in event:
                if event[time].serial == i:
                    wr.writerow([serial[i].serial, serial[i].name_drive, serial[i].name_volume, serial[i].time_install, event[time].time_conn, event[time].time_disconn])

def saveHiveFile():
    tempdir = tempfile.gettempdir()
    tempdir = tempdir + "\\savehive"

    comm = "RegEx.exe -h " + tempdir
    os.system(comm)

    return tempdir

def createShellbagFile(drive):
    path_hive = saveHiveFile()
    username = getpass.getuser()
    name_ntuser = username+".NTUSER.DAT"
    name_usrclass = username+".USRCLASS.DAT"

    shellbags.shellbag_main(path_hive + "\\"+name_ntuser, "csv", "temp_shellbag.csv")
    shellbags.shellbag_main(path_hive + "\\"+name_usrclass, "csv", "temp_shellbag.csv")


    extractshellbagFile(drive)
    
def extractshellbagFile(drive):
    temp_f = open('temp_shellbag.csv', 'r')
    f = open('shellbag.csv', 'wb')
    rdr = csv.reader(temp_f)
    wr = csv.writer(f)
    for line in rdr:
        if len(line) == 0:
            continue
        
        for dr in drive:
            if dr+"\\" in line[1]:
                wr.writerow([line[0], line[1]])
        
    f.close()
    temp_f.close() 

def createEvtxToXml(path):
    name_xml = os.getcwd()+"\\DriveFrameworks-UserMode.xml"
    comm = "del "+name_xml
    os.system(comm)

    evtx_dump.evtx_main(path, name_xml)
    
    return name_xml

if __name__ == "__main__":
    main()