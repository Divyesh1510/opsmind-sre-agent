import pytest
from agent import retain_memory, recall_memory, diagnose_incident, is_mock_mode

SAMPLE_OOM_LOG = """
[ERROR] 2026-09-28T18:22:10Z kubelet node-worker-pool-4
Container 'payment-svc' in pod 'checkout-service-7f698d-x9qzp' terminated.
Reason: OOMKilled (Exit Code 137).
Memory cgroup usage 1572864000 exceeded limit 1572864000.
Stack: goroutine 4821 [chan receive, 42 minutes]:
google.golang.org/grpc/internal/transport.(*loopyWriter).run()
"""

SAMPLE_PG_LOG = """
2026-09-28 14:15:02 UTC [5432]: [3-1] user=app_service,db=production FATAL: remaining connection slots are reserved for non-replication superuser connections
2026-09-28 14:15:02 UTC [5432]: [4-1] user=app_service,db=production DETAIL: Connection pool capacity reached max 500 backends.
"""

def test_hindsight_retain():
    """Verify that persisting a test post-mortem returns a successful status."""
    res = retain_memory(
        incident_id="INC-TEST-001",
        context="Test canary pod restarted due to ephemeral disk exhaustion in logging sidecar.",
        resolution="Added log rotation cronjob and trimmed stdout verbosity."
    )
    assert res is True, "Expected retain_memory to return True"

def test_hindsight_recall():
    """Verify that querying an error log similar to INC-8102 returns relevant memories from Hindsight."""
    memories = recall_memory(SAMPLE_OOM_LOG, top_k=2)
    assert isinstance(memories, list), "Expected recall_memory to return a list"
    assert len(memories) > 0, "Expected at least one recalled memory for OOM log"
    
    # Check that either incident ID or relevant text exists in the recalled memories
    found_relevant = False
    for mem in memories:
        content = mem.get("text", "") if isinstance(mem, dict) else str(mem)
        meta = mem.get("metadata", {}) if isinstance(mem, dict) else {}
        if "8102" in str(meta) or "OOMKilled" in content or "gRPC" in content or "8102" in content:
            found_relevant = True
            break
    assert found_relevant, f"Recalled memories did not contain expected INC-8102 or OOM context: {memories}"

def test_stateless_vs_stateful_diagnosis():
    """Test both stateless (use_memory=False) and stateful (use_memory=True) diagnosis."""
    # Stateless test
    stateless_result = diagnose_incident(SAMPLE_OOM_LOG, use_memory=False)
    assert stateless_result["memory_used"] is False
    assert len(stateless_result["recalled_memories"]) == 0
    assert "Root Cause Analysis" in stateless_result["analysis"]
    assert "Actionable Mitigation Commands" in stateless_result["analysis"]
    assert "Memory Attribution" in stateless_result["analysis"]

    # Stateful test
    stateful_result = diagnose_incident(SAMPLE_OOM_LOG, use_memory=True)
    assert stateful_result["memory_used"] is True
    assert len(stateful_result["recalled_memories"]) > 0
    assert "Root Cause Analysis" in stateful_result["analysis"]
    assert "Actionable Mitigation Commands" in stateful_result["analysis"]
    assert "Memory Attribution" in stateful_result["analysis"]
    
    # Verify that tribal knowledge (INC-8102 or gRPC client leak) is incorporated
    analysis_text = stateful_result["analysis"]
    assert ("8102" in analysis_text or "gRPC" in analysis_text or "leak" in analysis_text or "payment-svc" in analysis_text), (
        "Expected stateful diagnosis to incorporate specific tribal knowledge from INC-8102"
    )

if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
