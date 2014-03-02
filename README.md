## MainTP.py

A python script which takes a hostname/ip address of a z/OS FTP server, a username and password and gives you either a bind shell or reverse shell and automatically connects to it. 

## How?

**Bind/Reverse Shell**: A JCL file is dynamically generated which contains either a bind or reverse shell in C. This C code is compiled, on z/OS, at the time of exploit. 

**CVE-2012-5951**: The JCL file contains an implementation of CVE-2012-5955 originally discovered by whomever perpetrated the Logica mainframe breach. Refer to https://github.com/mainframed/logica/blob/master/kuku.rx for original local priv escalation exploit on OMVS. This is essentially a REXX script that exploits a flaw to give you UID 0. 

**JCL**: A JCL file is dynamically created based on the criteria provided (shell type, ip addresses, ports), uploaded via FTP and executed by JES (using the SITE FILE=JES extended commands). 

**NetEBCDICat**: A copy of NetEBCDICat is here as well. NetEBCDICat is just an implementation, in python, of a socket ommunicator but it translates EBCDIC to ASCII because OMVS only speaks EBCDIC (ugh!). 

## Together

[+] Connecting to: mainframe.company.com : 21

[+] Switching to JES mode

[+] Inserting JCL in to job queue

[+] Job JOB00000 added to JES queue

[+] Connecting Reverse Shell - Waiting for z/OS!

id

uid=0(SYSROOT) gid=0(SYS1)

