# TFTP-Python-Implementation
### TFTP (Trivial File Transfer Protocol) implementation

***What it include?***


[tftp server](https://github.com/kamalaweenat/tftp-python-implemention/blob/main/server.py): <br>Ruuning the server to handle every client request (put/get request)
for each request open new thread<br>

[tftp client](https://github.com/kamalaweenat/tftp-python-implemention/blob/main/client.py): <br>Sending request to the server either get or put<br>

[tftp.py](https://github.com/kamalaweenat/tftp-python-implemention/blob/main/tftp.py): <br>Shared modules for both client and servers<br>


## Features:
* Pure python
* Git/Put file of any size (can change the size block from 512)
* Timeout supported
* Handle multi-client requests - threads support
* Verbose mode for printing packet info

<br>

***Running the server:***

*Usage:*<br>
`$ ./server.py [-h] [-p PORT] [-t TIMEOUT] [-c CWD]`

Don't forget to set the execute permission: `$ chmod +x *` <br>

For example:<br>
`$ sudo ./server.py`

Note: use the sudo privilege to open the port - 69 (this is a system port)

Options used to run this command:

**-p**: change the port use the <br>
**-t**: timeout to close the connection use the option<br>
**-c**: current directory for the server use the option <br>

<br>

***Running the client:***

*Usage:*<br>
`$ ./client.py [-h] [-p PORT] [-t TIMEOUT] [-c CWD] [-b BLKSIZE] [-n TARGETNAME] {get,put} ... host filename`

Options used to run this command:

**-p**: change the port use the <br>
**-t**: timeout to close the connection use the option<br>
**-c**: current directory for the server use the option <br>
**-b**: indicates the size in bytes of the data block used to transfer files (default, 512) <br>

For example:<br>
`$ ./client.py put 10.0.0.29 msgFile`



