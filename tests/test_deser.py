#  Copyright (c) 2024 SIMBA Chain Inc. https://simbachain.com
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

import unittest
from libsimba_eth.utils import convert_bytes32_to_string, convert_to_bytes32_array, keccak_hash, string_to_uint256


class TestSer(unittest.TestCase):

    def test_bytes_to_string(self):
        edition_bytes = convert_to_bytes32_array(" Edition 1000000000/1000000000", 1)
        edition_str = convert_bytes32_to_string(edition_bytes, 1)
        assert edition_str == " Edition 1000000000/1000000000"

        data = {
            "name": "2020 Lorem ipsum dolor sit amet",
            "contentHash": "0x8eebc511ae55f498d9f0a3a1ddcb58a0bb639c9f8f89d6c83e430f25de900ff2",
            "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut lab",
            "image": "https://picsum.photos/200/300/?t=asdfj938j0qf98jas0df8je098j2faa",
        }
        inputs = {
            "name": convert_to_bytes32_array(data["name"], 1),
            "description": convert_to_bytes32_array(data["description"], 4),
            "image": convert_to_bytes32_array(data["image"], 4),
            "contentHash": data["contentHash"]
        }

        outputs = {
            "name": convert_bytes32_to_string(inputs["name"]),
            "description": convert_bytes32_to_string(inputs["description"]),
            "image": convert_bytes32_to_string(inputs["image"], 4),
            "contentHash": inputs["contentHash"]
        }
        assert data == outputs

        inputs_no_pref = {
            "name": convert_to_bytes32_array(data["name"], 1, prefix=False),
            "description": convert_to_bytes32_array(data["description"], 4, prefix=False),
            "image": convert_to_bytes32_array(data["image"], 4, prefix=False),
            "contentHash": data["contentHash"]
        }

        outputs_no_pref = {
            "name": convert_bytes32_to_string(inputs_no_pref["name"]),
            "description": convert_bytes32_to_string(inputs_no_pref["description"]),
            "image": convert_bytes32_to_string(inputs_no_pref["image"]),
            "contentHash": inputs["contentHash"]
        }
        assert data == outputs_no_pref

        # truncated
        description = convert_bytes32_to_string(inputs["description"], 2)
        assert description == "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do "
        assert len(description) == 64

    def test_conversions(self):
        hash_val = keccak_hash("A short string")
        assert hash_val == "c02616352442fd8d6b29e47623743b0644e7168b988c4545b71df141245db363"
        int_val = int.from_bytes(bytes.fromhex(hash_val), byteorder="big", signed=False)
        assert int_val == 86911360387564328691877682441780275511611438275732502394544537523081168401251
        recovered = int_val.to_bytes(32, byteorder='big')
        hexed = recovered.hex()
        assert hexed == hash_val
        int_val2 = string_to_uint256("A short string")
        #  function convert(string memory value) external pure returns (uint256) {
        #      bytes32 hash = keccak256(bytes(value));
        #      return uint256(hash);
        #  }
        #  86911360387564328691877682441780275511611438275732502394544537523081168401251
        assert int_val2 == int_val
        int_val3 = string_to_uint256(f"A {' '.join(['very' for i in range(100)])}long string")
        assert int_val3 == 44831467989385379626249444820128067825371402133342580492608562458279217187427
