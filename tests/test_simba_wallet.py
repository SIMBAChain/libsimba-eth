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
import pytest
from libsimba.exceptions import SimbaWalletException, SimbaSigningException
from libsimba_eth.hdwallet import HDWallet
from libsimba_eth.account import Account


class TestWallet(unittest.TestCase):
    def test_generate_from_mnemonic(self):
        wallet = HDWallet()
        mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        wallet.generate_from_mnemonic(mnemonic)
        self.assertIsNotNone(wallet.wallet)
        self.assertEqual(wallet.wallet.mnemonic(), mnemonic)

    def test_generate_from_mnemonic_invalid(self):
        wallet = HDWallet()
        mnemonic = "invalid"
        with pytest.raises(SimbaWalletException) as exc:
            wallet.generate_from_mnemonic(mnemonic)
        self.assertIn("Invalid mnemonic words", str(exc))
        self.assertIsNone(wallet.wallet)

    def test_generate_from_mnemonic_no_param(self):
        wallet = HDWallet()
        wallet.generate_from_mnemonic()
        self.assertIsNotNone(wallet.wallet.mnemonic())

    def test_generate_from_private_key(self):
        wallet = HDWallet()
        private_key = "1837c1be8e2995ec11cda2b066151be2cfb48adf9e47b151d46adab3a21cdf67"
        wallet.generate_from_private_key(private_key)
        self.assertIsNotNone(wallet.wallet)
        self.assertEqual(wallet.wallet.private_key(), private_key)

    def test_generate_from_private_key_invalid(self):
        wallet = HDWallet()
        private_key = "invalid"
        with pytest.raises(SimbaWalletException) as exc:
            wallet.generate_from_private_key(private_key)
        self.assertIn("Invalid private key", str(exc))
        self.assertIsNone(wallet.wallet)

    def test_delete_wallet(self):
        wallet = HDWallet()
        wallet.wallet = "bob"
        wallet.forget_wallet()
        self.assertIsNone(wallet.wallet)

    def test_delete_no_wallet(self):
        wallet = HDWallet()
        wallet.forget_wallet()
        self.assertIsNone(wallet.wallet)

    def test_wallet_exists_true(self):
        wallet = HDWallet()
        wallet.wallet = "bob"
        self.assertTrue(wallet.wallet_available())

    def test_wallet_exists_false(self):
        wallet = HDWallet()
        self.assertFalse(wallet.wallet_available())

    def test_wallet_sign(self):
        wallet = HDWallet()
        private_key = "1837c1be8e2995ec11cda2b066151be2cfb48adf9e47b151d46adab3a21cdf67"
        wallet.generate_from_private_key(private_key)
        transaction_payload = {
            "chainId": "0x1",
            "to": "0xa508dD875f10C33C52a8abb20E16fc68E981F186",
            "value": 0,
            "gas": "0x5d6a",
            "gasPrice": "0x3b9aca00",
            "data": "0xdb7eff7c00000000",
            "nonce": "0x2",
        }
        signature = wallet.sign(transaction_payload)
        expected_sig = {'hash': '0x3773a4ffc2b221b363a1736dc499a013f068ac9dcc8b7b61a96fd4909b09e50c',
                        'r': 9389877437201441527590551076413838946095745398428510897479304541253263983039,
                        'rawTransaction': '0xf86b02843b9aca00825d6a94a508dd875f10c33c52a8abb20e16fc68e981f1868088db7eff7c0000000025a014c27b777153e36245b843c842c09e3617bd8c0ebd7832d081324c9364fc81bfa0091204051b8c16da45b33c547b2289e022abb5de9d1524a0b18f5ee4c182327e',
                        's': 4102646629101590168612246216598901915663873816833034393817015735473791971966,
                        'v': 37}
        self.assertEqual(expected_sig, signature)

    def test_wallet_sign_1559(self):
        wallet = HDWallet()
        private_key = "1837c1be8e2995ec11cda2b066151be2cfb48adf9e47b151d46adab3a21cdf67"
        wallet.generate_from_private_key(private_key)
        transaction_payload = {
            "chainId": "0x1",
            "to": "0xa508dD875f10C33C52a8abb20E16fc68E981F186",
            "value": 0,
            "gas": "0x5d6a",
            "maxPriorityFeePerGas": "0x3b9aca00",
            "maxFeePerGas": "0x3b9aca00",
            "data": "0xdb7eff7c00000000",
            "nonce": "0x3",
        }
        signature = wallet.sign(transaction_payload)
        expected_sig = {'hash': '0xc7e2fc426656e1749b32e3b92c0f4b6a4b9f1c01ed2c006bc0677d40b7870dea',
                        'r': 53524252319509897870324361522032540719558513194970647790878361227687436289664,
                        'rawTransaction': '0x02f8720103843b9aca00843b9aca00825d6a94a508dd875f10c33c52a8abb20e16fc68e981f1868088db7eff7c00000000c080a07655a73b250c1a8fc383b87ead035f8cc880e356df77d872d1eb57b78a650680a001bb667a8c9a9294f91a044ef080d519ddb837b5338c91d79071de3ae2b8fcd1',
                        's': 783420531744998595018119459454821602758617200384347858859847985470216142033,
                        'v': 0}
        self.assertEqual(expected_sig, signature)

    def test_account_sign_1559(self):
        account = Account(private_key="1837c1be8e2995ec11cda2b066151be2cfb48adf9e47b151d46adab3a21cdf67")
        transaction_payload = {
            "chainId": "0x1",
            "to": "0xa508dD875f10C33C52a8abb20E16fc68E981F186",
            "value": 0,
            "gas": "0x5d6a",
            "maxPriorityFeePerGas": "0x3b9aca00",
            "maxFeePerGas": "0x3b9aca00",
            "data": "0xdb7eff7c00000000",
            "nonce": "0x3",
        }
        signature = account.sign(transaction_payload)
        expected_sig = {'hash': '0xc7e2fc426656e1749b32e3b92c0f4b6a4b9f1c01ed2c006bc0677d40b7870dea',
                        'r': 53524252319509897870324361522032540719558513194970647790878361227687436289664,
                        'rawTransaction': '0x02f8720103843b9aca00843b9aca00825d6a94a508dd875f10c33c52a8abb20e16fc68e981f1868088db7eff7c00000000c080a07655a73b250c1a8fc383b87ead035f8cc880e356df77d872d1eb57b78a650680a001bb667a8c9a9294f91a044ef080d519ddb837b5338c91d79071de3ae2b8fcd1',
                        's': 783420531744998595018119459454821602758617200384347858859847985470216142033,
                        'v': 0}
        self.assertEqual(expected_sig, signature)

    def test_wallet_sign_no_wallet(self):
        wallet = HDWallet()
        with pytest.raises(SimbaWalletException) as exc:
            wallet.sign({})
        self.assertIn("No wallet loaded!", str(exc))

    def test_wallet_sign_invalid_addr(self):
        wallet = HDWallet()
        private_key = "1837c1be8e2995ec11cda2b066151be2cfb48adf9e47b151d46adab3a21cdf67"
        wallet.generate_from_private_key(private_key)
        transaction_payload = {
            "to": "0xa508dD875f10C33C52a8abb20E16fc",
            "value": 0,
            "gas": "0x5d6a",
            "gasPrice": "0x3b9aca00",
            "data": "0xdb7eff7c00000000",
            "nonce": "0x2",
        }
        with pytest.raises(SimbaSigningException) as exc:
            wallet.sign(transaction_payload)
        self.assertIn("Transaction had invalid fields", str(exc))

    def test_wallet_sign_missing_key(self):
        wallet = HDWallet()
        private_key = "1837c1be8e2995ec11cda2b066151be2cfb48adf9e47b151d46adab3a21cdf67"
        wallet.generate_from_private_key(private_key)
        transaction_payload = {
            "value": 0,
            "gas": "0x5d6a",
            "gasPrice": "0x3b9aca00",
            "data": "0xdb7eff7c00000000",
            "nonce": "0x2",
        }
        with pytest.raises(SimbaSigningException) as exc:
            wallet.sign(transaction_payload)
        self.assertIn("Missing field in transaction: 'to'", str(exc))

    def test_get_address(self):
        wallet = HDWallet()
        private_key = "1837c1be8e2995ec11cda2b066151be2cfb48adf9e47b151d46adab3a21cdf67"
        wallet.generate_from_private_key(private_key)
        addr = wallet.get_address()
        self.assertEqual(addr, "0xa8E070649A1D98651D281FdD428BD3EeC0d279e0")

    def test_wallet_get_address_no_wallet(self):
        wallet = HDWallet()
        with pytest.raises(SimbaWalletException) as exc:
            wallet.get_address()
        self.assertIn("No wallet loaded!", str(exc))

    def test_signing(self):
        account = Account(private_key="1837c1be8e2995ec11cda2b066151be2cfb48adf9e47b151d46adab3a21cdf67")
        sig = account.sign_values(values=[("string", "hello"), ("uint256", 12)])
        self.assertEqual(sig,
                         "0x8c25852645d71a528aaa00a87908ba61cb8a380f3e4843c3d296cf7348b6224a0ffbd470a2b994d629c5dd80fb860c219b41e45534caa4ed54e4cd286be3e89e1c")

        sig = account.sign_message("hello")
        self.assertEqual(sig,
                         "0x430119b79e1652978d552d5aac5b1f4ad567e59bb5b27d172674377719b4feda058c6f0559b58855287e16e470a84df2dc49e92b10d510d44febe068368262cf1c")

        with pytest.raises(SimbaSigningException):
            _ = account.sign_values(values=[("str", "hello"), ("uint256", 12)])

        with pytest.raises(SimbaSigningException):
            _ = account.sign_values(values=[("string", "hello"), ("uint256", "foo")])
