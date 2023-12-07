from dataclasses import dataclass, field
from comm.constants import *
from comm.interface import COMM_Interface, COMM_Simulate
from comm.packet import Packet, list_to_packet, calculate_checksum8
import time

@dataclass
class COMM:
    protocol:   COMM_Interface
    timeout_ms: int

    def echo(self, echo_packet: list) -> bool:
        command     = COMM_COMMAND_ECHO
        payload_len = len(echo_packet)
        payload     = echo_packet[:]

        response = self.__start_transaction(command, payload_len, payload)
        if not response.valid:
            return False
        
        if response.status != COMM_STATUS.SUCCESS:
            print(f'COMM Fail. Status: {response.status}')
            return False
        
        print('Echo Payload: ')
        print(response.payload)
        print('Echo Packet')
        print(bytes(response.packet_list))

        return True

    def __start_transaction(self, cmd: int, payload_len: int, payload: list) -> Packet:
        rx_list = list()

        if not self.__send_packet(cmd, payload_len, payload):
            return Packet(False)

        elapsed_time_ms = 0
        current_time_ms = int(time.time() * 1000)

        while not self.__receive_packet(rx_list):
            elapsed_time_ms += int(time.time() * 1000) - current_time_ms
            current_time_ms  = int(time.time() * 1000)

            if elapsed_time_ms >= self.timeout_ms:
                print('Timeout')
                return Packet(False)

        packet = list_to_packet(rx_list)
        if not packet.is_header_valid() or not packet.is_read_direction():
            return Packet(True, True, COMM_STATUS.FORMAT_ERROR)
        
        if not packet.is_checksum_valid():
            return Packet(True, True, COMM_STATUS.CHECKSUM_FAIL)
        
        return packet
    
    def __receive_only_transaction(self) -> Packet:
        rx_list = list()
        elapsed_time_ms = 0
        current_time_ms = int(time.time() * 1000)

        while not self.__receive_packet(rx_list):
            elapsed_time_ms += int(time.time() * 1000) - current_time_ms
            current_time_ms  = int(time.time() * 1000)

            if elapsed_time_ms >= self.timeout_ms:
                print('Timeout')
                return Packet(False)

        packet = list_to_packet(rx_list)
        if not packet.is_header_valid() or not packet.is_read_direction():
            return Packet(True, True, COMM_STATUS.FORMAT_ERROR)
        
        if not packet.is_checksum_valid():
            return Packet(True, True, COMM_STATUS.CHECKSUM_FAIL)
        
        return packet

    def __send_packet(self, cmd: int, payload_len: int, payload: list) -> bool:
        checksum    = int()
        packet      = bytes()

        packet += COMM_HEADER.encode('utf-8')
        packet += COMM_DIR_WRITE.to_bytes(COMM_DIR_SIZE, byteorder='big')
        packet += cmd.to_bytes(COMM_COMMAND_SIZE, byteorder='big')
        packet += payload_len.to_bytes(COMM_PAYLOAD_LEN_SIZE, byteorder='big')
        packet += bytes(payload)

        checksum = calculate_checksum8(packet)
        checksum = 0x100 - checksum

        packet += checksum.to_bytes(1, byteorder='big')

        return self.protocol.send(list(packet))
    
    def __receive_packet(self, data: list) -> bool:
        return self.protocol.receive(data)

if __name__ == '__main__':
    comm = COMM(COMM_Simulate, 1000)
    comm.echo([i for i in range(10)])
