from mido import Message, open_ioport, get_ioport_names, write_syx_file, read_syx_file
import time
import os
import argparse
from itertools import product

program_name_to_number = lambda pname: 'abcd'.index(pname[0].lower())*8 + int(pname[1])-1

class SH201SysExMessage(object):
    _HEADER = (65, 127, 0, 0, 22)
    _MSGTYPECODES = {'get': (17,),
                     'put': (18,)
                    }
    def __init__(self, msg_type):
        self.message = Message('sysex')
        self.msg_type = msg_type
        
    def _compile_message(self):
        if hasattr(self, 'addr') and hasattr(self, 'data'):
            msg = self._HEADER + self._TXRX
            msg += self.addr + self.data
            msg += (self._compute_checksum(),)
            self.message.data = msg
            
    def _compute_checksum(self):
        return 127 - sum(self.addr + self.data)%128

    @property
    def msg_type(self):
        return self.__msg_type
    @msg_type.setter
    def msg_type(self, msg_type):
        self.__msg_type = msg_type
        self._TXRX = self._MSGTYPECODES[msg_type]
        
    @property
    def payload(self):
        return self.message.data
    @payload.setter
    def payload(self, payl):
        '''
        Set the complete message payload
        Input
        ------
        payl: a complete message payload (not including start and stop flags)
        '''
        self.msg_type = [k for k,v in self._MSGTYPECODES.items() if v==(payl[5],)][0]
        self.addr = payl[6:10]
        self.data = payl[10:-2]
        self.message.data = payl
        
    @property
    def data(self):
        return self.__data
    @data.setter
    def data(self, dat):
        self.__data = dat
        self._compile_message()

    @property
    def addr(self):
        return self.__addr
    @addr.setter
    def addr(self, addr):
        self.__addr = addr
        self.__program = addr[1]
        self._compile_message()
        
    @property
    def program(self):
        return self.__program
    @program.setter
    def program(self, p):
        addr = list(self.addr) if hasattr(self, 'addr') else [32,None,0,0]
        addr[1] = p
        self.addr = tuple(addr)

class SH201Librarian(object):
    _REQPATCH = (0, 0, 21, 66)
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
    
    def _generate_download_patch_message(self, program_number):
        req = SH201SysExMessage(msg_type='get')
        req.data = self._REQPATCH
        req.program = program_number
        return req.message
    
    def change_program(self, p):
        req = Message('program_change', program=p)
        self.port.send(req)
    
    def download_patch(self, program_number, n_messages=21, timeout=3):
        '''
        A patch is completely specified by 21 messages
        '''
        if type(program_number) is str:
            program_number = program_name_to_number(program_number)
        patch = []
        tic = time.time()
        i = 0
        req = self._generate_download_patch_message(program_number)
        print(req.hex())
        self.port.send(req)
        while len(patch)<=n_messages:
            i += 1
            rcv = self.port.receive()
            toc = time.time()
            if (toc-tic)>timeout: break
            if rcv is None:
                time.sleep(0.1)
                continue
            # filter sysex messages originating from the desired patch number
            if (rcv.type=='sysex') and (rcv.data[7]==program_number):
                patch.append(rcv)
        return patch
    
    def upload_patch(self, program_number, patch):
        '''
        Overwrites the patch settings
        Input
        --------
        program_number (int) number of the patch you want to overwrite. A1 is 0, D8 is 32
        patch (list of sysex messages)
        '''
        if type(patch) is str:
            patch = read_syx_file(patch)
        if type(program_number) is str:
            program_number = program_name_to_number(program_number)
        for m in patch:
            mess = SH201SysExMessage('put')
            mess.payload = m.data
            mess.program = program_number
            self.port.send(mess.message)
    
    def backup_all(self, directory, prefix='patch_'):
        for i, (bank, prog) in enumerate(product(['A','B','C','D'], range(1,9))):
            program_name = '%s%i' % (bank, prog)
            print(program_name, end=' ', flush=True)
            write_syx_file(os.path.join(directory, '%s%s.syx'%(prefix, program_name)),
                           self.download_patch(i))
            
if __name__=='__main__':
    parser = argparse.ArgumentParser(description = '''
    Simple librarian for your SH-201
    ''')
    
    parser.add_argument('--ioport_name', action='store',
                      dest='ioport_name',
                      help='(optional) name of MIDI port communicating with SH-201')
    parser.add_argument('--backup_directory', action='store', dest='backup_directory',
                           help='directory to store patches')
    parser.add_argument('--backup_prefix', action='store', dest='backup_prefix',
                           help='use in conjunction with `--backup_directory` to specify a file name prefix')
    parser.add_argument('--patch_path', action='store', dest='patch_path',
                        help='upload the patch at this path to your SH-201'
                       )
    parser.add_argument('--program_number', action='store', dest='program_number',
                        help='specifies the bank you want to overwrite with the patch at `--patch_path`'
                       )
    args = parser.parse_args()
    sh201 = SH201Librarian(ioport_name=getattr(args, 'ioport_name', None))
    if not args.backup_directory is None:
        print('Backing up patches to %s'%args.backup_directory)
        sh201.backup_all(directory=args.backup_directory, prefix=args.backup_prefix)
    elif not args.patch_path is None:
        print('Uploading patch at %s to your SH-201 at location %s' % (args.patch_path, args.program_number))
        sh201.upload_patch(args.program_number, args.patch_path)