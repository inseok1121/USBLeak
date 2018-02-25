from struct import *

p2 = lambda x, y : pack_from('<H', x, y)
up1 = lambda x, y : unpack_from('@c', x, y)[0]
up2 = lambda x, y : unpack_from('<H', x, y)[0]
r_up2 = lambda x, y : unpack_from('>H', x, y)[0]
up4 = lambda x, y : unpack_from('<L', x, y)[0]
r_up4 = lambda x, y : unpack_from('>L', x, y)[0]
uc_up1 = lambda x, y : unpack_from('B', x, y)[0]

size_block = 4096

def main():
    path = "C:\\Users\\sillo\\temp\\SYSTEM"
    target = "SYSTEM\\ControlSet001\\Enum\\USBSTOR".split('\\')[1:]
    f = open(path, "rb")
    offset_rootcell = read_hive_header(f) + size_block - 0x20
    read_hive_bin_header(f, offset_rootcell, target, 0)


def read_hive_header(f):
    f.seek(0)
    hive_header = f.read(0x30)

    if is_reg(up4(hive_header, 0)) == False:
        exit()

    offset_rootcell = up4(hive_header, 0x24)
    
    return offset_rootcell
def read_hive_bin_header(f, offset, target, i):
    f.seek(offset)
    bin_header = f.read(0x20)
    
    if is_bin(up4(bin_header, 0)) == False:
        return 0
    
    size_bin = up4(bin_header, 0x08) - 0x20
    
    read_hive_bin(f, size_bin, target, i, 0)

def read_hive_bin(f, size, target, i, flag):
    if flag == 0:
        bin_body = f.read(size)
        offet_subkeylist = up4(bin_body, 0x20)
        search_subkey(f, offset_subkeylist, target, i)
    elif flag == 1:


def search_subkey(f, offset, target, i):

    

def is_reg(sig):
    if sig == 1718052210:
        return True
    else:
        return False
def is_bin(sig):
    if sig == 1852400232:
        return True
    else:
        return False

if __name__ == "__main__":
    main()