from dataclasses import dataclass


@dataclass(frozen=True)
class Certification:
    """Represents a cybersecurity certification entry."""

    id: int
    name: str
    provider: str
    url: str
    is_free: bool
    hands_on: bool


# Backward compatibility alias
FreeCertification = Certification
