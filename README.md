## MainTP.py

A python script which takes a hostname/ip address of a z/OS FTP server, a username and password and gives you shell access in OMVS. 

## How?

**Netcat**: A copy of the netcat binary is stored in this script BASE64 encoded. It's been precompiled in OMVS to make this a stand alone script. After connecting to z/OS it uploads this file. 

**JCL**: A JCL file is dynamically created based on a bunch of criteria. It copies the binary and executes a listener on a random port. 

**NetEBCDICat**: A copy of NetEBCDICat is here as well. NetEBCDICat is just an implementation, in python, of netcat but it translates EBCDIC to ASCII because netcat in OMVS only speaks EBCDIC. 

## Together

[+] Connecting to: mainframe.company.com : 21

[+] Uploading trapdoor binary

[+] Switching to JES mode

[+] Inserting JCL in to job queue

[+] Cleaning up...

[+] Connecting Shell on port 50033 .....Done!

id

uid=31337(CASE) gid=0(GRP1)

