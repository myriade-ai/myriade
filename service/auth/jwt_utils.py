"""
JWT utilities for secure token verification
"""

import logging
from typing import Dict, Optional

import jwt
import requests
from cryptography.hazmat.primitives import serialization

from config import AUTH_CLIENT_ID, ENV, INFRA_URL

logger = logging.getLogger(__name__)


class JWTVerificationError(Exception):
    """Raised when JWT verification fails"""

    pass


def get_public_key_from_jwks(token: str) -> Optional[str]:
    """
    Fetch public key from JWKS endpoint based on the token's kid claim.

    Args:
        token: JWT token to get kid from

    Returns:
        Public key string or None if not found
    """
    try:
        # Get kid from token header without verification
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        if not kid:
            logger.warning("Token missing 'kid' claim in header")
            return None

        # Fetch JWKS
        response = requests.get(INFRA_URL + "/auth/jwks", timeout=10)
        response.raise_for_status()
        jwks = response.json()

        # Find matching key
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                # Convert JWK to PEM format
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                return (
                    public_key.public_key()
                    .public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo,
                    )
                    .decode()
                )

        logger.warning(f"No matching key found for kid: {kid}")
        return None

    except Exception as e:
        logger.error(f"Failed to fetch public key from JWKS: {str(e)}")
        return None


def verify_jwt_token(token: str, require_verification: bool = None) -> Dict:
    """
    Verify JWT token with proper signature validation.

    Args:
        token: JWT token to verify
        require_verification: Force verification on/off, defaults to production env

    Returns:
        Decoded token payload

    Raises:
        JWTVerificationError: If token verification fails
    """
    if require_verification is None:
        require_verification = ENV == "production"

    try:
        if not require_verification:
            # Development mode - decode without verification but log warning
            logger.warning(
                "JWT signature verification disabled - development mode only"
            )
            decoded = jwt.decode(token, options={"verify_signature": False})
            return decoded

        public_key = get_public_key_from_jwks(token)

        if not public_key:
            raise JWTVerificationError(
                "No public key available for JWT verification. "
                "Please configure JWT_PUBLIC_KEY or JWKS_URL environment variables."
            )

        # Verify token with public key
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=AUTH_CLIENT_ID,  # Verify audience matches our client
            options={
                "verify_signature": True,
                "verify_exp": True,  # Verify expiration
                "verify_aud": bool(
                    AUTH_CLIENT_ID
                ),  # Verify audience if we have client_id
                "require": ["exp", "iat", "sub"],  # Require essential claims
            },
        )

        logger.info("JWT token verified successfully")
        return decoded

    except jwt.ExpiredSignatureError as e:
        raise JWTVerificationError("Token has expired") from e
    except jwt.InvalidAudienceError as e:
        raise JWTVerificationError("Token audience mismatch") from e
    except jwt.InvalidSignatureError as e:
        raise JWTVerificationError("Invalid token signature") from e
    except jwt.InvalidTokenError as e:
        raise JWTVerificationError(f"Invalid token: {str(e)}") from e
    except Exception as e:
        logger.error(f"JWT verification failed: {str(e)}")
        raise JWTVerificationError(f"Token verification failed: {str(e)}") from e
