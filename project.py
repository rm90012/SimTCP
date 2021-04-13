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
import errno

def send(sock: socket.socket, data: bytes):
    """
    Implementation of the sending logic for sending data over a slow,
    lossy, constrained network.

    Args:
        sock -- A socket object, constructed and initialized to communicate
                over a simulated lossy network.
        data -- A bytes object, containing the data to send over the network.
    """
    global pkt
    
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

    @setInterval(4) ##15
    def function():
        nonlocal ack_recv
        nonlocal wait 
        nonlocal rounds 
        nonlocal seqNum
        nonlocal rounds 
                                                                
        if ((ackWait == 0 and ack_recv == 0) or rounds == 0):    ##Packet not recieved, so Resend 
            sock.send(pkt)
            logger.info("Packet not recieved...Resending Packet")
            ##seqNum = seqNum - 1 
        elif(ack_recv == 1 ):                    ##Packet recieved so timer should not send another packet
            ##sock.send(ACK.to_bytes(1,'big'))
            logger.info("Packet recieved in correct order")
            ack_recv = 0 
            return

    sock.setblocking(1)
    ##sock.settimeout(20)
    logger = util.logging.get_logger("project-sender")
    seqNum = 0
    seqNumRecv = 0
    chunk_size = util.MAX_PACKET - 2 ##util.MAX_PACKET 
    offsets = range(0, len(data), chunk_size) ##util.MAX_PACKET
    ACK = 1
   
    ackWait = 0 
    rounds = 0
    Ack_Expected = 0 

    for chunk in [data[i:i + chunk_size] for i in offsets]:

        seqNumSend = seqNum.to_bytes(1, 'big')
        pkt = bytearray(seqNumSend)
        pkt = pkt + chunk 
        sock.send(pkt)
        ack_recv = 0 
        logger.info("Sending %s bytes", len(pkt)) 
        logger.info("Waiting for %d seconds for ACK or Timeout", 6)

        while(ackWait == 0 ): ##Waiting for ACK state
            ##sock.send(pkt)
            ##print("ITS IN ACK WAITING MODE") ##Debugging Purposes 
            return_data = sock.recv(1)
            stop = function() ##Starting Sender Timer

            if (int.from_bytes(return_data,'big') == Ack_Expected ): ## if the packet is recieved correctly 
                ack_recv = 1 
                logger.info("ACK recieved for packet %d", seqNum)
                temp = Ack_Expected 
                if(Ack_Expected == 0 ):
                    Ack_Expected = 1 
                elif(Ack_Expected == 1 ):
                    Ack_Expected = 0
                ackWait = 1

        if ( seqNum == 0 ): ##Adjusting Sequence numbers 
            seqNum = 1 
        elif (seqNum == 1 ):
            seqNum = 0 
        ackWait = 0 
        ##print("\n   \n   \n  round: ", rounds) ##Debugging action
        ##rounds = rounds + 1 

       
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

    expectedSeqnum = 0

    logger = util.logging.get_logger("project-receiver")
    num_bytes = 0 
    ##sock.settimeout(15)
    ##sock.setblocking(1)
    global ack_recv
    ack_recv = 0
    while True:
        try:
            data = sock.recv(util.MAX_PACKET) ##util.MAX_PACKET
            if not data:
                break 
        except socket.error as e:
            err = e.args[0]
            if(err == errno.EAGAIN or err == errno.EWOULDBLOCK):
                time.sleep(1) 
                ##print('No Data Avaiable') ##If first Packet is Dropped, Recv should catch the exception and continue listening for refire
                continue 
        else: 
            logger.info("recieved %d bytes" , len(data))
            recvSeqnum = data[0]
            data = data[1:len(data)]
            logger.info("Recieved Sequence number %d expecting Sequence number %d ", recvSeqnum, expectedSeqnum)

            if(recvSeqnum == expectedSeqnum): ## Sending ACK for correctly Recieved packet from Sender
                ACK = recvSeqnum 
                sock.send(ACK.to_bytes(1,'big'))
                logger.info("Sending ACK for packet %d", recvSeqnum)
                if (expectedSeqnum == 0):
                    expectedSeqnum = 1 
                elif (expectedSeqnum == 1 ):
                    expectedSeqnum = 0 
                dest.write(data)

            elif(recvSeqnum != expectedSeqnum): ##Detect Duplicate for Lost ACK or Premature Timeout from Sender timer  
                logger.info("Duplicated Detected...Not Writing to Data")
                if (recvSeqnum != expectedSeqnum):
                    expectedSeqnum = recvSeqnum
                    ACK = expectedSeqnum
                    sock.send(ACK.to_bytes(1, 'big'))
                if (expectedSeqnum == 0 ):
                    expectedSeqnum = 1 
                elif(expectedSeqnum == 1 ):
                    expectedSeqnum = 0 

            num_bytes += len(data)
            dest.flush()
    return num_bytes 
    