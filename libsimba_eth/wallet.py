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

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple, Union

from eth_account.datastructures import SignedMessage
from eth_account.messages import encode_defunct
from libsimba.exceptions import SimbaSigningException, SimbaWalletException
from libsimba.wallet import Wallet
from web3.auto import w3


class WalletBase(Wallet, ABC):

    def sign_message(self, value: Union[bytes, bytearray, str]) -> str:
        if isinstance(value, str):
            solidity_type = "string"
        else:
            solidity_type = "bytes"
        return self.sign_values(values=[(solidity_type, value)], hash_message=False)

    def sign_values(
        self, values: List[Tuple[str, Any]], hash_message: Optional[bool] = True
    ) -> str:
        """Sign a message given the types and values and an identity dict with keys 'pub' and 'priv'
        The 'pub' element is the address, the 'priv' element is the private key.

        If the hash_message argument is present and set to false, the signing will happen directly on the input.
        This requires that the input is either a single 'bytes' type string in hex format, or a single 'string' type.
        """
        types, data = zip(*values)
        if not hash_message:
            if (
                len(types) == 1
                and isinstance(data[0], str)
                and types[0] in ["bytes", "string"]
            ):
                if data[0].startswith("0x"):
                    msg = data[0]
                else:
                    msg = "0x{}".format(data[0].encode().hex())
            else:
                raise SimbaSigningException(
                    message="Can only not hash message if inputs is a hex bytes",
                )
        else:
            try:
                msg = w3.solidity_keccak(types, data).hex()
            except Exception as ex:
                raise SimbaSigningException(
                    message=str(ex),
                )
        try:
            message = encode_defunct(hexstr=msg)
            signed_message: SignedMessage = w3.eth.account.sign_message(
                message, private_key=self.get_private_key()
            )
            hex = signed_message.signature.hex()
            return hex
        except Exception as ex:
            raise SimbaSigningException(
                message=str(ex),
            )

    def sign(self, payload: dict) -> dict:
        """
        Sign the transaction payload with the wallet

        Args:
            payload: a transaction object
        Returns:
            Returns the signed transaction.
            The part of the signed transaction to be sent to the server
            is the `rawTransaction` field of the returned signature dict.
        """
        if not self.wallet_available():
            raise SimbaWalletException(message="No wallet loaded!")

        try:
            transaction_template = {
                "to": payload["to"],
                "value": payload.get("value", 0),
                "gas": payload["gas"],
                "data": payload["data"][2:],
                "nonce": payload["nonce"],
            }
            if payload.get("chainId"):
                transaction_template["chainId"] = payload["chainId"]
            if payload.get("gasPrice"):
                # legacy transaction
                transaction_template["gasPrice"] = payload["gasPrice"]
            else:
                # EIP 1559 transaction
                transaction_template["maxPriorityFeePerGas"] = payload[
                    "maxPriorityFeePerGas"
                ]
                transaction_template["maxFeePerGas"] = payload["maxFeePerGas"]
        except KeyError as exc:
            raise SimbaSigningException(message=f"Missing field in transaction: {exc}")

        private_key = self.get_private_key()

        try:
            signed = w3.eth.account.sign_transaction(transaction_template, private_key)
        except TypeError as exc:
            raise SimbaSigningException(message=f"Invalid transaction provided: {exc}")

        return {
            "rawTransaction": signed.rawTransaction.hex(),
            "hash": signed.hash.hex(),
            "r": signed.r,
            "s": signed.s,
            "v": signed.v,
        }

    def get_address(self) -> str:
        """
        The address associated with this wallet

        Returns:
            Returns the address associated with this wallet
        """
        if not self.wallet_available():
            raise SimbaWalletException(message="No wallet loaded!")
        return self._address()

    def get_private_key(self) -> str:
        if not self.wallet_available():
            raise SimbaWalletException(message="No wallet loaded!")
        return self._key()

    @abstractmethod
    def _address(self) -> str:
        """Return the address"""
        ...

    @abstractmethod
    def _key(self) -> str:
        """Return the private key"""
        ...
