import logging
from agent import retain_memory, is_mock_mode

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("seed_data")

HISTORICAL_INCIDENTS = [
    {
        "incident_id": "INC-8102",
        "context": (
            "Checkout service Kubernetes pod terminated with OOMKilled exit code 137. "
            "Pod memory spiked beyond 1.5Gi limit during high-traffic evening flash sale. "
            "Stack trace showed repeated gRPC transport buffering and goroutine leakage."
        ),
        "resolution": (
            "Root cause: unclosed gRPC client stream leak buffering payloads during high traffic. "
            "Remediation: deploy hotfix setting gRPC keepalive timeouts and restart deployment payment-svc. "
            "Command: kubectl set env deployment/payment-svc GRPC_KEEPALIVE_TIMEOUT_MS=5000 && "
            "kubectl rollout restart deployment/payment-svc -n production."
        )
    },
    {
        "incident_id": "INC-7940",
        "context": (
            "PostgreSQL connection pool starvation with FATAL: remaining connection slots are reserved "
            "for non-replication superuser connections. Frontend checkout and catalog services returned HTTP 503."
        ),
        "resolution": (
            "Root cause: PgBouncer pool_mode set to session instead of transaction under high concurrency. "
            "Remediation: update configmap pgbouncer-config to pool_mode = transaction and execute reload. "
            "Command: kubectl patch configmap pgbouncer-config -p '{\"data\":{\"pool_mode\":\"transaction\"}}' && "
            "kubectl exec -it deploy/pgbouncer -- pkill -HUP pgbouncer."
        )
    },
    {
        "incident_id": "INC-9210",
        "context": (
            "Kafka consumer lag spike on order-events topic causing partition rebalance deadlock. "
            "Consumer group rebalanced continuously and stopped consuming offsets."
        ),
        "resolution": (
            "Root cause: processing duration exceeded max.poll.interval.ms due to downstream database latency. "
            "Remediation: tune max.poll.interval.ms=600000 and reduce max.poll.records=250. "
            "Command: kubectl set env deployment/order-consumer MAX_POLL_INTERVAL_MS=600000 MAX_POLL_RECORDS=250."
        )
    }
]

def seed_hindsight_memory():
    """Iterate through historical incidents and seed them into Hindsight."""
    mode_str = "MOCK / FALLBACK MODE" if is_mock_mode() else "LIVE VECTORIZE HINDSIGHT"
    print("=" * 65)
    print(f"  OpsMind Seeder: Ingesting Historical Post-Mortems ({mode_str})")
    print("=" * 65)

    success_count = 0
    total = len(HISTORICAL_INCIDENTS)

    for inc in HISTORICAL_INCIDENTS:
        inc_id = inc["incident_id"]
        print(f"\n[+] Seeding Incident {inc_id}...")
        status = retain_memory(
            incident_id=inc_id,
            context=inc["context"],
            resolution=inc["resolution"]
        )
        if status:
            print(f"    [OK] SUCCESS: {inc_id} successfully indexed in Hindsight.")
            success_count += 1
        else:
            print(f"    [ERR] FAILED: Could not index {inc_id}.")

    print("\n" + "=" * 65)
    print(f"Seeding Complete: {success_count}/{total} post-mortems persisted to Hindsight.")
    print("=" * 65)

if __name__ == "__main__":
    seed_hindsight_memory()
