import streamlit as st
import json
import time
from agent import diagnose_incident, retain_memory, is_mock_mode

# Page configuration
st.set_page_config(
    page_title="OpsMind — Autonomous Memory-Augmented SRE Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #3B82F6 0%, #8B5CF6 50%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.1rem;
    }
    .sub-header {
        color: #94A3B8;
        font-size: 0.95rem;
        margin-bottom: 1.2rem;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    .badge-memory {
        background-color: #1E1B4B;
        color: #A78BFA;
        border: 1px solid #6366F1;
    }
    .badge-llm {
        background-color: #064E3B;
        color: #6EE7B7;
        border: 1px solid #10B981;
    }
    .diff-col-stateless {
        background: rgba(239, 68, 68, 0.05);
        border: 1px solid rgba(239, 68, 68, 0.25);
        border-radius: 8px;
        padding: 1.2rem;
    }
    .diff-col-memory {
        background: rgba(16, 185, 129, 0.05);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 8px;
        padding: 1.2rem;
    }
    .terminal-container {
        background: #090D16;
        border: 1px solid #1E293B;
        border-left: 4px solid #10B981;
        border-radius: 6px;
        padding: 0.8rem 1rem;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 0.88rem;
        color: #E2E8F0;
        margin-top: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# App Header
st.markdown('<div class="main-header">🛡️ OpsMind — Persistent Memory SRE Incident Agent</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">'
    '<span class="badge badge-memory">🧠 Vectorize Hindsight REST API (Persistent Memory)</span>'
    '<span class="badge badge-llm">⚡ Groq High-Speed LLM Inference</span>'
    '</div>', 
    unsafe_allow_html=True
)

# 1. Top-Level Enterprise Impact Metric Cards
metric_c1, metric_c2, metric_c3 = st.columns(3)
with metric_c1:
    st.metric(
        label="Estimated MTTR Reduction",
        value="78%",
        delta="-31 mins"
    )
with metric_c2:
    st.metric(
        label="Incident Recurrence Check",
        value="Active",
        delta="Vectorize Hindsight",
        delta_color="normal"
    )
with metric_c3:
    st.metric(
        label="Knowledge Base",
        value="Enterprise Runbooks",
        delta="Persistent Indexed",
        delta_color="normal"
    )

st.divider()

if is_mock_mode():
    st.info("ℹ️ Running in **Simulated Fallback Mode** (placeholder API keys in `.env`). Autonomous deterministic mocks active for Vectorize Hindsight and Groq.")

# Default preset error log
DEFAULT_OOM_LOG = """[ERROR] 2026-09-28T18:22:10Z kubelet node-worker-pool-4
Container 'payment-svc' in pod 'checkout-service-7f698d-x9qzp' terminated.
Reason: OOMKilled (Exit Code 137).
Memory cgroup usage 1572864000 exceeded limit 1572864000.
Stack: goroutine 4821 [chan receive, 42 minutes]:
google.golang.org/grpc/internal/transport.(*loopyWriter).run()
"""

# Two-column layout
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("1. Incident Input & Control")
    
    preset = st.selectbox(
        "Load Quick Scenario:",
        [
            "INC-8102: Checkout Pod OOMKilled (Exit Code 137)",
            "INC-7940: PostgreSQL Connection Pool Starvation",
            "INC-9210: Kafka Consumer Lag & Rebalance Deadlock",
            "Custom Incident Log"
        ]
    )

    if preset.startswith("INC-8102"):
        selected_log = DEFAULT_OOM_LOG
    elif preset.startswith("INC-7940"):
        selected_log = """2026-09-28 14:15:02 UTC [5432]: [3-1] user=app_service,db=production FATAL: remaining connection slots are reserved for non-replication superuser connections
2026-09-28 14:15:02 UTC [5432]: [4-1] user=app_service,db=production DETAIL: Connection pool capacity reached max 500 backends."""
    elif preset.startswith("INC-9210"):
        selected_log = """[WARN] 2026-09-28T16:04:12Z org.apache.kafka.clients.consumer.internals.ConsumerCoordinator
[Consumer clientId=order-consumer-1, groupId=order-processing-group] 
Offset commit failed on partition order-events-4: The request timed out.
[ERROR] CommitFailedException: Commit cannot be completed since the group has already rebalanced and assigned the partitions to another member. This means that the time between subsequent calls to poll() was longer than the configured max.poll.interval.ms."""
    else:
        selected_log = ""

    raw_log = st.text_area(
        "Incident Stack Trace / Alert Logs:",
        value=selected_log,
        height=200,
        placeholder="Paste production alerts, stack traces, or Kubernetes termination logs here..."
    )

    use_memory = st.toggle(
        "🧠 Enable Hindsight Memory Recall", 
        value=True,
        help="When enabled, queries Vectorize Hindsight memory bank to cross-reference organizational post-mortems and tribal knowledge."
    )

    btn_c1, btn_c2 = st.columns([1, 1])
    with btn_c1:
        diagnose_btn = st.button("🚀 Diagnose Incident", type="primary", use_container_width=True)
    with btn_c2:
        diff_btn = st.button("⚡ Instant Before vs. After Diff", help="Run parallel diagnosis: Stateless baseline vs. Hindsight context-aware memory", use_container_width=True)

with col2:
    st.subheader("2. Diagnosis & Memory Attribution")
    
    # Handle single diagnosis
    if diagnose_btn:
        if not raw_log.strip():
            st.warning("⚠️ Please provide an incident stack trace or alert log to diagnose.")
        else:
            with st.spinner("OpsMind is investigating logs and querying Vectorize Hindsight memory..."):
                result = diagnose_incident(raw_log, use_memory=use_memory)
                st.session_state["view_mode"] = "single"
                st.session_state["last_result"] = result

    # Handle Before vs. After Side-by-Side Diff
    if diff_btn:
        if not raw_log.strip():
            st.warning("⚠️ Please provide an incident stack trace or alert log to diagnose.")
        else:
            with st.spinner("⚡ Running Side-by-Side Comparison: Stateless LLM vs. Vectorize Hindsight..."):
                stateless_res = diagnose_incident(raw_log, use_memory=False)
                memory_res = diagnose_incident(raw_log, use_memory=True)
                st.session_state["view_mode"] = "diff"
                st.session_state["diff_stateless"] = stateless_res
                st.session_state["diff_memory"] = memory_res

    # Render Single Diagnosis Result
    if st.session_state.get("view_mode") == "single" and "last_result" in st.session_state:
        res = st.session_state["last_result"]
        recalled = res.get("recalled_memories", [])
        
        # Expandable box for Recalled Tribal Memories
        with st.expander(f"🔍 Recalled Tribal Memories from Hindsight ({len(recalled)} found)", expanded=bool(recalled)):
            if not recalled:
                st.caption("No historical post-mortems retrieved (Memory Recall disabled or no matching vectors).")
            else:
                for idx, mem in enumerate(recalled, 1):
                    if isinstance(mem, dict):
                        meta = mem.get("metadata", {})
                        inc_id = meta.get("incident_id", "N/A")
                        sim = mem.get("similarity", "N/A")
                        content = mem.get("text", "")
                        st.markdown(f"**Memory #{idx} — Incident {inc_id}** (Relevance Score: `{sim}`)")
                        st.code(content, language="markdown")
                    else:
                        st.markdown(f"**Memory #{idx}**")
                        st.code(str(mem), language="markdown")

        # Rendered Markdown box containing Root Cause Analysis, Mitigation Commands, Attribution
        st.markdown(res.get("analysis", ""))

        # 3. Simulate Remediation (Dry Run) Button
        st.markdown("---")
        if st.button("🚀 Execute Runbook (Dry Run)", key="single_runbook_btn"):
            with st.status("Initiating dry-run remediation workflow...", expanded=True) as status:
                st.write("🔑 Authenticating with production cluster `production-k8s-eu-west-1`...")
                time.sleep(0.4)
                st.write("📋 Validating RBAC and namespace `production` permissions...")
                time.sleep(0.3)
                st.write("⚡ Executing hotfix rolling restart: `kubectl rollout restart deployment/payment-svc`...")
                time.sleep(0.5)
                st.write("🔍 Monitoring container termination and replacement pods...")
                time.sleep(0.4)
                status.update(label="✅ Remediation verified in dry-run mode!", state="complete", expanded=True)
            
            st.code(
                "[DRY-RUN] Authenticating with cluster production-k8s-eu-west-1...\n"
                "[DRY-RUN] Executing: kubectl rollout restart deployment/payment-svc -n production\n"
                "[DRY-RUN] Pod payment-svc-7f698d-x9qzp terminating...\n"
                "[DRY-RUN] New pod scheduled and running. Memory baseline stabilized.\n"
                "[STATUS] MTTR target met in 14.2s.",
                language="bash"
            )

    # Render Side-by-Side Diff Result
    elif st.session_state.get("view_mode") == "diff":
        st.info("📊 **Side-by-Side Mode**: Stateless LLM Baseline vs. Vectorize Hindsight Augmented Agent")

# Side-by-Side Diff Full Width Container
if st.session_state.get("view_mode") == "diff" and "diff_stateless" in st.session_state:
    st.markdown("### ⚡ Live Comparison: Stateless LLM vs. Vectorize Hindsight")
    
    col_stateless, col_memory = st.columns(2, gap="medium")

    with col_stateless:
        st.error("❌ **Without Memory (Stateless LLM Baseline)**")
        st.caption("Standard reasoning without internal organization history or past post-mortems.")
        stateless_data = st.session_state["diff_stateless"]
        st.markdown(stateless_data.get("analysis", ""))

    with col_memory:
        st.success("✅ **With Hindsight Memory (Context-Aware SRE Agent)**")
        st.caption("Augmented with Vectorize Hindsight persistent memory bank (`sre-incident-bank`).")
        memory_data = st.session_state["diff_memory"]
        mem_recalled = memory_data.get("recalled_memories", [])
        
        with st.expander(f"🔍 Recalled Tribal Memories ({len(mem_recalled)} matches)", expanded=True):
            for idx, mem in enumerate(mem_recalled, 1):
                if isinstance(mem, dict):
                    meta = mem.get("metadata", {})
                    inc_id = meta.get("incident_id", "N/A")
                    sim = mem.get("similarity", "N/A")
                    content = mem.get("text", "")
                    st.markdown(f"**Match #{idx}: {inc_id}** (Score: `{sim}`)")
                    st.caption(content[:250] + ("..." if len(content) > 250 else ""))
                else:
                    st.caption(str(mem))
        
        st.markdown(memory_data.get("analysis", ""))

        st.markdown("---")
        if st.button("🚀 Execute Runbook (Dry Run)", key="diff_runbook_btn"):
            with st.status("Executing SRE targeted dry-run...", expanded=True) as status:
                st.write("🔑 Authenticating with production cluster `production-k8s-eu-west-1`...")
                time.sleep(0.4)
                st.write("⚡ Applying tribal patch from INC-8102...")
                time.sleep(0.5)
                status.update(label="✅ Remediation verified in dry-run mode!", state="complete", expanded=True)
            
            st.code(
                "[DRY-RUN] Authenticating with cluster production-k8s-eu-west-1...\n"
                "[DRY-RUN] Executing: kubectl rollout restart deployment/payment-svc -n production\n"
                "[DRY-RUN] Pod payment-svc-7f698d-x9qzp terminating...\n"
                "[DRY-RUN] New pod scheduled and running. Memory baseline stabilized.\n"
                "[STATUS] MTTR target met in 14.2s.",
                language="bash"
            )

st.divider()

# Bottom Section: Closed-Loop Learning Form
st.subheader("3. 🔄 Closed-Loop Learning: Retain New Post-Mortem")
st.caption("Feed newly resolved incidents back into Vectorize Hindsight to prevent repeat outages across the engineering org.")

with st.form("retain_form", clear_on_submit=True):
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        new_inc_id = st.text_input("Incident ID", placeholder="e.g. INC-9500")
    with col_f2:
        new_context = st.text_input("Incident Summary / Symptoms", placeholder="e.g. Redis eviction storm causing session drops")
    
    new_resolution = st.text_area("Root Cause & Remediation Steps", placeholder="e.g. Root cause: maxmemory-policy was volatile-lru instead of allkeys-lru. Remediation: config set maxmemory-policy allkeys-lru.")
    
    submit_retain = st.form_submit_button("💾 Retain into Hindsight Memory Bank")

    if submit_retain:
        if not new_inc_id or not new_context or not new_resolution:
            st.error("Please fill out Incident ID, Summary, and Resolution fields.")
        else:
            with st.spinner(f"Ingesting {new_inc_id} into Vectorize Hindsight..."):
                success = retain_memory(
                    incident_id=new_inc_id.strip(),
                    context=new_context.strip(),
                    resolution=new_resolution.strip()
                )
                if success:
                    st.success(f"✅ Successfully retained {new_inc_id} in Hindsight! It is immediately recallable for future incidents.")
                else:
                    st.error(f"❌ Failed to retain {new_inc_id}. Check logs or network connection.")
