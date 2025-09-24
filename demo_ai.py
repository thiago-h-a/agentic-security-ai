#!/usr/bin/env python3
import asyncio
import random
import time
from fastAPI import HuntState, hunt_graph

# --- Mock realistic messages for each step ---
COLLECTOR_OUTCOMES = [
    "Normalized 2 SMB events from workstation-12",
    "Collected 3 login anomalies from web01",
    "Parsed 1 suspicious PowerShell execution",
    "No suspicious events found in current logs"
]

INTEL_OUTCOMES = [
    "Matched IP 203.0.113.77 with known C2 infrastructure",
    "Enriched PowerShell command with MITRE ATT&CK T1059.001",
    "Domain suspicious.example.com linked to phishing campaign",
    "No CTI match found for given evidence"
]

HYPOTHESIS_OUTCOMES = [
    "Possible lateral movement via SMB",
    "Potential exfiltration from db02",
    "Suspicion of ransomware on fileserver-01",
    "Unlikely benign scheduled task"
]

QUERY_BUILDER_OUTCOMES = [
    "Compiled query: FROM logs WHERE event_type='SMB' AND failed_logins > 5",
    "Compiled query: FROM dns WHERE domain='suspicious.example.com'",
    "Compiled query: FROM process WHERE command LIKE '%powershell.exe -enc%'",
    "Compiled query: FROM auth WHERE country NOT IN ['US','CA']"
]

DETECTOR_OUTCOMES = [
    "Alert: Multiple failed logins detected on SSH",
    "Alert: Suspicious outbound DNS spike",
    "Alert: Registry persistence created",
    "No alerts detected"
]

CORRELATOR_OUTCOMES = [
    "Correlated SSH brute force with MFA bypass attempt",
    "Correlated DNS exfiltration with PowerShell execution",
    "Single alert only, no correlation",
    "No alerts to correlate"
]

RESPONDER_OUTCOMES = [
    "Isolated workstation-22 from network",
    "Disabled compromised account db02-user",
    "Blocked outbound traffic to 203.0.113.77",
    "No response actions taken"
]


# --- Define realistic demo cases ---
CASES = [
    HuntState(messages=[
        {"role": "system", "content": "Previous hunt context with lateral movement suspicion"},
        {"role": "user", "content": "Analyst noted unusual SMB traffic"},
        {"role": "assistant", "content": "Recommend checking workstation logins"}
    ], evidence={}, alerts=[], story=None),
    HuntState(messages=[
        {"role": "user", "content": "Suspicious login from foreign IP"},
        {"role": "assistant", "content": "Suggested checking MFA logs"},
        {"role": "system", "content": "Context: previous brute-force alerts on same account"}
    ], evidence={}, alerts=[], story=None),
    HuntState(messages=[
        {"role": "user", "content": "Strange PowerShell activity detected on host"},
        {"role": "assistant", "content": "Investigating process tree..."}
    ], evidence={"process": "powershell.exe -EncodedCommand", "host": "workstation-22"}, alerts=[], story=None),
    HuntState(messages=[
        {"role": "system", "content": "Malware signature match on uploaded file"},
        {"role": "assistant", "content": "Hash corresponds to known Trojan"}
    ], evidence={"file_hash": "abcd1234", "file_path": "/tmp/malicious.exe", "signature": "Trojan.Generic"}, alerts=[], story=None),
]


async def run_pipeline(case: HuntState, case_id: int):
    print(f"\n=== Running Case {case_id} ===")
    print("Initial Messages:")
    for m in case.messages:
        print(f" - {m['role'].capitalize()}: {m['content']}")
    print("")

    # Simulate pipeline with artificial delays
    steps = [
        ("collector_node", random.choice(COLLECTOR_OUTCOMES)),
        ("intel_agent", random.choice(INTEL_OUTCOMES)),
        ("hypothesis_agent", random.choice(HYPOTHESIS_OUTCOMES)),
        ("query_builder_agent", random.choice(QUERY_BUILDER_OUTCOMES)),
        ("detector_node", random.choice(DETECTOR_OUTCOMES)),
        ("correlator_node", random.choice(CORRELATOR_OUTCOMES)),
        ("responder_node", random.choice(RESPONDER_OUTCOMES)),
    ]

    for step, outcome in steps:
        await asyncio.sleep(0.6)  # ~streaming effect
        print(f"[{step}] {outcome}")
        if "No" in outcome or "Unlikely" in outcome:
            break  # stop pipeline early if nothing suspicious

    print(f"=== Final State for Case {case_id}: {step} ===\n")


async def stream_cases():
    case_id = 1
    while True:
        case = random.choice(CASES)
        await run_pipeline(case, case_id)
        case_id += 1
        await asyncio.sleep(1)  # space between pipelines


if __name__ == "__main__":
    try:
        asyncio.run(stream_cases())
    except KeyboardInterrupt:
        print("\nStopped by user.")
