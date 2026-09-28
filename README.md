# OpsMind — Memory-Augmented SRE Incident Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Memory](https://img.shields.io/badge/Memory-Vectorize%20Hindsight-8A2BE2.svg)](https://hindsight.vectorize.io/)
[![Inference](https://img.shields.io/badge/Inference-Groq%20Cloud-F55036.svg)](https://groq.com/)
[![Technical Article](https://img.shields.io/badge/Article-Medium-black.svg?logo=medium)](https://medium.com/@divyeshatla/eliminating-mttr-with-persistent-agent-memory-how-we-built-opsmind-using-vectorize-hindsight-fd5fe16848cc)

> **Eliminating production downtime by transforming stateless incident triage into persistent, memory-augmented site reliability engineering.**

📖 **Deep-Dive Technical Case Study:**  
[Eliminating MTTR with Persistent Agent Memory: How We Built OpsMind Using Vectorize Hindsight](https://medium.com/@divyeshatla/eliminating-mttr-with-persistent-agent-memory-how-we-built-opsmind-using-vectorize-hindsight-fd5fe16848cc)

---

## 🎯 Problem Statement & Solution

### The SRE Amnesia Problem
Engineering teams lose thousands of dollars per minute during critical outages. The primary driver of elevated **Mean Time to Resolution (MTTR)** is organizational amnesia: past post-mortems, root cause analyses (RCAs), and temporary mitigations remain scattered across closed Jira tickets, Slack threads, and tribal knowledge. 

When engineers feed crash dumps to stateless LLMs, the models fail:
* They lack cluster topology and institutional context.
* They suggest generic, textbook remediation steps (e.g., *"increase resource limits"*, *"restart pods"*).
* They force on-call engineers through 30–45 minutes of trial and error for recurring incidents.

### The OpsMind Solution
**OpsMind** introduces persistent, cross-session agent memory via **Vectorize Hindsight** coupled with high-speed LLM inference via **Groq**. OpsMind forms a closed-loop operational lifecycle:
1. **Semantic Recall:** Cross-references incoming crash traces with historical post-mortems.
2. **Attributed Diagnosis:** Generates actionable, cluster-specific mitigations and Go/Kubernetes patches.
3. **Closed-Loop Retention:** Automatically commits new outage resolutions back into the persistent memory bank to ensure no incident is solved twice.

---

## ⚡ The Memory Impact: Before vs. After

| Metric / Capability | Stateless LLM Baseline | OpsMind + Vectorize Hindsight |
| :--- | :--- | :--- |
| **Context Awareness** | Generic / Zero memory of past failures | Semantic retrieval of identical past incidents |
| **Diagnosis Quality** | Textbook advice (*"check pod metrics, inspect logs"*) | Exact failure pattern pinpointed (e.g., unclosed gRPC streams, PgBouncer pool modes) |
| **Actionable Mitigation** | Theoretical steps | Exact `kubectl` commands, configuration patches, and code fixes |
| **Institutional Learning** | Discarded upon conversation close | Persisted into long-term memory via `/retain` |
| **Estimated MTTR** | ~40–60 minutes | **~4–14 seconds (78% reduction)** |

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    A[Incoming Stack Trace / Alert Log] --> B{Hindsight Memory Recall}
    B -->|Query Vectorize Hindsight API| C[(Persistent Memory Bank)]
    C -->|Recalled Post-Mortems & RCA| D[Context Injector]
    A --> D
    D --> E[Groq High-Speed LLM Inference]
    E --> F[Attributed Diagnosis & Executable Runbooks]
    F --> G[Dry-Run Cluster Remediation]
    G --> H[Closed-Loop Retention: /retain]
    H -->|Commit New Fix| C
