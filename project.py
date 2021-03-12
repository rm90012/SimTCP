"""
Where solution code to project should be written.  No other files should
be modified.
"""

import socket
import io
import time
import typing
import struct
import util
import util.logging
import threading
from threading import Timer
from queue import Queue  

def send(sock: socket.socket, data: bytes):
    """
    Implementation of the sending logic for sending data over a slow,
    lossy, constrained network.

    Args:
        sock -- A socket object, constructed and initialized to communicate
                over a simulated lossy network.
        data -- A bytes object, containing the data to send over the network.
    """

    # Naive implementation where we chunk the data to be sent into
    # packets as large as the network will allow, and then send them
    # over the network, pausing half a second between sends to let the
    # network "rest" :)
    global pkt
    global ack_recv
    ##sock.settimeout(20)
    
    def setInterval(interval):
        def decorator(function):
            def wrapper(*args, **kwargs):
                stopped = threading.Event()

                def loop(): # executed in another thread
                    while not stopped.wait(interval): # until stopped
                        function(*args, **kwargs)

                t = threading.Thread(target=loop)
                t.daemon = True # stop if the program exits
                t.start()
                return stopped
            return wrapper
        return decorator

    
    wait = False

    @setInterval(20)
    def function():
        global ack_recv
        nonlocal wait 
                                                    ## What if First Packet is dropped ?
        if (ack_recv == 0 and return_data == None):    ##Packet not recieved, so Resend 
            sock.send(pkt)
            print("Packet not recieved...Resending Packet")
        elif(ack_recv == 1 ):                    ##Packet recieved so timer should not send another packet
            ##sock.send(ACK.to_bytes(1,'big'))
            print("Packet recieved in correct order")
            ack_recv = 0 
        ##elif(ack_recv == 0 and ackWait == 0):
            ##logger.info("ACK Possibly dropped...Waiting for ACK ")
        if (ackWait == 0 and wait):      ##Waiting if ACK got possibly dropped so timer will not refire Packet or send duplicate packet 
            logger.info("ACK Possibly dropped...Waiting for ACK ")
            return



    sock.setblocking(1)
    logger = util.logging.get_logger("project-sender")
    seqNum = 0
    seqNumRecv = 0
    chunk_size = 1398 ##util.MAX_PACKET 
    offsets = range(0, len(data), 1398) ##util.MAX_PACKET
    ACK = 1
    ack_recv = 0
    ackWait = 0 
    rounds = 0

    for chunk in [data[i:i + chunk_size] for i in offsets]:

        wait = False 
        seqNumSend = seqNum.to_bytes(1, 'big')
        pkt = bytearray(seqNumSend)
        pkt = pkt + chunk 
        sock.send(pkt)
        ack_recv = 0 
        ##print(pkt)
        ##sock.setblocking(0)
        logger.info("Sending %s bytes", len(pkt)) 
        logger.info("Waiting for %d seconds for ACK or Timeout", 18)
        ##stop = function()
        while(ackWait == 0 ): ##Waiting for ACK 0 state
            print("ITS IN ACK WAITING MODE")
            return_data = sock.recv(1)
            print(return_data)
            stop = function()
            ##print(return_data)
            if (int.from_bytes(return_data,'big') == 1 ): ## if the packet is recieved correctly recieved 
                ack_recv = 1 
                logger.info("ACK recieved for packet %d", seqNum)
                ackWait = 1 
                wait = False 
                ##sock.send(ackWait.to_bytes(1,'big'))
            elif (int.from_bytes(return_data,'big') == 0): ## if the packet is not recived 
                ack_recv = 0 
                logger.info("ACK not recieved for packet %d will resend", seqNum)
                wait = True 
            elif(return_data == None): ##ACK dropped Case... Should this be handled by the timer? 
                logger.info("ACK probably dropped... Sender will Wait")
                ack_recv = 0 

        seqNum = seqNum + 1
        ackWait = 0 
        print("\n   \n   \n  round: ", rounds)
        rounds = rounds + 1 

       
def recv(sock: socket.socket, dest: io.BufferedIOBase) -> int:
    """
    Implementation of the receiving logic for receiving data over a slow,
    lossy, constrained network.

    Args:
        sock -- A socket object, constructed and initialized to communicate
                over a simulated lossy network.

    Return:
        The number of bytes written to the destination.
    """
    global ACK
    def setInterval(interval):
        def decorator(function):
            def wrapper(*args, **kwargs):
                stopped = threading.Event()

                def loop(): # executed in another thread
                    while not stopped.wait(interval): # until stopped
                        function(*args, **kwargs)

                t = threading.Thread(target=loop)
                t.daemon = True # stop if the program exits
                t.start()
                return stopped
            return wrapper
        return decorator

    expectedSeqnum = 0
    
    error = False 
    ackDropped = False

    @setInterval(21)
    def recieverTime():
        nonlocal expectedSeqnum 
        nonlocal error
        nonlocal ackDropped

        '''
        if(recvSeqnum == expectedSeqnum):
            ACK = 1 
            sock.send(ACK.to_bytes(1,'big'))
            logger.info("Sending ACK for packet %d", recvSeqnum)
            expectedSeqnum = expectedSeqnum + 1
        '''                                                                              
        
        if (recvSeqnum != expectedSeqnum and ackDropped ):  ## IF ACK gets dropped /// I know this logic is wrong I am trying to correct it 
            ACK = 1                                      ## Need to fix issue with resending ACK when the ACK was not dropped but the packet was dropped
            sock.send(ACK.to_bytes(1, 'big'))
            logger.info("ACK was Dropped, resending")
            ##expectedSeqnum = expectedSeqnum + 1 
            expectedSeqnum = recvSeqnum
        elif (recvSeqnum != expectedSeqnum):  ## IF Packet from the sender gets dropped 
            ACK = 0 
            sock.send(ACK.to_bytes(1, 'big'))
            logger.info("Packet not recieved...Resend Packet")
            if (expectedSeqnum > recvSeqnum):
                expectedSeqnum = expectedSeqnum - 1 
            elif (expectedSeqnum < recvSeqnum):
                expectedSeqnum = expectedSeqnum + 1 
            ackDropped = False 


    logger = util.logging.get_logger("project-receiver")
    num_bytes = 0 
    ##sock.settimeout(15)
    sock.setblocking(1)

    while True:
        data = sock.recv(1400) ##util.MAX_PACKET
        ackDropped = False 
        try:
            '''
            print("recv timed out")
            sock.setblocking(0)
            print("DATA Not recieved... Sending 0 ACK")
            ACK = 0
            sock.send(ACK.to_bytes(0, 'big'))
            '''
        ##if not data:
          ##  break
            ackDropped = False 
            logger.info("recieved %d bytes" , len(data))
            recvSeqnum = data[0]
            data = data[1:len(data)]
            logger.info("Recieved Sequence number %d expecting Sequence number %d ", recvSeqnum, expectedSeqnum)
            '''
            if (error):
                expectedSeqnum = expectedSeqnum - 1 
                ackDropped = True 
                error = False
                ''' 
            if(recvSeqnum == expectedSeqnum): ## Sending ACK for correctly Recieved packet from Sender
                ACK = 1 
                sock.send(ACK.to_bytes(1,'big'))
                logger.info("Sending ACK for packet %d", recvSeqnum)
                expectedSeqnum = expectedSeqnum + 1
                stop = recieverTime()
                ##ackDropped = True
            elif (recvSeqnum != expectedSeqnum): ##If the packet recieved is not correct
                ACK = 0 
                sock.send(ACK.to_bytes(1, 'big'))
                logger.info("Packet sent out of order... Send last packet")
        except socket.error as e:
            err = e.args[0]
            sock.setblocking(0)
        dest.write(data)
        num_bytes += len(data)
        dest.flush()
    return num_bytes 
    