import os
import json
import logging
from typing import List, Dict, Any, Optional
import requests
from dotenv import load_dotenv
from groq import Groq

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("opsmind-agent")

# Load environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY", "")
HINDSIGHT_BASE_URL = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io").rstrip("/")
HINDSIGHT_BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "sre-incident-bank")

def get_hindsight_headers() -> Dict[str, str]:
    """Returns headers required for Vectorize Hindsight API calls."""
    return {
        "Authorization": f"Bearer {HINDSIGHT_API_KEY}",
        "Content-Type": "application/json"
    }

def is_mock_mode() -> bool:
    """Detect if placeholder/dummy API keys are configured."""
    return (
        not GROQ_API_KEY 
        or "your_" in GROQ_API_KEY.lower() 
        or not HINDSIGHT_API_KEY 
        or "your_" in HINDSIGHT_API_KEY.lower()
    )

# In-memory mock store for mock/fallback execution when keys are dummy
_MOCK_MEMORY_STORE: List[Dict[str, Any]] = [
    {
        "text": "Incident: INC-8102\nContext: Checkout service Kubernetes pod terminated with OOMKilled exit code 137. Pod memory spiked beyond 1.5Gi limit during evening flash sale.\nResolution: Root cause: unclosed gRPC client stream leak buffering payloads during high traffic. Remediation: deploy hotfix setting gRPC keepalive timeouts and restart deployment payment-svc.",
        "metadata": {"incident_id": "INC-8102", "type": "post_mortem"}
    },
    {
        "text": "Incident: INC-7940\nContext: PostgreSQL connection pool starvation with FATAL: remaining connection slots are reserved for non-replication superuser connections.\nResolution: Root cause: PgBouncer pool_mode set to session instead of transaction. Remediation: update configmap pgbouncer-config to pool_mode = transaction and execute reload.",
        "metadata": {"incident_id": "INC-7940", "type": "post_mortem"}
    },
    {
        "text": "Incident: INC-9210\nContext: Kafka consumer lag spike on order-events topic causing partition rebalance deadlock.\nResolution: Root cause: processing duration exceeded max.poll.interval.ms. Remediation: tune max.poll.interval.ms=600000 and reduce max.poll.records=250.",
        "metadata": {"incident_id": "INC-9210", "type": "post_mortem"}
    }
]

def ensure_bank_exists() -> bool:
    """Ensure the specified memory bank exists in Hindsight."""
    if is_mock_mode():
        return True
    url = f"{HINDSIGHT_BASE_URL}/v1/default/banks/{HINDSIGHT_BANK_ID}"
    try:
        res = requests.put(url, headers=get_hindsight_headers(), json={"name": "SRE Incident Bank"}, timeout=10)
        return res.status_code in (200, 201)
    except Exception as e:
        logger.warning(f"Could not verify/create bank {HINDSIGHT_BANK_ID}: {e}")
        return False

def retain_memory(incident_id: str, context: str, resolution: str) -> bool:
    """
    Persist post-mortem context and resolution into Vectorize Hindsight memory bank.
    Supports both live Vectorize Hindsight REST API (/v1/default/banks/{bank_id}/memories)
    and fallback mock mode.
    """
    full_text = f"Incident: {incident_id}\nContext: {context}\nResolution: {resolution}"
    metadata = {
        "incident_id": incident_id,
        "type": "post_mortem"
    }

    if is_mock_mode():
        logger.info(f"[Mock Mode] Storing incident {incident_id} in local memory store.")
        _MOCK_MEMORY_STORE.append({
            "text": full_text,
            "metadata": metadata
        })
        return True

    # Ensure bank is initialized
    ensure_bank_exists()

    # Vectorize Hindsight REST API: POST /v1/default/banks/{bank_id}/memories
    # Use async=True for fast, non-blocking ingestion
    url = f"{HINDSIGHT_BASE_URL}/v1/default/banks/{HINDSIGHT_BANK_ID}/memories"
    payload = {
        "async": True,
        "items": [
            {
                "content": full_text,
                "metadata": metadata
            }
        ]
    }

    try:
        response = requests.post(url, headers=get_hindsight_headers(), json=payload, timeout=15)
        if response.status_code in (200, 201, 202):
            logger.info(f"Successfully retained memory for {incident_id} in Hindsight.")
            return True
        else:
            logger.error(f"Hindsight retain failed [{response.status_code}]: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while connecting to Hindsight retain endpoint: {e}")
        return False

def recall_memory(query: str, top_k: int = 3) -> List[Any]:
    """
    Query Vectorize Hindsight memory bank to retrieve relevant historical post-mortems.
    Returns a list of memory strings or memory objects from results/memories.
    """
    if is_mock_mode():
        logger.info(f"[Mock Mode] Searching local mock store for query: {query[:50]}...")
        results = []
        q_lower = query.lower()
        for item in _MOCK_MEMORY_STORE:
            text = item.get("text", "")
            meta = item.get("metadata", {})
            score = 0.5
            if "oomkilled" in q_lower or "137" in q_lower or "grpc" in q_lower or "payment-svc" in q_lower:
                if "INC-8102" in text or "OOMKilled" in text:
                    score = 0.95
            elif "postgres" in q_lower or "pgbouncer" in q_lower or "connection" in q_lower or "slots" in q_lower:
                if "INC-7940" in text or "PostgreSQL" in text:
                    score = 0.92
            elif "kafka" in q_lower or "rebalance" in q_lower or "lag" in q_lower or "poll" in q_lower:
                if "INC-9210" in text or "Kafka" in text:
                    score = 0.91

            if score > 0.6:
                results.append({
                    "text": text,
                    "metadata": meta,
                    "similarity": score
                })

        if not results:
            results = [{
                "text": m.get("text", ""),
                "metadata": m.get("metadata", {}),
                "similarity": 0.70
            } for m in _MOCK_MEMORY_STORE[:top_k]]
        return results[:top_k]

    # Live Vectorize Hindsight REST API: POST /v1/default/banks/{bank_id}/memories/recall
    url = f"{HINDSIGHT_BASE_URL}/v1/default/banks/{HINDSIGHT_BANK_ID}/memories/recall"
    payload = {
        "query": query,
        "budget": "mid"
    }

    try:
        response = requests.post(url, headers=get_hindsight_headers(), json=payload, timeout=15)
        if response.status_code == 200:
            data = response.json()
            # Vectorize Hindsight returns {"results": [...]} or {"memories": [...]}
            raw_memories = data.get("results") or data.get("memories") or []
            normalized = []
            for item in raw_memories:
                if isinstance(item, dict):
                    scores = item.get("scores", {})
                    sim = scores.get("final") or scores.get("semantic") or 0.85
                    normalized.append({
                        "text": item.get("text", ""),
                        "metadata": item.get("metadata") or {},
                        "similarity": round(float(sim), 3) if isinstance(sim, (int, float)) else sim
                    })
                else:
                    normalized.append({"text": str(item), "metadata": {}, "similarity": 0.80})
            return normalized[:top_k]
        else:
            logger.warning(f"Hindsight recall returned status {response.status_code}: {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Error querying Hindsight recall endpoint: {e}")
        return []

def diagnose_incident(raw_log: str, use_memory: bool = True) -> Dict[str, Any]:
    """
    Diagnose an incident using Groq LLM inference, optionally augmented with Hindsight persistent memory.
    """
    recalled_memories: List[Any] = []
    
    if use_memory:
        recalled_memories = recall_memory(raw_log, top_k=3)

    # Build prompt instructions based on memory presence
    if not use_memory:
        system_prompt = (
            "You are OpsMind, a Senior Site Reliability Engineer (SRE). "
            "Perform a standard, generic SRE diagnosis based strictly on first principles and industry conventions. "
            "You DO NOT have access to internal company post-mortems or historical organizational context. "
            "Format your response with the following sections:\n"
            "### 1. Root Cause Analysis\n"
            "### 2. Actionable Mitigation Commands\n"
            "### 3. Memory Attribution\n"
            "State clearly in Memory Attribution that no historical memory was used."
        )
        user_prompt = f"Analyze this incident log/alert:\n```\n{raw_log}\n```"
    else:
        # Build context from memories
        memory_context_blocks = []
        for i, mem in enumerate(recalled_memories, 1):
            if isinstance(mem, dict):
                content = mem.get("text") or mem.get("content") or json.dumps(mem)
                meta = mem.get("metadata", {})
                inc_id = meta.get("incident_id", "Historical Record")
                sim = mem.get("similarity", "N/A")
                memory_context_blocks.append(f"[Memory #{i} | Incident {inc_id} | Similarity: {sim}]:\n{content}")
            else:
                memory_context_blocks.append(f"[Memory #{i}]:\n{str(mem)}")

        memories_text = "\n\n".join(memory_context_blocks) if memory_context_blocks else "No relevant historical incidents found."

        system_prompt = (
            "You are OpsMind, an autonomous, memory-augmented SRE Incident Response Agent powered by Vectorize Hindsight and Groq. "
            "You have access to historical organizational tribal knowledge and post-mortems retrieved from the Vectorize Hindsight memory bank.\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Deeply analyze the provided incident log.\n"
            "2. Cross-reference with the retrieved post-mortems below. If an exact match or highly similar architectural pattern exists, cite the specific historical Incident ID.\n"
            "3. Format your response into structured Markdown sections:\n"
            "### 1. Root Cause Analysis\n"
            "Pinpoint the technical failure mechanism, highlighting specific internal culprits discovered in past post-mortems if applicable.\n"
            "### 2. Actionable Mitigation Commands\n"
            "Provide copy-pasteable terminal commands (e.g., kubectl, psql, kafka-configs) to mitigate or fix the issue immediately.\n"
            "### 3. Memory Attribution\n"
            "Explicitly attribute the diagnosis to the recalled incident(s) from Vectorize Hindsight or note if it diverges from past incidents."
        )
        user_prompt = (
            f"--- RECALLED TRIBAL MEMORIES (VECTORIZE HINDSIGHT) ---\n"
            f"{memories_text}\n"
            f"------------------------------------------------------\n\n"
            f"--- CURRENT INCIDENT ALERT / RAW LOG ---\n"
            f"{raw_log}\n"
            f"----------------------------------------\n"
            f"Diagnose the incident, synthesize the tribal knowledge, and provide remediation."
        )

    # Perform LLM inference via Groq or fallback mock
    if is_mock_mode():
        logger.info("[Mock Mode] Generating synthetic SRE diagnosis.")
        if not use_memory:
            analysis = (
                "### 1. Root Cause Analysis\n"
                "The container exited with code 137, signifying that the Linux kernel Out-Of-Memory (OOM) killer terminated the process after exceeding pod memory resource limits.\n\n"
                "### 2. Actionable Mitigation Commands\n"
                "```bash\n"
                "# Inspect pod resource usage and events\n"
                "kubectl describe pod <pod-name> -n production\n"
                "# Scale or increase pod memory limits\n"
                "kubectl set resources deployment <deployment-name> --limits=memory=2Gi,cpu=1\n"
                "```\n\n"
                "### 3. Memory Attribution\n"
                "**Standard Reasoning**: No historical organizational memory was used. This diagnosis is based entirely on generic Kubernetes OOM exit code 137 documentation."
            )
        else:
            analysis = (
                "### 1. Root Cause Analysis\n"
                "The checkout service pod was terminated with **exit code 137 (OOMKilled)**. Cross-referencing our persistent tribal memory, this is **identical to incident INC-8102**: an unclosed gRPC client stream leak in `payment-svc` that buffers message payloads into memory under elevated traffic volumes, rapidly exhausting the pod's 1.5Gi memory ceiling.\n\n"
                "### 2. Actionable Mitigation Commands\n"
                "```bash\n"
                "# 1. Apply hotfix setting gRPC client keepalive timeouts and connection limits\n"
                "kubectl set env deployment/payment-svc GRPC_KEEPALIVE_TIMEOUT_MS=5000 GRPC_MAX_CONNECTION_AGE_MS=30000 -n production\n\n"
                "# 2. Perform rolling restart to flush buffered leak\n"
                "kubectl rollout restart deployment/payment-svc -n production\n\n"
                "# 3. Verify pod stabilization\n"
                "kubectl rollout status deployment/payment-svc -n production --watch\n"
                "```\n\n"
                "### 3. Memory Attribution\n"
                "**Vectorize Hindsight Memory Attribution**: Diagnosed via direct correlation with historical post-mortem **INC-8102** (similarity: 0.95). The root cause (unclosed gRPC client stream leak) and specific remediation were directly recalled from internal organizational memory, preventing redundant triage."
            )
        
        return {
            "analysis": analysis,
            "recalled_memories": recalled_memories,
            "memory_used": use_memory
        }

    # Live Groq API execution
    try:
        client = Groq(api_key=GROQ_API_KEY)
        models_to_try = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]
        response = None
        for model in models_to_try:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2,
                    max_tokens=1500
                )
                if response:
                    logger.info(f"Groq inference succeeded using model: {model}")
                    break
            except Exception as e:
                logger.warning(f"Groq model {model} failed, trying next fallback: {e}")
                continue

        if not response:
            raise RuntimeError("All configured Groq models failed to return a response.")

        analysis = response.choices[0].message.content
        return {
            "analysis": analysis,
            "recalled_memories": recalled_memories,
            "memory_used": use_memory
        }
    except Exception as e:
        logger.error(f"Groq inference failed: {e}")
        return {
            "analysis": f"### Error in SRE Agent Inference\nFailed to invoke Groq API: {str(e)}",
            "recalled_memories": recalled_memories,
            "memory_used": use_memory
        }
