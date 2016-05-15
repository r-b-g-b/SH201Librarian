from mido import Message, open_ioport, get_ioport_names, write_syx_file, read_syx_file
import time
import os
import argparse

class SH201Librarian(object):
    _DUMP = Message('sysex', data=[65, 127, 0, 0, 22, 17, 16, 0, 0, 0, 0, 0, 9, 88, 15])
    def __init__(self, ioport_name=None):
        if ioport_name is None:
            ioport_name = self._gui_select_ioport()
        self.port = open_ioport(ioport_name)
    def _gui_select_ioport(self):
        ioport_names = get_ioport_names()
        for i in range(len(ioport_names)):
            print('%.2i:\t%s' % (i, ioport_names[i]))
        ioport_num = int(input('Enter number of MIDI interface: '))
        try:
            return ioport_names[ioport_num]
        except OSError as errmsg:
            print(errmsg)
            
    def change_program(self, p):
        req = Message('program_change', program=p)
        self.port.send(req)
    
    def download_patch(self, program_number, timeout=3):
        self.change_program(program_number)
        patch = []
        tic = time.time()
        i = 0
        self.port.send(self._DUMP)
        while len(patch)<=10:
            i += 1
            rcv = self.port.receive(block=False)
            toc = time.time()
            if (toc-tic)>timeout: break
            if rcv is None:
                time.sleep(0.1)
                continue
            if rcv.type=='sysex':
                
                patch.append(rcv)
        return patch
    def upload_patch(self, destination, patch):
        if type(patch) is str:
            patch = read_syx_file(patch)
        self.change_program(destination)
        [self.port.send(m) for m in patch]
        
    def backup_all(self, directory, prefix='patch_'):
        for p in range(4*8):            
            write_syx_file(os.path.join(directory, prefix+'%2.2i.syx'%p), self.download_patch(p))
            
if __name__=='__main__':
    parser = argparse.ArgumentParser(description = '''
    Simple librarian for your SH-201
    ''')
    
    parser.add_argument('-n', action='store',
                      dest='ioport_name',
                      help='(optional) name of MIDI port communicating with SH-201')
    parser.add_argument('-d', '--backup_directory', action='store', dest='backup_directory',
                           help='directory to store patches')
    parser.add_argument('-p', '--backup_prefix', action='store', dest='backup_prefix',
                           help='use in conjunction with `-d` to specify a file name prefix')
    args = parser.parse_args()
    print(args.ioport_name)
    sh201 = SH201Librarian(ioport_name=getattr(args, 'ioport_name', None))
    if hasattr(args, 'backup_directory'):
        print('Backing up patches to %s'%args.backup_directory)
        sh201.backup_all(directory=args.backup_directory, prefix=args.backup_prefix)