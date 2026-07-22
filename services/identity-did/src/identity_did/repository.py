import re

from vpp_common import utc_now_iso

from .schemas import (
    AuthorizationRecord,
    DeviceRecord,
    StoredResult,
    SubjectRecord,
)


MOCK_PUBLIC_KEY = "bW9jay1wdWJsaWMta2V5"
_DEMO_SUBJECTS = (
    ("did:vpp:operator:001", "VPP operator", "operator"),
    (
        "did:vpp:load-aggregator:001",
        "Load aggregator",
        "load_aggregator",
    ),
    (
        "did:vpp:renewable-plant:001",
        "Renewable plant",
        "renewable_plant",
    ),
    ("did:vpp:storage:001", "Energy storage", "storage"),
)


class InMemoryRepository:
    def __init__(self) -> None:
        self.subjects: dict[str, SubjectRecord] = {}
        self.devices: dict[str, DeviceRecord] = {}
        self.authorizations: dict[str, AuthorizationRecord] = {}
        self.idempotency: dict[str, StoredResult] = {}
        self._subject_counters: dict[str, int] = {}
        self._device_counters: dict[str, int] = {}
        self._seed_demo_subjects()

    @staticmethod
    def slug(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")

    def next_subject_did(self, subject_type: str) -> str:
        return self._next_did(subject_type, self._subject_counters)

    def next_device_did(self, device_type: str) -> str:
        return self._next_did(device_type, self._device_counters)

    def _next_did(self, identity_type: str, counters: dict[str, int]) -> str:
        slug = self.slug(identity_type)
        next_number = counters.get(slug, 1)
        while True:
            candidate = f"did:vpp:{slug}:{next_number:03d}"
            next_number += 1
            if candidate not in self.subjects and candidate not in self.devices:
                counters[slug] = next_number
                return candidate

    def _seed_demo_subjects(self) -> None:
        for subject_did, name, subject_type in _DEMO_SUBJECTS:
            self.subjects[subject_did] = SubjectRecord(
                subjectDid=subject_did,
                name=name,
                type=subject_type,
                publicKey=MOCK_PUBLIC_KEY,
                status="active",
                createdAt=utc_now_iso(),
            )
