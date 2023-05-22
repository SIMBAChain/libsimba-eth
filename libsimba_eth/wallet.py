from abc import ABC, abstractmethod

from libsimba.exceptions import SimbaSigningException, SimbaWalletException
from libsimba.wallet import Wallet
from web3.auto import w3


class WalletBase(Wallet, ABC):
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
