import socket
import sys
import udt
import packet
import timer


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
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to the port
    server_address = ('localhost', 10000)
    print(f"Server: Starting up on {server_address[0]} port {server_address[1]}")
    sock.bind(server_address)

    expected_seq = 0  # Expected sequence number

    try:
        while True:
            print(f"Server: Waiting for packet {expected_seq}")
            pkt, addr = udt.recv(sock)
            seq, checksum, dataRcvd = packet.extract(pkt)

            print(f"Server: Received packet with seq={seq}, expected={expected_seq}")

            # Verify checksum
            if verify_checksum(seq, checksum, dataRcvd):
                print(f"Server: Valid checksum for packet with data: {dataRcvd}")

                # Check if this is the packet we're expecting
                if seq == expected_seq:
                    print(f"Server: Received expected packet {seq}")
                    # Move to next sequence number
                    expected_seq = (expected_seq + 1) % 256
                else:
                    print(f"Server: Duplicate or out-of-order packet, expected {expected_seq}, got {seq}")

                # Always ACK the received packet regardless of sequence
                ack_message = f"ACK-{seq}".encode('utf-8')
                ack_checksum = create_checksum(seq, ack_message)

                # Create and send ACK packet
                ack_pkt = packet.make(seq, ack_checksum, ack_message)
                udt.send(ack_pkt, sock, addr)
                print(f"Server: Sent ACK for packet {seq}")

                # Check if this is the termination message
                if dataRcvd == b'DONE':
                    print("Server: Received DONE message, shutting down")
                    break

            else:
                print(f"Server: Invalid checksum for packet {seq}, dropping packet")
                # For corrupted packets, we don't send an ACK

    except Exception as e:
        print(f"Server: Error: {e}")

    finally:
        print("Server: Closing socket")
        sock.close()


if __name__ == "__main__":
    main()