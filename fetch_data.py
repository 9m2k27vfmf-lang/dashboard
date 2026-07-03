"""
Fetch WHOOP + GitHub + Claude data and save to data.json for the dashboard.
Run: python3 fetch_data.py
"""

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import requests
from whoop_auth import get_access_token

# Physical RAM in MB (used to calc RAM percentage)
def _total_ram_mb() -> int:
    try:
        out = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True)
        return int(out.stdout.strip()) // (1024 * 1024)
    except Exception:
        return 16384  # sensible fallback (16 GB)

WHOOP_BASE = "https://api.prod.whoop.com/developer/v2"
GITHUB_USER = "9m2k27vfmf-lang"
DATA_FILE = Path(__file__).parent / "data.json"


# ── WHOOP ──────────────────────────────────────────────────────────────────────

def fetch_whoop() -> dict:
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    def get(path, params=None):
        r = requests.get(f"{WHOOP_BASE}{path}", headers=headers, params=params or {})
        if r.status_code == 200:
            return r.json()
        print(f"  WHOOP {path} → {r.status_code}")
        return {}

    # Last 7 days of cycles
    cycles_raw = get("/cycle", {"limit": 7})
    cycles = []
    for c in cycles_raw.get("records", []):
        score = c.get("score") or {}
        cycles.append({
            "date": c.get("start", "")[:10],
            "strain": round(score.get("strain", 0), 1),
            "kilojoule": round(score.get("kilojoule", 0), 0),
            "average_heart_rate": score.get("average_heart_rate", 0),
            "max_heart_rate": score.get("max_heart_rate", 0),
        })

    # Latest recovery
    recovery_raw = get("/recovery", {"limit": 1})
    recovery_records = recovery_raw.get("records", [{}])
    latest_recovery = recovery_records[0] if recovery_records else {}
    rec_score = latest_recovery.get("score") or {}

    # Latest sleep
    sleep_raw = get("/activity/sleep", {"limit": 1})
    sleep_records = sleep_raw.get("records", [{}])
    latest_sleep = sleep_records[0] if sleep_records else {}
    sleep_score = latest_sleep.get("score") or {}

    return {
        "recovery_score": rec_score.get("recovery_score", 0),
        "hrv_rmssd": round(rec_score.get("hrv_rmssd_milli", 0), 1),
        "resting_heart_rate": rec_score.get("resting_heart_rate", 0),
        "sleep_performance": sleep_score.get("sleep_performance_percentage", 0),
        "sleep_minutes": int((
            (datetime.fromisoformat(latest_sleep["end"].replace("Z", "+00:00")) -
             datetime.fromisoformat(latest_sleep["start"].replace("Z", "+00:00"))).seconds // 60
        ) if latest_sleep.get("end") and latest_sleep.get("start") else 0),
        "cycles": cycles,
    }


# ── GitHub ─────────────────────────────────────────────────────────────────────

def fetch_github() -> dict:
    try:
        result = subprocess.run(
            ["gh", "api", f"users/{GITHUB_USER}"],
            capture_output=True, text=True
        )
        user = json.loads(result.stdout) if result.returncode == 0 else {}

        repos_result = subprocess.run(
            ["gh", "repo", "list", GITHUB_USER, "--json",
             "name,description,pushedAt,stargazerCount,url", "--limit", "10"],
            capture_output=True, text=True
        )
        repos = json.loads(repos_result.stdout) if repos_result.returncode == 0 else []

        prs_result = subprocess.run(
            ["gh", "search", "prs", "--author", GITHUB_USER,
             "--json", "title,state,url,updatedAt", "--limit", "5"],
            capture_output=True, text=True
        )
        prs = json.loads(prs_result.stdout) if prs_result.returncode == 0 else []

        return {
            "username": user.get("login", GITHUB_USER),
            "public_repos": user.get("public_repos", 0),
            "followers": user.get("followers", 0),
            "repos": repos,
            "recent_prs": prs,
        }
    except Exception as e:
        print(f"  GitHub fetch error: {e}")
        return {"username": GITHUB_USER, "public_repos": 0, "followers": 0, "repos": [], "recent_prs": []}


# ── Claude (CPU + RAM) ─────────────────────────────────────────────────────────

def fetch_claude() -> dict:
    """Aggregate CPU% and RAM (RSS) for every running Claude process."""
    try:
        result = subprocess.run(
            ["ps", "-axo", "pid,pcpu,rss,comm"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return {"running": False, "process_count": 0, "cpu_percent": 0.0,
                    "ram_mb": 0, "ram_percent": 0.0, "total_ram_mb": _total_ram_mb()}

        cpu_total = 0.0
        rss_total_kb = 0  # ps reports rss in KB on macOS
        count = 0

        for line in result.stdout.splitlines()[1:]:
            parts = line.strip().split(None, 3)
            if len(parts) < 4:
                continue
            _, pcpu, rss, comm = parts
            # Match any Claude-related binary path
            if "/Claude.app/" in comm or "/claude-code/" in comm or comm.endswith("/claude"):
                try:
                    cpu_total += float(pcpu)
                    rss_total_kb += int(rss)
                    count += 1
                except ValueError:
                    continue

        total_ram_mb = _total_ram_mb()
        ram_mb = rss_total_kb // 1024
        ram_percent = (ram_mb / total_ram_mb * 100) if total_ram_mb else 0.0

        return {
            "running": count > 0,
            "process_count": count,
            "cpu_percent": round(cpu_total, 1),
            "ram_mb": ram_mb,
            "ram_percent": round(ram_percent, 1),
            "total_ram_mb": total_ram_mb,
        }
    except Exception as e:
        print(f"  Claude fetch error: {e}")
        return {"running": False, "process_count": 0, "cpu_percent": 0.0,
                "ram_mb": 0, "ram_percent": 0.0, "total_ram_mb": _total_ram_mb()}


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("Fetching WHOOP data...")
    whoop = fetch_whoop()
    print(f"  Recovery: {whoop['recovery_score']}%  HRV: {whoop['hrv_rmssd']}ms")

    print("Fetching GitHub data...")
    github = fetch_github()
    print(f"  Repos: {github['public_repos']}  PRs: {len(github['recent_prs'])}")

    print("Fetching Claude stats...")
    claude = fetch_claude()
    print(f"  Processes: {claude['process_count']}  CPU: {claude['cpu_percent']}%  RAM: {claude['ram_mb']} MB")

    data = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "whoop": whoop,
        "github": github,
        "claude": claude,
    }

    DATA_FILE.write_text(json.dumps(data, indent=2))
    print(f"\nData saved to {DATA_FILE}")
    print("Open index.html in your browser to see the dashboard.")


if __name__ == "__main__":
    main()
