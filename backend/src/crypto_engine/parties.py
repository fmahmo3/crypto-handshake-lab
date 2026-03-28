"""Participant classes for the DH key exchange."""
from __future__ import annotations

from dataclasses import dataclass, field

from cryptography.hazmat.primitives.asymmetric.dh import (
    DHParameters,
    DHPrivateKey,
    DHPublicKey,
)

from .primitives import generate_dh_keypair, perform_key_exchange


@dataclass
class Party:
    """A named participant (e.g. Alice or Bob) in a Diffie-Hellman exchange.

    Lifecycle:
        1. ``generate_keys(parameters)`` — create private/public key pair.
        2. ``compute_shared_secret(peer_public_key)`` — derive shared secret.
    """

    name: str
    private_key: DHPrivateKey | None = field(default=None, repr=False)
    public_key: DHPublicKey | None = field(default=None, repr=False)
    shared_secret: bytes | None = field(default=None, repr=False)

    def generate_keys(self, parameters: DHParameters) -> None:
        """Generate a fresh DH key pair from *parameters*."""
        self.private_key, self.public_key = generate_dh_keypair(parameters)

    def compute_shared_secret(self, peer_public_key: DHPublicKey) -> None:
        """Compute the shared secret from the peer's public key.

        Raises ``ValueError`` if ``generate_keys`` has not been called first.
        """
        if self.private_key is None:
            raise ValueError(
                f"{self.name} has no private key — call generate_keys() first."
            )
        self.shared_secret = perform_key_exchange(self.private_key, peer_public_key)

    # ------------------------------------------------------------------
    # Convenience properties for extracting raw integers (used by
    # the handshake to record hex values at each step).
    # ------------------------------------------------------------------

    @property
    def private_key_int(self) -> int | None:
        """The private key as a Python integer (the exponent x)."""
        if self.private_key is None:
            return None
        return self.private_key.private_numbers().x

    @property
    def public_key_int(self) -> int | None:
        """The public key as a Python integer (the value y = g^x mod p)."""
        if self.public_key is None:
            return None
        return self.public_key.public_numbers().y
