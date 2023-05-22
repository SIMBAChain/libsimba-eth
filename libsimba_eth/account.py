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
        return self.account.address

    def _key(self) -> str:
        return self.account.key
