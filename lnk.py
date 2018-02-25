#!/usr/bin/python

# This is a quick and dirty port of lnk-parse-1.0.pl found here:
#   https://code.google.com/p/revealertoolkit/source/browse/trunk/tools/lnk-parse-1.0.pl
#   Windows LNK file parser - Jacob Cunningham - jakec76@users.sourceforge.net
#   Based on the contents of the document:
#   http://www.i2s-lab.com/Papers/The_Windows_Shortcut_File_Format.pdf
#   v1.0
#
#  Edits by YK
#   - Added support for blank/invalid timestamps
#   - Bug fixes for attribute parsing & unicode strings

import sys, struct, datetime, binascii


# HASH of flag attributes
flag_hash = [["",""] for _ in range(7)]
flag_hash[0][1] = "HAS SHELLIDLIST"
flag_hash[0][0] = "NO SHELLIDLIST"
flag_hash[1][1] = "POINTS TO FILE/DIR"
flag_hash[1][0] = "NOT POINT TO FILE/DIR"
flag_hash[2][1] = "HAS DESCRIPTION"
flag_hash[2][0] = "NO DESCRIPTION"
flag_hash[3][1] = "HAS RELATIVE PATH STRING"
flag_hash[3][0] = "NO RELATIVE PATH STRING"
flag_hash[4][1] = "HAS WORKING DIRECTORY"
flag_hash[4][0] = "NO WORKING DIRECTORY"
flag_hash[5][1] = "HAS CMD LINE ARGS"
flag_hash[5][0] = "NO CMD LINE ARGS"
flag_hash[6][1] = "HAS CUSTOM ICON"
flag_hash[6][0] = "NO CUSTOM ICON"

# HASH of FileAttributes
file_hash = [["",""] for _ in range(15)]
file_hash[0][1] = "READ ONLY"
file_hash[1][1] = "HIDDEN"
file_hash[2][1] = "SYSTEM FILE"
file_hash[3][1] = "VOLUME LABEL (not possible)"
file_hash[4][1] = "DIRECTORY"
file_hash[5][1] = "ARCHIVE"
file_hash[6][1] = "NTFS EFS"
file_hash[7][1] = "NORMAL"
file_hash[8][1] = "TEMP"
file_hash[9][1] = "SPARSE"
file_hash[10][1] = "REPARSE POINT DATA"
file_hash[11][1] = "COMPRESSED"
file_hash[12][1] = "OFFLINE"
file_hash[13][1] = "NOT_CONTENT_INDEXED"
file_hash[14][1] = "ENCRYPTED"

#Hash of ShowWnd values
show_wnd_hash = [[""] for _ in range(11)]
show_wnd_hash[0] = "SW_HIDE"
show_wnd_hash[1] = "SW_NORMAL"
show_wnd_hash[2] = "SW_SHOWMINIMIZED"
show_wnd_hash[3] = "SW_SHOWMAXIMIZED"
show_wnd_hash[4] = "SW_SHOWNOACTIVE"
show_wnd_hash[5] = "SW_SHOW"
show_wnd_hash[6] = "SW_MINIMIZE"
show_wnd_hash[7] = "SW_SHOWMINNOACTIVE"
show_wnd_hash[8] = "SW_SHOWNA"
show_wnd_hash[9] = "SW_RESTORE"
show_wnd_hash[10] = "SW_SHOWDEFAULT"

# Hash for Volume types
vol_type_hash = [[""] for _ in range(7)]
vol_type_hash[0] = "Unknown"
vol_type_hash[1] = "No root directory"
vol_type_hash[2] = "Removable (Floppy,Zip,USB,etc.)"
vol_type_hash[3] = "Fixed (Hard Disk)"
vol_type_hash[4] = "Remote (Network Drive)"
vol_type_hash[5] = "CD-ROM"
vol_type_hash[6] = "RAM Drive"


def reverse_hex(HEXDATE):
    hexVals = [HEXDATE[i:i + 2] for i in range(0, 16, 2)]
    reversedHexVals = hexVals[::-1]
    return ''.join(reversedHexVals)


def assert_lnk_signature(f):
    f.seek(0)
    sig = f.read(4)
    guid = f.read(16)
    if sig != 'L\x00\x00\x00':
        raise Exception("This is not a .lnk file.")
    if guid != '\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00F':
        raise Exception("Cannot read this kind of .lnk file.")


# read COUNT bytes at LOC and unpack into binary
def read_unpack_bin(f, loc, count):
    
    # jump to the specified location
    f.seek(loc)

    raw = f.read(count)
    result = ""

    for b in raw:
        result += ("{0:08b}".format(ord(b)))[::-1]

    return result


# read COUNT bytes at LOC and unpack into ascii
def read_unpack_ascii(f,loc,count):

    # jump to the specified location
    f.seek(loc)

    # should interpret as ascii automagically
    return f.read(count)


# read COUNT bytes at LOC
def read_unpack(f, loc, count):
    
    # jump to the specified location
    f.seek(loc)

    raw = f.read(count)
    result = ""

    for b in raw:
        result += binascii.hexlify(b)

    return result


# Read a null terminated string from the specified location.
def read_null_term(f, loc):
    
    # jump to the start position
    f.seek(loc)

    result = ""
    b = f.read(1)

    while b != "\x00":
        result += str(b)
        b = f.read(1)

    return result


# adapted from pylink.py
def ms_time_to_unix_str(windows_time):
    time_str = ''
    try:
        unix_time = windows_time / 10000000.0 - 11644473600
        time_str = str(datetime.datetime.fromtimestamp(unix_time))
    except:
        pass
    return time_str


def add_info(f,loc):

    tmp_len_hex = reverse_hex(read_unpack(f,loc,2))
    tmp_len = 2 * int(tmp_len_hex, 16)

    loc += 2

    if (tmp_len != 0):
        tmp_string = read_unpack_ascii(f, loc, tmp_len)
        now_loc = f.tell()
        return (tmp_string, now_loc)
    else:
        now_loc = f.tell()
        return (None, now_loc)


def parse_lnk(filename):

    #read the file in binary module
    f = open(filename, 'rb')

    try:
        assert_lnk_signature(f)
    except Exception as e:
        return "[!] Exception: "+str(e)

    output = "Lnk File: " + filename + "\n"

    # get the flag bits
    flags = read_unpack_bin(f,20,1)
    flag_desc = list()

    # flags are only the first 7 bits
    for cnt in range(len(flags)-1):
        bit = int(flags[cnt])
        # grab the description for this bit
        flag_desc.append(flag_hash[cnt][bit])

    output += "Link Flags: " + " | ".join(flag_desc) + "\n"

    # File Attributes 4bytes@18h = 24d
    file_attrib = read_unpack_bin(f,24,4)
    attrib_desc = list()
    for cnt in range(0, 14):
        bit = int(file_attrib[cnt])
        # grab the description for this bit
        if bit == 1:
            attrib_desc.append(file_hash[cnt][1])
    if len(attrib_desc) > 0:
        output += "File Attributes: " + " | ".join(attrib_desc) + "\n"

    # Create time 8bytes @ 1ch = 28
    create_time = reverse_hex(read_unpack(f,28,8))
    output += "Create Time:   "+ms_time_to_unix_str(int(create_time, 16)) + "\n"

    # Access time 8 bytes@ 0x24 = 36D
    access_time = reverse_hex(read_unpack(f,36,8))
    output += "Access Time:   "+ms_time_to_unix_str(int(access_time, 16)) + "\n"

    # Modified Time8b @ 0x2C = 44D
    modified_time = reverse_hex(read_unpack(f,44,8))
    output += "Modified Time: "+ms_time_to_unix_str(int(modified_time, 16)) + "\n"

    # Target File length starts @ 34h = 52d
    length_hex = reverse_hex(read_unpack(f,52,4))
    length = int(length_hex, 16)
    output += "Target length: "+str(length) + "\n"

    # Icon File info starts @ 38h = 56d
    icon_index_hex = reverse_hex(read_unpack(f,56,4))
    icon_index = int(icon_index_hex, 16)
    output += "Icon Index: "+str(icon_index) + "\n"

    # show windows starts @3Ch = 60d 
    show_wnd_hex = reverse_hex(read_unpack(f,60,1))
    show_wnd = int(show_wnd_hex, 16)
    output += "ShowWnd: "+str(show_wnd_hash[show_wnd]) + "\n"

    # hot key starts @40h = 64d 
    hotkey_hex = reverse_hex(read_unpack(f,64,4))
    hotkey = int(hotkey_hex, 16)
    output += "HotKey: "+str(hotkey) + "\n"

    #------------------------------------------------------------------------
    # End of Flag parsing
    #------------------------------------------------------------------------

    # get the number of items
    items_hex = reverse_hex(read_unpack(f,76,2))
    items = int(items_hex, 16)

    list_end = 78 + items

    struct_start = list_end
    first_off_off = struct_start + 4
    vol_flags_off = struct_start + 8
    local_vol_off = struct_start + 12
    base_path_off = struct_start + 16
    net_vol_off = struct_start + 20
    rem_path_off = struct_start + 24

    # Structure length
    struct_len_hex = reverse_hex(read_unpack(f,struct_start,4))
    struct_len = int(struct_len_hex, 16)
    struct_end = struct_start + struct_len

    # First offset after struct - Should be 1C under normal circumstances
    first_off = read_unpack(f,first_off_off,1)

    # File location flags
    vol_flags = read_unpack_bin(f,vol_flags_off,1)

    # Local volume table
    # Random garbage if bit0 is clear in volume flags
    if vol_flags[:2] == "10":
        

        base_path_off_hex = reverse_hex(read_unpack(f,base_path_off,4))
        base_path_off = struct_start + int(base_path_off_hex, 16)

        # Read base path data upto NULL term 
        base_path = read_null_term(f,base_path_off)
        basepath = str(base_path)

    # Network Volume Table
    elif vol_flags[:2] == "01":
        basepath = "network volume flags"

    else:
        basepath = "unkonown volume flags"

    f.close()
    return basepath

def analy_lnk(file):
    out = parse_lnk(file)
    return out