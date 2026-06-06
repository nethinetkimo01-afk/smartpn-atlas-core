"""
Non-interactive ClaudeSync setup for smartpn-atlas-core.

Usage:
    $env:CLAUDE_SESSION_KEY = "sk-ant-..."
    python nightly/claudesync_setup.py

Steps:
  1. Generate SSH ed25519 key if missing
  2. Login to claude.ai
  3. Auto-select organization
  4. Find or create "DATA SYSTEM" project
  5. Write .claudesync config into 00_HANDOFF
  6. Run first push
"""
import os, sys, json, subprocess
from pathlib import Path
from datetime import datetime, timedelta

HANDOFF = Path(r"D:\smartpn-atlas-core\00_HANDOFF")
SSH_DIR = Path.home() / ".ssh"
SSH_KEY = SSH_DIR / "id_ed25519"
CS_EXE  = Path(r"C:\Users\user\AppData\Local\Python\pythoncore-3.14-64\Scripts\claudesync.exe")


def step(msg):
    print(f"\n{'='*55}\n  {msg}\n{'='*55}")


def ensure_ssh_key():
    step("Step 1: SSH key")
    if SSH_KEY.exists():
        print(f"  OK — {SSH_KEY}")
        return
    SSH_DIR.mkdir(exist_ok=True)
    print("  Generating ed25519 key...")
    r = subprocess.run(
        ["ssh-keygen", "-t", "ed25519", "-C", "claudesync@smartpn",
         "-f", str(SSH_KEY), "-N", ""],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        print(f"  FAIL: {r.stderr}")
        sys.exit(1)
    print(f"  Created: {SSH_KEY}")


def login(session_key):
    step("Step 2: Login to claude.ai")
    env = os.environ.copy()
    env["CLAUDE_SESSION_KEY"] = session_key
    r = subprocess.run(
        [str(CS_EXE), "auth", "login", "--provider", "claude.ai", "--auto-approve"],
        capture_output=True, text=True, env=env
    )
    out = (r.stdout + r.stderr).strip()
    print(f"  {out}")
    if r.returncode != 0 or "failed" in out.lower():
        print("\n  FAIL: Login failed. Check session key.")
        sys.exit(1)


def select_org():
    step("Step 3: Select organization")
    # Use Python API to get orgs without interactive prompt
    try:
        sys.path.insert(0, str(Path(r"C:\Users\user\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages")))
        from claudesync.configmanager import FileConfigManager
        from claudesync.provider_factory import get_provider

        cfg = FileConfigManager()
        cfg.set("active_provider", "claude.ai", local=False)

        provider = get_provider(cfg, "claude.ai")
        orgs = provider.get_organizations()

        if not orgs:
            print("  FAIL: No organizations found.")
            sys.exit(1)

        org = orgs[0]
        print(f"  Using: {org['name']} ({org['id']})")

        # Save org to global config (so it's available for project commands)
        cfg.set("active_organization_id", org["id"], local=False)
        return org, cfg, provider

    except Exception as e:
        print(f"  FAIL: {e}")
        sys.exit(1)


def find_or_create_project(org, cfg, provider):
    step("Step 4: Find DATA SYSTEM project")
    try:
        projects = provider.get_projects(org["id"])
        print(f"  {len(projects)} project(s) found:")
        for p in projects:
            print(f"    - {p['name']} ({p['id']})")

        target = None
        for p in projects:
            if "DATA" in p["name"].upper() or "SYSTEM" in p["name"].upper():
                target = p
                break

        if not target and projects:
            print("  'DATA SYSTEM' not found, using first project...")
            target = projects[0]

        if not target:
            print("  Creating 'DATA SYSTEM' project...")
            target = provider.create_project(
                org["id"], "DATA SYSTEM", "smartpn-atlas-core handoff documents"
            )
            print(f"  Created: {target['name']} ({target['id']})")
        else:
            print(f"  Selected: {target['name']} ({target['id']})")

        return target

    except Exception as e:
        print(f"  FAIL: {e}")
        sys.exit(1)


def write_local_config(org, project):
    step("Step 5: Write .claudesync config in 00_HANDOFF")
    cs_dir = HANDOFF / ".claudesync"
    cs_dir.mkdir(exist_ok=True)
    cfg_file = cs_dir / "config.local.json"

    cfg = {}
    if cfg_file.exists():
        with open(cfg_file) as f:
            cfg = json.load(f)

    cfg.update({
        "active_provider":         "claude.ai",
        "active_organization_id":  org["id"],
        "active_project_id":       project["id"],
        "active_project_name":     project["name"],
        "local_path":              str(HANDOFF),
    })

    with open(cfg_file, "w") as f:
        json.dump(cfg, f, indent=2)
    print(f"  Written: {cfg_file}")


def first_push():
    step("Step 6: First push to Claude.ai")
    r = subprocess.run(
        [str(CS_EXE), "push"],
        cwd=str(HANDOFF),
        capture_output=True, text=True
    )
    out = (r.stdout + r.stderr).strip()
    for line in out.splitlines():
        print(f"  {line}")
    if r.returncode != 0:
        print("  WARNING: Push errors above — check manually")
    else:
        print("  Push OK")


def main():
    session_key = os.environ.get("CLAUDE_SESSION_KEY", "").strip()
    if not session_key:
        print("""
ERROR: CLAUDE_SESSION_KEY not set.

How to get your session key:
  1. Open https://claude.ai — log in
  2. Press F12 → Application → Cookies → https://claude.ai
  3. Copy the 'sessionKey' value (starts with sk-ant-...)

Then run in PowerShell:
  $env:CLAUDE_SESSION_KEY = "sk-ant-..."
  python nightly/claudesync_setup.py
""")
        sys.exit(1)

    ensure_ssh_key()
    login(session_key)
    org, cfg, provider = select_org()
    project = find_or_create_project(org, cfg, provider)
    write_local_config(org, project)
    first_push()

    print(f"""
{'='*55}
  Setup complete!
  00_HANDOFF → Claude.ai project: {project['name']}
  Nightly auto-sync active after every git push.
{'='*55}
""")


if __name__ == "__main__":
    main()
