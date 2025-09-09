#!/usr/bin/env python3
from __future__ import annotations

"""
AppTrust rollback utility

Purpose:
- Perform a rollback of an application version using the dedicated AppTrust API:
  POST /apptrust/api/v1/applications/{application_key}/versions/{version}/rollback

Behavior:
- Fetches the version's current stage via the Content API and passes it as the
  required "from_stage" in the rollback request body.
- Fails fast if the version is UNASSIGNED (rollback not applicable).

Authentication (no long-lived tokens required in CI):
- Preferred: Use JFrog CLI with OIDC (GitHub Actions OIDC). When configured,
  this script will call `jf curl` to perform authenticated REST calls without
  needing a `JFROG_ACCESS_TOKEN`.
- Fallback (local/manual): Provide `--token` or env `APPTRUST_ACCESS_TOKEN`.

Inputs:
- --app: application key (e.g., bookverse-inventory)
- --version: semantic version to rollback (e.g., 1.2.3)
- --base-url: base API URL (env APPTRUST_BASE_URL) — required only when using --token
- --token: bearer token (env APPTRUST_ACCESS_TOKEN) — optional; omit in CI with OIDC

Notes:
- This script does not print secrets.
- Logs include a sanitized description of the endpoint and request body used.
"""

# This file is copied from bookverse-demo-init/scripts/apptrust_rollback.py
# Keep the two in sync when updating.

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import shutil
import subprocess

SEMVER_RE = re.compile(
    r"^\s*v?(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?\s*$"
)

@dataclass(frozen=True)
class SemVer:
    major: int
    minor: int
    patch: int
    prerelease: Tuple[str, ...]
    original: str

    @staticmethod
    def parse(version: str) -> Optional["SemVer"]:
        m = SEMVER_RE.match(version)
        if not m:
            return None
        g = m.groupdict()
        prerelease_raw = g.get("prerelease") or ""
        return SemVer(int(g["major"]), int(g["minor"]), int(g["patch"]), tuple(prerelease_raw.split(".")) if prerelease_raw else tuple(), version)

    def __lt__(self, other: "SemVer") -> bool:  # type: ignore[override]
        return compare_semver(self, other) < 0

def compare_semver(a: SemVer, b: SemVer) -> int:
    if a.major != b.major:
        return -1 if a.major < b.major else 1
    if a.minor != b.minor:
        return -1 if a.minor < b.minor else 1
    if a.patch != b.patch:
        return -1 if a.patch < b.patch else 1
    if not a.prerelease and b.prerelease:
        return 1
    if a.prerelease and not b.prerelease:
        return -1
    for at, bt in zip(a.prerelease, b.prerelease):
        if at == bt:
            continue
        a_num, b_num = at.isdigit(), bt.isdigit()
        if a_num and b_num:
            ai, bi = int(at), int(bt)
            if ai != bi:
                return -1 if ai < bi else 1
        elif a_num and not b_num:
            return -1
        elif not a_num and b_num:
            return 1
        else:
            if at < bt:
                return -1
            return 1
    if len(a.prerelease) != len(b.prerelease):
        return -1 if len(a.prerelease) < len(b.prerelease) else 1
    return 0

def sort_versions_by_semver_desc(version_strings: List[str]) -> List[str]:
    parsed: List[Tuple[SemVer, str]] = []
    for v in version_strings:
        sv = SemVer.parse(v)
        if sv is not None:
            parsed.append((sv, v))
    parsed.sort(key=lambda t: t[0], reverse=True)  # type: ignore[arg-type]
    return [v for _, v in parsed]

class AppTrustClient:
    def __init__(self, base_url: str, token: str, timeout_seconds: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout_seconds = timeout_seconds

    def _request(self, method: str, path: str, query: Optional[Dict[str, Any]] = None, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        if query:
            q = urllib.parse.urlencode({k: v for k, v in query.items() if v is not None})
            url = f"{url}?{q}"
        data = None
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url=url, data=data, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
            raw = resp.read()
            if not raw:
                return {}
            try:
                return json.loads(raw.decode("utf-8"))
            except Exception:
                return {"raw": raw.decode("utf-8", errors="replace")}

    def list_application_versions(self, app_key: str, limit: int = 1000) -> Dict[str, Any]:
        path = f"/applications/{urllib.parse.quote(app_key)}/versions"
        return self._request("GET", path, query={"limit": limit, "order_by": "created", "order_asc": "false"})

    def patch_application_version(self, app_key: str, version: str, tag: Optional[str] = None, properties: Optional[Dict[str, List[str]]] = None, delete_properties: Optional[List[str]] = None) -> Dict[str, Any]:
        path = f"/applications/{urllib.parse.quote(app_key)}/versions/{urllib.parse.quote(version)}"
        body: Dict[str, Any] = {}
        if tag is not None:
            body["tag"] = tag
        if properties is not None:
            body["properties"] = properties
        if delete_properties is not None:
            body["delete_properties"] = delete_properties
        return self._request("PATCH", path, body=body)

    def get_version_content(self, app_key: str, version: str) -> Dict[str, Any]:
        path = f"/applications/{urllib.parse.quote(app_key)}/versions/{urllib.parse.quote(version)}/content"
        return self._request("GET", path)

    def rollback_application_version(self, app_key: str, version: str, from_stage: str) -> Dict[str, Any]:
        """Invoke dedicated rollback endpoint.

        POST /apptrust/api/v1/applications/{application_key}/versions/{version}/rollback
        Body: {"from_stage": "<stage>"}
        """
        path = f"/applications/{urllib.parse.quote(app_key)}/versions/{urllib.parse.quote(version)}/rollback"
        return self._request("POST", path, body={"from_stage": from_stage})


class AppTrustClientCLI:
    """AppTrust client backed by JFrog CLI (OIDC-enabled).

    Requires `jf` on PATH and a configured server context (e.g., via
    `jf c add --interactive=false --url "$JFROG_URL" --access-token ""`).
    """

    def __init__(self, timeout_seconds: int = 30) -> None:
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _ensure_cli_available() -> None:
        if shutil.which("jf") is None:
            raise RuntimeError("JFrog CLI (jf) not found on PATH. Either install/configure it for OIDC or provide --token.")

    @staticmethod
    def _run_jf(method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        AppTrustClientCLI._ensure_cli_available()
        args: List[str] = ["jf", "curl", "-X", method.upper(), path]
        if body is not None:
            args += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
        try:
            proc = subprocess.run(args, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            # Surface stderr while keeping output concise
            raise RuntimeError(f"jf curl failed: {e.stderr.strip() or e}")
        raw = (proc.stdout or "").strip()
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except Exception:
            return {"raw": raw}

    def get_version_content(self, app_key: str, version: str) -> Dict[str, Any]:
        path = f"/apptrust/api/v1/applications/{urllib.parse.quote(app_key)}/versions/{urllib.parse.quote(version)}/content"
        return self._run_jf("GET", path)

    def rollback_application_version(self, app_key: str, version: str, from_stage: str) -> Dict[str, Any]:
        path = f"/apptrust/api/v1/applications/{urllib.parse.quote(app_key)}/versions/{urllib.parse.quote(version)}/rollback"
        return self._run_jf("POST", path, body={"from_stage": from_stage})

TRUSTED = "TRUSTED_RELEASE"
RELEASED = "RELEASED"
QUARANTINE_TAG = "quarantine"
LATEST_TAG = "latest"
BACKUP_BEFORE_LATEST = "original_tag_before_latest"
BACKUP_BEFORE_QUARANTINE = "original_tag_before_quarantine"

def get_prod_versions(client: AppTrustClient, app_key: str) -> List[Dict[str, Any]]:
    resp = client.list_application_versions(app_key)
    versions = resp.get("versions", [])
    norm: List[Dict[str, Any]] = []
    for v in versions:
        ver = str(v.get("version", ""))
        tag = v.get("tag")
        tag_str = "" if tag is None else str(tag)
        rs = str(v.get("release_status", "")).upper()
        if rs in (TRUSTED, RELEASED):
            norm.append({"version": ver, "tag": tag_str, "release_status": rs})
    order = sort_versions_by_semver_desc([v["version"] for v in norm])
    idx = {ver: i for i, ver in enumerate(order)}
    norm.sort(key=lambda x: idx.get(x["version"], 10**9))
    return norm

def pick_next_latest(sorted_prod_versions: List[Dict[str, Any]], exclude_version: str) -> Optional[Dict[str, Any]]:
    dup: Dict[str, List[Dict[str, Any]]] = {}
    for v in sorted_prod_versions:
        if v["version"] == exclude_version:
            continue
        if v.get("tag", "") == QUARANTINE_TAG:
            continue
        dup.setdefault(v["version"], []).append(v)
    if not dup:
        return None
    seen: set[str] = set()
    ordered: List[str] = []
    for v in sorted_prod_versions:
        vv = v["version"]
        if vv == exclude_version:
            continue
        if vv in dup and vv not in seen:
            ordered.append(vv)
            seen.add(vv)
    for ver in ordered:
        cands = dup[ver]
        trusted = [c for c in cands if c.get("release_status") == TRUSTED]
        if trusted:
            return trusted[0]
        return cands[0]
    return None

def backup_tag_then_patch(client: AppTrustClient, app_key: str, version: str, backup_prop_key: str, new_tag: str, current_tag: str, dry_run: bool) -> None:
    props = {backup_prop_key: [current_tag]}
    if dry_run:
        print(f"[DRY-RUN] PATCH backup+tag: app={app_key} version={version} props={props} tag={new_tag}")
        return
    client.patch_application_version(app_key, version, tag=new_tag, properties=props)

def rollback_in_prod(client: AppTrustClient, app_key: str, target_version: str) -> None:
    content = client.get_version_content(app_key, target_version)
    from_stage = str(content.get("current_stage") or "").strip()
    if not from_stage or from_stage.upper() == "UNASSIGNED":
        raise RuntimeError("Cannot rollback a version in UNASSIGNED or unknown stage")
    # Sanitize and print an explicit, debuggable description of the call.
    # Do not emit tokens or the absolute base URL; show only the relative API path and the body.
    print(
        "Calling AppTrust endpoint: POST /applications/"
        f"{app_key}/versions/{target_version}/rollback with body {{from_stage: {from_stage}}}"
    )
    client.rollback_application_version(app_key, target_version, from_stage)
    print(f"Invoked AppTrust rollback for {app_key}@{target_version} from {from_stage}")


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.environ.get(name)
    if v is None or v.strip() == "":
        return default
    return v.strip()

def main() -> int:
    parser = argparse.ArgumentParser(description="AppTrust PROD rollback utility")
    parser.add_argument("--app", required=True, help="Application key")
    parser.add_argument("--version", required=True, help="Target version to rollback (SemVer)")
    parser.add_argument("--base-url", default=_env("APPTRUST_BASE_URL"), help="Base API URL, e.g. https://<host>/apptrust/api/v1 (env: APPTRUST_BASE_URL). Required with --token; ignored with OIDC.")
    parser.add_argument("--token", default=_env("APPTRUST_ACCESS_TOKEN"), help="Access token (env: APPTRUST_ACCESS_TOKEN). Optional if JFrog CLI OIDC is configured.")
    args = parser.parse_args()

    client: Any
    if args.token:
        if not args.base_url:
            print("Missing --base-url or APPTRUST_BASE_URL for token-based auth", file=sys.stderr)
            return 2
        client = AppTrustClient(args.base_url, args.token)
    else:
        # OIDC via JFrog CLI
        try:
            client = AppTrustClientCLI()
        except Exception as e:
            print(f"OIDC (CLI) auth not available and no token provided: {e}", file=sys.stderr)
            return 2

    try:
        start = time.time()
        rollback_in_prod(client, args.app, args.version)
        elapsed = time.time() - start
        print(f"Done in {elapsed:.2f}s")
        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
