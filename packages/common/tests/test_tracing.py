from vpp_common.tracing import TRACE_HEADER, resolve_trace_id


def test_trace_header_name_is_frozen():
    assert TRACE_HEADER == "X-Trace-Id"


def test_resolve_trace_id_preserves_valid_incoming():
    assert resolve_trace_id("trace_existing") == "trace_existing"


def test_resolve_trace_id_preserves_prefix_only_value():
    assert resolve_trace_id("trace_") == "trace_"


def test_resolve_trace_id_generates_when_missing():
    generated = resolve_trace_id(None)
    assert generated.startswith("trace_")
    assert len(generated) > len("trace_")


def test_resolve_trace_id_replaces_invalid_incoming():
    assert resolve_trace_id("contains spaces").startswith("trace_")
    assert resolve_trace_id("not-trace-prefixed").startswith("trace_")
    assert resolve_trace_id("trace_" + "x" * 128).startswith("trace_")
