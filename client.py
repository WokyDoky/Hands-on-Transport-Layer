import socket
import sys
import udt, packet
import timer as t


def create_checksum(i,data):
    checksum = '20000000' # just for testing.
    # logic to implement checksum calculation

    return checksum


def verify_checksum(i, checksum, data):
    # implement logic to verify checksum

    return True


def main():
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(0)	 # making the socket non-blocking
    server_address = ('localhost', 10000)

    mytimer = t.Timer(1)
    try:

        # Send data
        i=0

        while i<20:
            texttosend = "mytextblah - "+str(i)
            checksum = create_checksum(i,texttosend).encode('utf-8')
            pkt = packet.make(i, checksum, bytes(texttosend, 'utf-8'))
            udt.send(pkt, sock, server_address)
            print("Client: Pkt sent - "+texttosend)

            # start timer
            mytimer.start()
            while mytimer.running() and not mytimer.timeout():
                print("timer running")
                rcvpkt, addr = udt.recv(sock)
                if rcvpkt:
                        seq, checksum, dataRcvd = packet.extract(rcvpkt)
                        if verify_checksum(seq, checksum, dataRcvd):
                            print("Client: Ack Received - %s", dataRcvd)
                            mytimer.stop()
                continue
            mytimer.stop()

            i=i+1

    finally:
        texttosend = "DONE"
        pkt = packet.make(i,bytes(texttosend, 'utf-8'))
        udt.send(pkt, sock, server_address)
        print("I am DONE sending")
        sock.close()


if __name__ == "__main__":
    main()