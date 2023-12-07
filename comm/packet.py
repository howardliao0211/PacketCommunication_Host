from dataclasses import dataclass, field
from comm.constants import *

@dataclass
class Packet:
    valid:          bool
    status_msg:     bool = False
    status:         COMM_STATUS = COMM_STATUS.SUCCESS
    header:         str  = field(default_factory=str)
    direction:      int  = 0
    command:        int  = 0
    payload_len:    int  = 0
    payload:        list = field(default_factory=list)
    checksum:       int  = 0
    packet_list:    list = field(default_factory=list)

    def is_checksum_valid(self) -> bool:
        return calculate_checksum8(self.packet_list) == 0
    
    def is_header_valid(self) -> bool:
        return self.header == COMM_HEADER
    
    def is_read_direction(self) -> bool:
        return self.direction == COMM_DIR_READ

def list_to_packet(data: list) -> Packet:
    packet = Packet(True)
    byte_data = bytes(data[:])
    packet.header       = byte_data[COMM_HEADER_OFFSET: COMM_HEADER_END].decode('utf-8')
    packet.direction    = int.from_bytes(byte_data[COMM_DIR_OFFSET: COMM_DIR_END], byteorder='big')
    packet.command      = int.from_bytes(byte_data[COMM_COMMAND_OFFSET: COMM_COMMAND_END], byteorder='big')
    packet.payload_len  = int.from_bytes(byte_data[COMM_PAYLOAD_LEN_OFFSET: COMM_PAYLOAD_LEN_END], byteorder='big')
    packet.payload      = data[COMM_PAYLOAD_OFFSET: COMM_PAYLOAD_OFFSET + packet.payload_len]
    packet.checksum     = data[COMM_PAYLOAD_OFFSET + packet.payload_len]
    packet.packet_list  = data[:]

    if packet.payload_len == 1:
        packet.status_msg = True
        packet.status = COMM_STATUS(int(packet.payload[0]))

    return packet

def calculate_checksum8(byte_array: list) -> int:
    checksum = sum(byte_array) % 256
    return checksum
