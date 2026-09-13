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