"""Typed errors mapped to CLI exit codes."""


class NostrobeError(Exception):
    """Base error for expected operational failures."""


class DecodeError(NostrobeError):
    """Media probing, decoding or encoding failed."""


class UnsupportedMediaError(NostrobeError):
    """Media is outside the supported SDR scope."""


class VerifierFailedError(NostrobeError):
    """Mitigated output failed verification."""


class ProfileError(NostrobeError):
    """An unknown or invalid profile was requested."""
