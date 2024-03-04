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

import binascii

from typing import Optional

from libsimba.exceptions import SimbaWalletException

from hdwallet import BIP44HDWallet
from hdwallet.cryptocurrencies import EthereumMainnet
from hdwallet.utils import generate_mnemonic
from libsimba_eth.wallet import WalletBase


class HDWallet(WalletBase):
    def __init__(self) -> None:
        self.wallet = None

    def generate_from_mnemonic(self, mnemonic: Optional[str] = None) -> None:
        """
        Create a new wallet using that wallet mnemonic. Set self.wallet to this new wallet.

        Args:
            mnemonic: A string the wallet will use to create the wallet
        """
        wallet: BIP44HDWallet = BIP44HDWallet(cryptocurrency=EthereumMainnet)

        if not mnemonic:
            mnemonic = generate_mnemonic(language="english", strength=128)

        try:
            wallet.from_mnemonic(
                mnemonic=mnemonic,
                language="english",
            )
        except ValueError as exc:
            raise SimbaWalletException(message=str(exc))
        # Clean default BIP44 derivation indexes/paths
        wallet.clean_derivation()

        self.wallet = wallet

    def generate_from_private_key(self, private_key: str) -> None:
        """
        Create a new wallet using that wallet mnemonic. Set self.wallet to this new wallet.

        Args:
            mnemonic: A string the wallet will use to create the wallet
        """
        wallet: BIP44HDWallet = BIP44HDWallet(cryptocurrency=EthereumMainnet)

        try:
            wallet.from_private_key(private_key=private_key)
        except binascii.Error:
            raise SimbaWalletException(message="Invalid private key")

        # Clean default BIP44 derivation indexes/paths
        wallet.clean_derivation()
        self.wallet = wallet

    def forget_wallet(self) -> None:
        """
        Remove the current wallet. Any attempts to do anything with the wallet
        after this is called will fail.
        """
        self.wallet = None

    def wallet_available(self) -> bool:
        """
        Does a wallet currently exists?

        Returns:
            Returns a boolean indicating if a wallet exist.
        """
        return self.wallet is not None

    def _address(self) -> str:
        return self.wallet.address()  # type: ignore

    def _key(self) -> str:
        return self.wallet.private_key()  # type: ignore
