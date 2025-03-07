import socket
import sys
import udt
import packet
import timer as t
import time


def create_checksum(seq, data):
    """Create a checksum for the given data by counting '1' bits.

    Args:
        seq: Sequence number
        data: Data to create checksum for (string or bytes)

    Returns:
        bytes: 8-byte checksum
    """
    # Convert data to bytes if needed
    data_bytes = data.encode('utf-8') if isinstance(data, str) else data
    bit_sum = sum(bin(byte).count('1') for byte in data_bytes)
    # Ensure checksum is exactly 8 bytes
    checksum = str(bit_sum).zfill(8).encode('utf-8')
    return checksum


def verify_checksum(seq, checksum, data):
    """Verify that the received checksum matches the calculated checksum.

    Args:
        seq: Sequence number
        checksum: Received checksum (bytes)
        data: Data to verify checksum for (string or bytes)

    Returns:
        bool: True if checksum is valid, False otherwise
    """
    data_bytes = data.encode('utf-8') if isinstance(data, str) else data
    bit_sum = sum(bin(byte).count('1') for byte in data_bytes)
    expected_checksum = str(bit_sum).zfill(8).encode('utf-8')
    return checksum == expected_checksum


def main():
    # Create a UDP socket and set it to non-blocking
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(0)
    server_address = ('localhost', 10000)

    # Initialize timer with a timeout value (in seconds)
    timeout_value = 1.0
    max_retries = 10
    mytimer = t.Timer(timeout_value)

    seq = 0  # Starting sequence number

    try:
        # Send 20 messages
        for message_num in range(20):
            retries = 0
            ack_received = False
            texttosend = f"Message-{message_num}-Seq-{seq}".encode('utf-8')
            checksum = create_checksum(seq, texttosend)
            pkt = packet.make(seq, checksum, texttosend)

            # Keep trying until ACK received or max retries reached
            while not ack_received and retries < max_retries:
                # Send the packet
                udt.send(pkt, sock, server_address)
                print(f"Client: Sent packet {seq} with data: {texttosend.decode('utf-8')}")

                # Start the timer and wait for ACK
                mytimer.start()

                while mytimer.running() and not mytimer.timeout():
                    try:
                        rcvpkt, addr = udt.recv(sock)

                        if rcvpkt:
                            ack_seq, ack_checksum, dataRcvd = packet.extract(rcvpkt)

                            # Verify checksum and sequence number
                            if verify_checksum(ack_seq, ack_checksum, dataRcvd):
                                print(f"Client: Received valid ACK: {dataRcvd.decode('utf-8')}")

                                # Check if ACK is for the correct sequence number
                                if ack_seq == seq:
                                    print(f"Client: ACK matches sent sequence {seq}")
                                    ack_received = True
                                    break
                                else:
                                    print(f"Client: Received ACK for wrong sequence, expected {seq}, got {ack_seq}")
                            else:
                                print(f"Client: Received corrupted ACK, dropping")

                    except BlockingIOError:
                        # No data available, continue waiting
                        time.sleep(0.01)
                    except Exception as e:
                        print(f"Client: Error receiving: {e}")

                # Stop the timer
                mytimer.stop()

                # If no ACK received, retransmit
                if not ack_received:
                    retries += 1
                    print(f"Client: Timeout for packet {seq}, retrying ({retries}/{max_retries})")

                    # Adaptive timeout - increase timeout value slightly with each retry
                    if retries > 1:
                        timeout_value = min(timeout_value * 1.5, 5.0)
                        mytimer = t.Timer(timeout_value)
                        print(f"Client: Increased timeout to {timeout_value:.2f} seconds")

            # Check if max retries reached without ACK
            if not ack_received:
                print(f"Client: Failed to receive ACK for packet {seq} after {max_retries} attempts")
                print("Client: Connection seems unreliable, terminating")
                break

            # Move to next sequence number
            seq = (seq + 1) % 256

            # Add a small delay between packets
            time.sleep(0.1)

    finally:
        # Send termination message
        texttosend = "DONE".encode('utf-8')
        checksum = create_checksum(seq, texttosend)
        pkt = packet.make(seq, checksum, texttosend)

        # Try to send DONE message with retries
        done_received = False
        retries = 0

        while not done_received and retries < max_retries:
            udt.send(pkt, sock, server_address)
            print(f"Client: Sent DONE message with sequence {seq}")

            # Wait for ACK
            mytimer.start()
            while mytimer.running() and not mytimer.timeout():
                try:
                    rcvpkt, addr = udt.recv(sock)
                    if rcvpkt:
                        ack_seq, ack_checksum, dataRcvd = packet.extract(rcvpkt)
                        if verify_checksum(ack_seq, ack_checksum, dataRcvd) and ack_seq == seq:
                            print("Client: Received ACK for DONE message")
                            done_received = True
                            break
                except:
                    time.sleep(0.01)

            mytimer.stop()
            if not done_received:
                retries += 1
                print(f"Client: Timeout for DONE message, retrying ({retries}/{max_retries})")

        print("Client: Closing connection")
        sock.close()


if __name__ == "__main__":
    main()