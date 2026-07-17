import pytest

from vpp_common.id_generator import ALLOWED_ID_PREFIXES, new_id


EXPECTED_PREFIXES = {
    "demo_",
    "batch_",
    "reading_",
    "asset_",
    "auth_",
    "fl_task_",
    "aggregate_",
    "global_model_v",
    "prediction_",
    "strategy_",
    "report_",
    "evt_",
    "tx_",
    "trace_",
}


def test_frozen_id_prefixes_are_complete():
    assert ALLOWED_ID_PREFIXES == frozenset(EXPECTED_PREFIXES)


@pytest.mark.parametrize("prefix", sorted(EXPECTED_PREFIXES))
def test_new_ids_use_requested_prefix(prefix):
    generated = new_id(prefix)
    assert generated.startswith(prefix)
    assert len(generated) > len(prefix)


def test_new_ids_are_unique():
    assert new_id("asset_") != new_id("asset_")


def test_unknown_id_prefix_is_rejected():
    with pytest.raises(ValueError, match="unsupported ID prefix"):
        new_id("unknown_")
