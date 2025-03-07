import socket
import sys
import udt, packet, timer


def create_checksum(i,data):
    # logic to implement checksum calculation
    checksum = '80000000'.encode('utf-8')
    return checksum


def verify_checksum(i, checksum, data):
    # logic to verify checksum

    return True


def main():
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to the port
    server_address = ('localhost', 10000)
    sock.bind(server_address)
    i=0
    while True:
        pkt, addr = udt.recv(sock)
        seq, checksum, dataRcvd = packet.extract(pkt)
        print("Server: Pkt Received - ", dataRcvd)
        if verify_checksum(seq, checksum, dataRcvd):
            acktosend = "ACK - "+str(seq)
            ackpkt = packet.make(i, create_checksum(i,acktosend), bytes(acktosend, 'utf-8'))
            udt.send(ackpkt, sock, addr)
            print("Server: Ack sent - %s", acktosend)
            if dataRcvd==b'DONE':
                sock.close()
                break


if __name__ == "__main__":
    main()