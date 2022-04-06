import struct

class TFTP:

    RRQ_OPCODE = 1
    WRQ_OPCODE = 2
    DAT_OPCODE = 3
    ACK_OPCODE = 4
    ERR_OPCODE = 5
   
    TRANSFER_MODES = ['netascii', 'octet', 'mail']

    TFTP_ERRORS = {
        0: 'Not Defined',
        1: 'File Not Found',
        2: 'Access Violation',
        3: 'Disk Full or Allocation Exceeded',
        4: 'Illegal TFTP operation',
        5: 'Unknown Transfer TID',
        6: 'File Already Exists',
        7: 'No Such User'
    }

    def __init__(self, blksize, transfer_mode):
        self.__blksize = blksize
        self.__transfer_mode = transfer_mode
        

    @property
    def TransferMode(self):
        return self.__transfer_mode   

    @property
    def BlckSize(self):
        return self.__blksize   

    @BlckSize.setter
    def BlckSize(self, blksize):
        self.__blksize = blksize   

    
    def read_file(self, block_no, filename):
        # Read file in binary mode
        with open(filename, 'rb') as f:
            # the position of the read/write pointer within the file
            # read each 512 bytes
            offset = (block_no - 1) * self.BlckSize
            # 0: The whence argument is optional and defaults to 0, which means absolute file positioning
            f.seek(offset, 0)
            # The number of bytes to return
            content = f.read(self.BlckSize)
        return content


    def pack_data(self, block_no, filename, mode): 
        
        #       DATA Message:
        #       ----------------------------------------------
        #       |   OpCode(03)  |  Block #  |      Data      |
        #       ----------------------------------------------
        #       |    2 bytes    |  2 bytes  |   0-512 bytes  |
        #       ---------------------------------------------- 

        # append data (read 512 bytes max from file) 
        data = self.read_file(block_no, filename)   

        # Parsing data into data packet
        # { (!)-Network Big Endian, (H)-unsigned short integer 2 bytes, (s)-char[] bytes 
        formatter = '!HH{}s'  
        formatter = formatter.format(len(data))

        # convert all data to bytes
        return struct.pack(formatter, TFTP.DAT_OPCODE, block_no, data)

    def get_dat_send_ack(self, packet, filename, sock, addr): 
        """ Put packet in server/clinet that works the same way
            return True if it's not the last packet to send more packets
            otherwise return false to finalize work """       
        
        opcode, block_no, data = TFTP.unpack_dat(packet)
                        
        with open(filename, 'ab+') as f:
            f.write(data)

        print(f"[GET DATA]: ({addr}) length({len(data)})")    

        packet_ack = TFTP.pack_ack(block_no)       
        TFTP.send_packet(packet_ack, sock, addr)

        print(f"[SEND ACK]: ({addr}) ACK number({block_no})")

        # Close connection once all data has been received and final 
        # ACK packet has been sent
        if len(data) < self.__blksize:
            print('Last packet..')
            return None # nothing is left to send

        return packet_ack 
   
    def get_ack_send_dat(self, last_packet, packet, filename, sock, addr, mode):
        """ Get ack packet and send data from server/clinet that works the same way
            return True if it's not the last packet to send more packets
            otherwise return false to finalize work""" 
    
        opcode, block_no = TFTP.unpack_ack(packet)    
        
        print(f"[GET ACK]: ({addr}) ACK number({block_no})")  

        # Check length of the last DATA packet sent, if the Datagram length is 
        # less than 516 it is the last packet. Upon receiving the final ACK packet
        # from the client we can terminate the connection.
        if last_packet and len(last_packet) < self.BlckSize + 4 :
            print('Last packet..')
            return None

        packet_data = self.pack_data(block_no + 1, filename, mode)    
        TFTP.send_packet(packet_data, sock, addr)

        print(f"[SEND DATA]: ({addr}) length({len(packet_data) - 4})")
        return packet_data       


    @staticmethod
    def pack_rq_header(opcode, filename, mode):
        
        #       RRQ/WRQ Message:
        #       ---------------------------------------------------------------------
        #       |   OpCode(01/02)  |  Filename  |  All 0s  |    Mode     |  All 0s  |
        #       ---------------------------------------------------------------------
        #       |      2 bytes     |  2 bytes   |  1 byte  |  (n) bytes  |  1 byte  |
        #       ---------------------------------------------------------------------

        # { (!)-Network Big Endian, (H)-unsigned short integer 2 bytes, 
        # (s)-char[] bytes, unsigned char integer 1 byte}
        
        formatter = '!H{}sB{}sB' 
        formatter = formatter.format(len(filename), len(mode))
        return struct.pack(formatter, opcode, filename.encode('utf-8'), 0, mode.encode('utf-8'), 0)


    @staticmethod
    def pack_ack(block_no):

        #       ACK Message:
        #       -----------------------------
        #       |   OpCode(04)  |  Block #  |
        #       -----------------------------
        #       |    2 bytes    |  2 bytes  |
        #       -----------------------------
    
        # { (!)-Network Big Endian, (H)-unsigned short integer 2 bytes
        formatter = '!HH'  
        return struct.pack(formatter, TFTP.ACK_OPCODE, block_no)

    @staticmethod
    def pack_error(error_code):

        #       ERROR Message:
        #       -------------------------------------------------------
        #       |   OpCode(05)  |  ErrorCode  |   ErrMsg   |  All 0s  | 
        #       -------------------------------------------------------
        #       |    2 bytes    |  2 bytes    |  (n) bytes |  1 byte  |
        #       -------------------------------------------------------
        
        # { (!)-Network Big Endian, (H)-unsigned short integer 2 bytes, (s)-char[] bytes 
        formatter = '!HH{}sB' 
        # Get error string message and encode it
        error_msg = TFTP.TFTP_ERRORS[error_code].encode('utf-8')
        formatter = formatter.format(len(error_msg))
        return struct.pack(formatter, TFTP.ERR_OPCODE, error_code, error_msg, 0)


    # Get opcode from TFTP header   
    @staticmethod 
    def get_opcode(packet):
        # Read first two bytes in big indean format
        opcode = int.from_bytes(packet[0:2], byteorder='big')           
        # return like RRQ/WRQ/ACK..
        return opcode 


    # Return filename and mode from decoded RRQ/WRQ header   
    @staticmethod 
    def unpack_rq_header(packet):
        # |   OpCode(01/02)  |  Filename  |  All 0s  |    Mode     |  All 0s  |  
        # skip the opcode part and split by zero byte
        opcode = int.from_bytes(packet[0:2], byteorder='big')  # Extracting opcode
        header = packet[2:].split(b'\x00') 
        filename = header[0].decode('utf-8');
        mode = header[1].decode('utf-8').lower()    
        return opcode, filename, mode

    
    # DAT PACKET UNPACK  
    @staticmethod  
    def unpack_dat(packet):
        # |   OpCode(03)  |  Block #  |      Data      |
        # Packet like: '\x00\x03\x00\x01\xDATA'  
        opcode   = int.from_bytes(packet[0:2], byteorder='big')  # Extracting opcode
        block_no = int.from_bytes(packet[2:4], byteorder='big')  # Extracting Block number
        data = packet[4:] 
        return opcode, block_no, data


    # ACK PACKET UNPACK  
    @staticmethod  
    def unpack_ack(packet):
        # |   OpCode(04)  |  Block #  |
        # packet like: '\x00\x04\x00\x01'      
        opcode   = int.from_bytes(packet[0:2] , byteorder='big')  # Extracting opcode
        block_no = int.from_bytes(packet[2:]  , byteorder='big')  # Extracting Block number
        return opcode, block_no


    # ACK PACKET UNPACK  
    @staticmethod 
    def unpack_error(packet):    
        # |   OpCode(05)  |  ErrorCode  |   ErrMsg   |  All 0s  |       
        opcode     = int.from_bytes(packet[0:2] , byteorder='big')  # Extracting opcode
        error_code = int.from_bytes(packet[2:4]  , byteorder='big')  # Extracting error code        
        error_msg  = packet[4:-1].decode('utf-8');  # Extracting error message
        return opcode, error_code, error_msg

    @staticmethod
    def send_packet(packet, socket, addr):
        socket.sendto(packet, addr)

    





