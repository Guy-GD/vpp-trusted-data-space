from secrets import token_hex


ALLOWED_ID_PREFIXES = frozenset(
    {
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
)


def new_id(prefix: str) -> str:
    """Generate a unique opaque ID with one of the frozen cross-module prefixes."""
    if prefix not in ALLOWED_ID_PREFIXES:
        allowed = ", ".join(sorted(ALLOWED_ID_PREFIXES))
        raise ValueError(f"unsupported ID prefix {prefix!r}; allowed prefixes: {allowed}")
    return f"{prefix}{token_hex(8)}"
