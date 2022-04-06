#!/usr/bin/env python3
import argparse
import os
import socket
from tftp import TFTP
import threading

class Server(TFTP):

    def __init__(self, port=69, buffer_size = 1024, is_logging = True, 
                    timeout = 500, blksize = 512, transfer_mode= TFTP.TRANSFER_MODES[1]):

        super().__init__(blksize, transfer_mode)

        self.__ip = ''
        self.__port = port # TFTP Protocol Port (69)
        self.__buffer_size = buffer_size
        self.__is_logging = is_logging # verbose messages       
        self.__timeout = timeout # timeout to waiting for the client
             
       

    def log(self, msg):
        if self.__is_logging:
            print(msg)


    def create_udp_socket(self, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.__ip, port))
        return sock


    def validate_request(self, packet): 
        """ 
            Validate the client request RRQ/WRQ
            If failed return the code error {0..7}  
            Otherwise (-1 means succeeded)
        """

        opcode = self.get_opcode(packet)   

        if opcode == TFTP.RRQ_OPCODE or opcode == TFTP.WRQ_OPCODE:
            # parse filename and mode from client request  
            opcode, filename, mode = self.unpack_rq_header(packet)
            
            #  Mail is not supported in this implementation
            if mode not in TFTP.TRANSFER_MODES or mode == 'mail':            
                return 0 # 'Not Defined' ERROR

            # Check if '/' is in filename - unwanted path for directories        
            if '/' in filename:           
                return 2 # Access Violation' ERROR         

            if opcode == TFTP.RRQ_OPCODE:                        
                # Check if file doesn't exist, 
                if not os.path.isfile(filename):               
                    return 1 # 'File Not Found' ERROR                

            else: # WRQ request
                # If file is exist in the server send a propriate 
                if os.path.isfile(filename):               
                    return 6 # ERROR ('File Already Exists')

            # Last try is to create the file - maybe other thread is creating it 
            

            return -1

        # Client request is only RRG/WRQ, in any other case of opcode send a propriate error    
        # 'Illegal TFTP operation' ERROR   
        return 4


        
    def handle_client(self, last_packet, client_sock, addr_client, filename, mode):
        """ Handle client request in new thread
            read, write to files"""        
        
        try:            
            
            while True:
                try:                
                    packet_client, addr = client_sock.recvfrom(self.__buffer_size)

                    # Check address (IP, port) matches initial connection address
                    if addr != addr_client:
                        packet_err = self.pack_error(5) # 'Unknown Transfer TID' ERROR 
                        TFTP.send_packet(packet_err, client_sock, addr_client)
                        break

                    opcode = self.get_opcode(packet_client)

                    if opcode == TFTP.ACK_OPCODE:
                        last_packet = self.get_ack_send_dat(last_packet, packet_client, filename, client_sock, addr_client, mode)  
                        if last_packet is None:
                            break   
                        
                    elif opcode == TFTP.DAT_OPCODE:
                        result = self.get_dat_send_ack(packet_client, filename, client_sock, addr_client) 
                        if result is None:
                            break

                    else:
                        # Threads only handle incoming packets with ACK/DATA opcodes, send
                        # 'Illegal TFTP Operation' ERROR packet for any other opcode.
                        packet_err = self.pack_error(4)
                        TFTP.send_packet(packet_err, client_sock, addr_client)
                        break


                except socket.timeout:
                    print("Connection timeouts")
                    break

            client_sock.close()
            return False

        except Exception as e:
            print(e)
            client_sock.close()
            return False # returning from the thread's run() method ends the thread


    def run_server(self):        

        self.log("Starting tftp server")
        # Create a datagram socket
        main_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) # UDP
        # Bind to address and ip
        main_sock.bind((self.__ip, self.__port))
        self.log(f"TFTP server is listening on ({socket.gethostname(), self.__port})..")

        # Listen for incoming datagrams
        while True:

            try:
                # Waiting for recieving request message from the client
                packet_req , addr_client = main_sock.recvfrom(self.__buffer_size)

                # Check if something got wrong in the client request
                code_error = self.validate_request(packet_req)
                if code_error != -1:
                    packet_err = TFTP.pack_error(code_error)

                    # send error message to the client                     
                    TFTP.send_packet(packet_err, main_sock, addr_client)

                    err_msg = TFTP.TFTP_ERRORS[code_error]
                    self.log(f"\n[ERROR] by {addr_client}, Code error({code_error}): {err_msg}\n")
                    continue # continue to wait for another client request 

                # parse packet after validating
                opcode, filename, mode = self.unpack_rq_header(packet_req)

                if opcode == TFTP.RRQ_OPCODE:
                    # read first block size of bytes (like 512 bytes)
                    packet = self.pack_data(1, filename, mode)
                    self.log(f"\n[REQUEST RECEIVED]: RRQ From ({addr_client})\n")
                
                else: # WRQ request
                   
                    # check if another thread by this time created the specific file
                    # it it has been created then returns an error "File already exists"
                    if os.path.isfile(filename):  
                        packet_err = TFTP.pack_error(6) # ERROR ('File Already Exists')
                        TFTP.send_packet(packet_err, main_sock, addr_client)   
                        continue # exit thread and wait for a new connection 
                        
                    with open(filename, 'w+'): # create an empty filename 
                        pass

                    packet = TFTP.pack_ack(0)
                    self.log(f"\n[REQUEST RECEIVED]: WRQ From ({addr_client})\n")                    
                
                # open new port to send/recive files from the client
                client_sock = self.create_udp_socket(port=0) # The OS will then pick an available port for you
                self.log(f"\nOpen a new port ({client_sock.getsockname()[1]}) for the client ({addr_client})\n")
                client_sock.settimeout(self.__timeout)
                TFTP.send_packet(packet, client_sock, addr_client)  

                if opcode == TFTP.RRQ_OPCODE:  
                    self.log(f"[SEND DATA]: ({addr_client}) length({len(packet) - 4})")
                else:
                    self.log(f"[SEND ACK]: ({addr_client}) ACK number({0})")

                # open for each new client request a new thread                
                threading.Thread(target=self.handle_client, args=(packet, client_sock, addr_client, filename, mode)).start()
                    
            except Exception as e:
                print("Error: ", e)
                main_sock.close()



def main():
    # Configuring arguments parser
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', dest='port', type=int,  default=69, help='server port')
    parser.add_argument('-t', "--timeout", dest='timeout', type=int, default=3, help="timeout to close the connection")
    parser.add_argument('-c', '--cwd', dest='cwd', type=str, default='', help='Change the current directory in which the files (with relative paths) are read or written')
   
    args = parser.parse_args()

    # change current working directory
    if args.cwd != '': 
        os.chdir(args.cwd)

    server = Server(args.port, timeout=args.timeout)     
    server.run_server()    


if __name__ == '__main__':
    main()