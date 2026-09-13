from pathlib import Path

from bot.security import hash_password, verify_password
from bot.storage import CertificationStore


def test_password_hash_round_trip() -> None:
    encoded = hash_password("correct horse")

    assert verify_password("correct horse", encoded)
    assert not verify_password("wrong horse", encoded)
    assert encoded != "correct horse"


def test_certification_store_supports_crud(tmp_path: Path) -> None:
    store = CertificationStore(tmp_path / "bot.sqlite3")
    certification_id = store.add(
        "Security+", "CompTIA", "https://example.test", hands_on=True
    )

    certification = store.find(certification_id)
    assert certification.name == "Security+"
    assert certification.provider == "CompTIA"
    assert certification.url == "https://example.test"
    assert certification.is_free is True
    assert certification.hands_on is True
    assert store.edit(certification_id, is_free=False, hands_on=False)
    certification = store.find(certification_id)
    assert certification.is_free is False
    assert certification.hands_on is False
    assert store.remove(certification_id)
    assert store.find(certification_id) is None


def test_format_certification() -> None:
    from bot.certifications import format_certification
    from bot.storage import Certification

    free_cert = Certification(
        id=1,
        name="Intro to Cyber",
        provider="Cisco",
        url="https://cisco.test",
        is_free=True,
        hands_on=False,
    )
    assert format_certification(free_cert) == "1. Cisco: [Intro to Cyber](https://cisco.test) (Free & Theoretical)"

    paid_cert = Certification(
        id=2,
        name="OSCP",
        provider="OffSec",
        url="https://offsec.test",
        is_free=False,
        hands_on=True,
    )
    assert format_certification(paid_cert) == "2. OffSec: [OSCP](https://offsec.test) (Paid & Hands-on)"


def test_split_message_respects_discord_limit() -> None:
    from bot.commands.certifications import split_message

    chunks = split_message("first\nsecond\nthird", limit=13)

    assert chunks == ["first\nsecond\n", "third"]
    assert all(len(chunk) <= 13 for chunk in chunks)


def test_split_message_splits_oversized_line() -> None:
    from bot.commands.certifications import split_message

    chunks = split_message("x" * 7, limit=3)

    assert chunks == ["xxx", "xxx", "x"]
