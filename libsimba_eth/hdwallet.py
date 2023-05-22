import binascii

from libsimba.exceptions import SimbaWalletException

from hdwallet import BIP44HDWallet
from hdwallet.cryptocurrencies import EthereumMainnet
from hdwallet.utils import generate_mnemonic
from libsimba_eth.wallet import WalletBase


class HDWallet(WalletBase):
    def __init__(self) -> None:
        self.wallet = None

    def generate_from_mnemonic(self, mnemonic: str = None):
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

    def generate_from_private_key(self, private_key):
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
        return self.wallet.address()

    def _key(self) -> str:
        return self.wallet.private_key()
