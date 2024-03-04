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

from eth_account import Account as web3Account

from libsimba_eth.wallet import WalletBase


class Account(WalletBase):
    def __init__(self, private_key: str):
        self.account = web3Account.from_key(private_key)

    def forget_wallet(self) -> None:
        """
        Remove the current wallet. Any attempts to do anything with the wallet
        after this is called will fail.
        """
        self.account = None

    def wallet_available(self) -> bool:
        """
        Does a wallet currently exists?

        Returns:
            Returns a boolean indicating if a wallet exist.
        """
        return self.account is not None

    def _address(self) -> str:
        return self.account.address  # type: ignore

    def _key(self) -> str:
        return self.account.key  # type: ignore
