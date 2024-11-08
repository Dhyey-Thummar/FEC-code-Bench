from typing import Optional, List
from pyo3 import create_exception, wrap_pyfunction, wrap_pymodule
from pyo3 import PyResult, PyErr, Python, PyModule, PyObject, PyBytes, PyClass

class Encoder:
    def __init__(self, encoder_native):
        self.encoder = encoder_native

    @staticmethod
    def with_defaults(data: bytes, maximum_transmission_unit: int) -> 'Encoder':
        encoder_native = EncoderNative.with_defaults(data, maximum_transmission_unit)
        return Encoder(encoder_native)

    def get_encoded_packets(self, py: Python, repair_packets_per_block: int) -> List[PyBytes]:
        packets = [
            PyBytes.new(py, packet.serialize()) 
            for packet in self.encoder.get_encoded_packets(repair_packets_per_block)
        ]
        return packets


class Decoder:
    def __init__(self, decoder_native):
        self.decoder = decoder_native

    @staticmethod
    def with_defaults(transfer_length: int, maximum_transmission_unit: int) -> 'Decoder':
        config = ObjectTransmissionInformation.with_defaults(transfer_length, maximum_transmission_unit)
        decoder_native = DecoderNative.new(config)
        return Decoder(decoder_native)

    def decode(self, py: Python, packet: PyBytes) -> Optional[PyBytes]:
        result = self.decoder.decode(EncodingPacket.deserialize(packet.as_bytes()))
        return PyBytes.new(py, result) if result else None


def raptorq(py: Python, m: PyModule) -> PyResult:
    m.add_class(Encoder)
    m.add_class(Decoder)
    return m
