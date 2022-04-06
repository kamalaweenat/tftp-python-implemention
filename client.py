#!/usr/bin/env python3
import socket
import os
import argparse
from tftp import TFTP

class Client(TFTP):

    def __init__(self, ip, port, request_mod, filename, targetname, timeout, blksize, buffer_size, transfer_mode, is_logging):
        super().__init__(blksize, transfer_mode)
        self.__ip = ip
        self.__port = port # TFTP Protocol Port (69)
        self.__request_mod = request_mod
        self.__filename = filename
        self.__targetname = targetname
        self.__timeout = timeout # timeout to waiting for the client
        self.__buffer_size = buffer_size
        self.__is_logging = is_logging # verbose messages  


    def handle_request(self):

        try:  

            # Creating udp socket
            sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            sock.settimeout(self.__timeout)  # Setting socket to timeout
            addr = (self.__ip, self.__port)

            if self.__request_mod == "get":
                request = self.pack_rq_header(TFTP.RRQ_OPCODE, self.__filename, self.TransferMode)
            else: # put request
                request = self.pack_rq_header(TFTP.WRQ_OPCODE, self.__filename, self.TransferMode)

            sock.sendto(request, addr)  # Sending TFTP RRQ packet to server

            last_packet = None
            while True:

                packet_req, addr = sock.recvfrom(self.__buffer_size)
                opcode = TFTP.get_opcode(packet_req)

                if opcode == TFTP.ERR_OPCODE: # an error occured 
                    # parse error message
                    opcode, error_code, error_msg = self.unpack_error(packet_req)
                    print(f"[Server Reply]: Error Message: {error_msg}, ERROR_CODE: ({error_code})")            
                    break

                elif opcode == TFTP.DAT_OPCODE: # this is client read (get) request, after sending RRQ                
                    last_packet = self.get_dat_send_ack(packet_req, self.__targetname, sock, addr)  
                    if last_packet is None:
                        break

                elif opcode == TFTP.ACK_OPCODE: # this is client write (put) request (WRQ request)
                    last_packet = self.get_ack_send_dat(last_packet, packet_req, self.__filename, sock, addr, self.TransferMode)
                    if last_packet is None:
                        break

            
            #self.check_get_put(result)

            if not sock is None:
                sock.close()  

        except Exception as e:
            print("Error: ", e)
            if not sock is None:
                sock.close()    



def main():
    # Configuring arguments parser
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', dest='port', type=int,  default=69, help='server port')
    parser.add_argument('-t', "--timeout", dest='timeout', type=int, default=3, help="timeout to close the connection")
    parser.add_argument('-c', '--cwd', dest='cwd', type=str, default='', help='Change the current directory in which the files (with relative paths) are read or written')
    parser.add_argument('-b', '--blksize', dest='blksize', type=int, default=512, help='indicates the size in bytes of the data block used to transfer files (default, 512).')

    subparsers = parser.add_subparsers(dest='cmd')
    subparsers.add_parser('get', help="get file from server")
    subparsers.add_parser('put', help="put file on server")

    parser.add_argument('host', type=str, default='127.0.0.1', help='Hostname')
    parser.add_argument('filename', type=str, default='', help='Filename')
    parser.add_argument('-n', '--targetname' , type=str, default='', help="Targetname")


    args = parser.parse_args()

    # change target filename
    if args.targetname == '': 
        args.targetname = args.filename

    # change current working directory
    if args.cwd != '': 
        os.chdir(args.cwd)

    # get request
    if args.cmd == 'get':   
        client = Client(args.host, args.port, "get", args.filename, args.targetname, args.timeout, 
                            args.blksize, 1024, TFTP.TRANSFER_MODES[1], True)
    # put request
    if args.cmd == 'put':
        #  check if file exists:
        if not os.path.isfile(args.filename):
            print(f"ERRORL you entered file does not exist in system folders")
            return

        client = Client(args.host, args.port, "put", args.filename, args.targetname, args.timeout, 
                            args.blksize, 1024, TFTP.TRANSFER_MODES[1], True)

    # os.chdir("/home/kamal/NetworkingProj/client_test")
    # client = Client("127.0.0.1", 6969, "put", "nature", "nature11", 3, 512, 1024, "octet", True)
    client.handle_request()     

if __name__ == "__main__"            :
    main()