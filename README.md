# TFTP-Python-Implementation
### TFTP (Trivial File Transfer Protocol) implementation

***What it include?***


[TFTP Server](https://github.com/kamalaweenat/tftp-python-implemention/blob/main/server.py): <br>Ruuning the server to handle every client request (put/get request)
for each request open new thread<br>

[TFTP Client](https://github.com/kamalaweenat/tftp-python-implemention/blob/main/client.py): <br>Sending request to the server either get or put<br>

[tftp.py](https://github.com/kamalaweenat/tftp-python-implemention/blob/main/tftp.py): <br>Shared modules for both client and servers<br>


## Features:
* Pure python
* Git/Put file of any size (can change thae size block from 512)
* Timeout supported
* Handle multi-client requests - threads support
* Verbose mode for printing packet info


