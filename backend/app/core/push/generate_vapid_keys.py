"""One-off CLI to print a fresh VAPID key pair for web push.

Usage: python -m app.core.push.generate_vapid_keys
Copy the printed values into VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY in .env.
"""

import base64

from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from py_vapid import Vapid02


def generate_vapid_keys() -> tuple[str, str]:
    vapid = Vapid02()
    vapid.generate_keys()

    raw_public = vapid.public_key.public_bytes(
        encoding=Encoding.X962,
        format=PublicFormat.UncompressedPoint,
    )
    public_key = base64.urlsafe_b64encode(raw_public).rstrip(b"=").decode()

    raw_private = vapid.private_key.private_numbers().private_value.to_bytes(32, "big")
    private_key = base64.urlsafe_b64encode(raw_private).rstrip(b"=").decode()

    return public_key, private_key


if __name__ == "__main__":
    public_key, private_key = generate_vapid_keys()
    print(f"VAPID_PUBLIC_KEY={public_key}")
    print(f"VAPID_PRIVATE_KEY={private_key}")
