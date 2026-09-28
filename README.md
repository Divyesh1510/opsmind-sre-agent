# OpsMind — Memory-Augmented SRE Incident Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Memory Layer](https://img.shields.io/badge/Memory-Vectorize%20Hindsight-8A2BE2.svg)](https://hindsight.vectorize.io/)
[![Inference](https://img.shields.io/badge/Inference-Groq%20Cloud-F55036.svg)](https://groq.com/)
[![Technical Article](https://img.shields.io/badge/Article-Medium-black.svg?logo=medium)](https://medium.com/@divyeshatla/eliminating-mttr-with-persistent-agent-memory-how-we-built-opsmind-using-vectorize-hindsight-fd5fe16848cc)

> **Eliminating Mean Time to Resolution (MTTR) by converting stateless crash diagnosis into persistent, memory-augmented site reliability engineering.**

📖 **Deep-Dive Technical Case Study:**  
[Eliminating MTTR with Persistent Agent Memory: How We Built OpsMind Using Vectorize Hindsight](https://medium.com/@divyeshatla/eliminating-mttr-with-persistent-agent-memory-how-we-built-opsmind-using-vectorize-hindsight-fd5fe16848cc)

---

## 🎯 Problem Statement & Solution

### The SRE Amnesia Problem
Site Reliability Engineering teams spend up to 40% of their on-call rotations debugging recurring failures. During critical production outages, post-mortems, temporary configuration workarounds, and root-cause analyses (RCAs) get siloed across closed Jira tickets, Slack threads, and tribal knowledge.

When engineers feed crash dumps to stateless LLMs, the models fail:
* **Zero Context:** They lack visibility into cluster topology, past commit regressions, and previous post-mortems.
* **Generic Advice:** They suggest basic troubleshooting steps (e.g., *"increase resource limits"*, *"restart pods"*) rather than root causes.
* **Downtime Expansion:** Teams spend 30–45 minutes of trial and error for issues that were solved weeks prior[cite: 2].

### The OpsMind Solution
**OpsMind** couples high-speed LLM inference (**Groq**) with long-term persistent agent memory (**Vectorize Hindsight**) to establish an autonomous incident response lifecycle[cite: 2]:
1. **Semantic Recall:** Ingests raw stack traces and queries Vectorize Hindsight (`/recall`) for historical post-mortems with relevance scoring[cite: 1, 3].
2. **Attributed Diagnosis:** Identifies recurring failure mechanisms (e.g., unclosed client streams, PgBouncer pooling bugs) and generates actionable `kubectl` fixes and code-level patches[cite: 4, 5].
3. **Closed-Loop Retention:** Automatically persists new incident resolutions back into Hindsight (`/retain`) so institutional knowledge compounds over time[cite: 1, 6].

---

## ⚡ The Memory Impact: Before vs. After

| Metric / Capability | Stateless LLM Baseline | OpsMind + Vectorize Hindsight |
| :--- | :--- | :--- |
| **Context Awareness** | Generic / Zero memory of previous outages[cite: 2] | Semantic retrieval of matching historical post-mortems[cite: 1, 3] |
| **Root Cause Accuracy** | Surface-level advice (*"check pod metrics"*)[cite: 2] | Exact architectural failure pinned (e.g., INC-8102 gRPC stream leak)[cite: 4] |
| **Actionable Output** | Theoretical steps[cite: 2] | Targeted `kubectl` commands, configmap edits, and code diffs[cite: 4, 5] |
| **Institutional Learning** | Lost on session close[cite: 2] | Persisted into long-term memory via `/retain`[cite: 1, 6] |
| **Estimated MTTR** | ~40–60 minutes[cite: 2] | **~4–14 seconds (78% reduction)** |

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    A[Incoming Alert / Stack Trace] --> B[OpsMind Ingestion Layer]
    B --> C{Memory Recall Enabled?}
    C -->|Yes| D[Vectorize Hindsight Engine: /recall]
    C -->|No| E[Stateless LLM Baseline]
    D -->|Semantic Match & Scoring| F[(Persistent Memory Bank)]
    F -->|Historical Post-Mortems & RCAs| G[Context-Injected System Prompt]
    G --> H[Groq Inference Engine: qwen-2.5-32b]
    E --> H
    H --> I[Attributed Diagnosis & Mitigation Plan]
    I --> J[Simulate Runbook Execution: Dry Run]
    I --> K[Closed-Loop Learning: /retain]
    K -->|Commit New Resolution| F
