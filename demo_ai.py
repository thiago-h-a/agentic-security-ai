#!/usr/bin/env python3
import asyncio
from team_agents.core.graph import hunt_graph, HuntState

CASES = []

# 2 cases with histories
CASES.append(HuntState(messages=[
    {"role": "system", "content": "Previous hunt context with lateral movement suspicion"},
    {"role": "user", "content": "Analyst noted unusual SMB traffic"},
    {"role": "assistant", "content": "Recommend checking workstation logins"}
], evidence={}, alerts=[], story=None))

CASES.append(HuntState(messages=[
    {"role": "user", "content": "Suspicious login from foreign IP"},
    {"role": "assistant", "content": "Suggested checking MFA logs"},
    {"role": "system", "content": "Context: previous brute-force alerts on same account"}
], evidence={}, alerts=[], story=None))

# 2-4 cases with key evidences
CASES.append(HuntState(messages=[
    {"role": "user", "content": "Strange PowerShell activity detected on host"},
    {"role": "assistant", "content": "Investigating process tree..."}
], evidence={"process": "powershell.exe -EncodedCommand", "host": "workstation-22"}, alerts=[], story=None))

CASES.append(HuntState(messages=[
    {"role": "system", "content": "Malware signature match on uploaded file"},
    {"role": "assistant", "content": "Hash corresponds to known Trojan"}
], evidence={"file_hash": "abcd1234", "file_path": "/tmp/malicious.exe", "signature": "Trojan.Generic"}, alerts=[], story=None))

CASES.append(HuntState(messages=[
    {"role": "user", "content": "Unusual outbound DNS traffic"},
    {"role": "system", "content": "Spike observed after business hours"}
], evidence={"domain": "suspicious.example.com", "queries": 150, "timeframe": "02:00-03:00"}, alerts=[], story=None))

CASES.append(HuntState(messages=[
    {"role": "assistant", "content": "Reviewing firewall logs"},
    {"role": "user", "content": "Found repeated connections to rare IPs"}
], evidence={"ip_address": "203.0.113.77", "connection_count": 45}, alerts=[], story=None))

# 6 cases with structured alerts
CASES.append(HuntState(messages=[{"role": "system", "content": "Alert: Brute force attempt detected on SSH"}], evidence={}, alerts=[{
    "evidence": {"host": "web01", "indicator": "SSH brute force", "meta": {"ip": "203.0.113.42"}}
}], story=None))

CASES.append(HuntState(messages=[{"role": "user", "content": "High volume of outbound data exfiltration"}], evidence={}, alerts=[{
    "evidence": {"host": "db02", "indicator": "Exfiltration", "meta": {"bytes": 500000000}}
}], story=None))

CASES.append(HuntState(messages=[{"role": "assistant", "content": "Detected persistence via suspicious registry key"}], evidence={}, alerts=[{
    "evidence": {"host": "workstation-15", "indicator": "Registry persistence", "meta": {"key": "HKCU\\Software\\Microsoft\\Windows\\Run"}}
}], story=None))

CASES.append(HuntState(messages=[{"role": "system", "content": "Alert: Ransomware behavior on shared drive"}], evidence={}, alerts=[{
    "evidence": {"host": "fileserver-01", "indicator": "File encryption", "meta": {"extension": ".locked"}}
}], story=None))

CASES.append(HuntState(messages=[{"role": "user", "content": "Suspicious scheduled task observed"}], evidence={}, alerts=[{
    "evidence": {"host": "admin-laptop", "indicator": "Scheduled task", "meta": {"task": "\"Updater\" at 3 AM"}}
}], story=None))

CASES.append(HuntState(messages=[{"role": "assistant", "content": "Privilege escalation attempt via token impersonation"}], evidence={}, alerts=[{
    "evidence": {"host": "domain-controller", "indicator": "Privilege escalation", "meta": {"technique": "Token impersonation"}}
}], story=None))

# 8 cases without problems
for i in range(8):
    CASES.append(HuntState(messages=[
        {"role": "system", "content": f"Routine scan report {i+1}"},
        {"role": "assistant", "content": "No suspicious activity detected"},
        {"role": "user", "content": "All checks clear, system normal."}
    ], evidence={}, alerts=[], story=None))

async def run_case(case: HuntState):
    print("Running case with initial messages:", case.messages)
    async for state in hunt_graph.astream(case):
        print("Step:", state)
    print("Final state:", state)

async def main():
    tasks = [run_case(c) for c in CASES]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
