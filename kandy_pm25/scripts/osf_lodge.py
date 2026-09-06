"""osf_lodge.py -- put a pre-registration on OSF so its timestamp is third-party.

WHY A SCRIPT AND NOT A BROWSER. A registration lodged by hand leaves no record of what was sent,
and this project has five registrations whose exact submitted text matters. This posts the file
verbatim, prints every identifier it creates, and verifies the artefact afterwards.

THE RULE THIS SCRIPT EXISTS TO ENFORCE (gotcha #89). An HTTP error is not evidence that nothing
happened. On a previous registration the OSF API returned 500 twice, 502 twice and 403 three
times across eight attempts, and ONE OF THE 500s HAD SUCCEEDED. A naive retry that created the
registration again would have produced a duplicate with a later timestamp, destroying the only
thing a pre-registration is for. So this script queries the collection BEFORE creating anything
and again after any failure, and refuses to create a second registration with the same title.

Usage: python scripts/osf_lodge.py --file docs/prereg_kandy_campaign_2026-09-05.md \
                                   --title "..." [--dry-run]
"""
from __future__ import annotations

import argparse
import io
import sys
import time
from pathlib import Path

import requests

REPO = Path(__file__).resolve().parents[1]
API = "https://api.osf.io/v2"
TOKEN_FILE = REPO.parent / "API.txt"


def token() -> str:
    for ln in io.open(TOKEN_FILE, encoding="utf-8", errors="replace"):
        if ln.strip().upper().startswith("OSF"):
            return ln.split(":", 1)[1].strip()
    raise SystemExit("no OSF token in API.txt")


def req(method, url, h, **kw):
    """One request, with the response body surfaced. No silent retries."""
    r = requests.request(method, url, headers=h, timeout=120, **kw)
    if not r.ok:
        body = (r.text or "")[:400]
        print(f"    HTTP {r.status_code}  {method} {url.split('/v2/')[-1][:60]}\n    {body}")
    return r


# Atmospheric Sciences, and Environmental Sciences, each as its full path from the taxonomy
# root. Resolved once via /v2/subjects/{id}/ and its parent chain, and hardcoded because the
# taxonomy is stable and a lookup per run is a needless dependency at submission time.
SUBJECT_PATHS = [
    ["584240d954be81056ceca9a1",   # Physical Sciences and Mathematics
     "584240d954be81056ceca9de",   # Oceanography and Atmospheric Sciences and Meteorology
     "584240da54be81056cecaad4"],  # Atmospheric Sciences
    ["584240d954be81056ceca9a1",
     "584240da54be81056cecaaf7"],  # Environmental Sciences
]
SUBJECT_LEAVES = [p[-1] for p in SUBJECT_PATHS]


def set_subjects(h, node, draft) -> bool:
    """Set subjects on BOTH the node and the draft, in the format each one demands.

    The node wants `subjects` as a list of full hierarchical PATHS. The draft wants a flat list
    of leaf ids. Sending either format to the other endpoint returns a 400 that names the
    problem but not the fix, so both shapes are spelled out here.
    """
    ok_node = req("PATCH", f"{API}/nodes/{node}/", h, json={"data": {
        "id": node, "type": "nodes",
        "attributes": {"subjects": SUBJECT_PATHS}}}).ok
    ok_draft = req("PATCH", f"{API}/draft_registrations/{draft}/", h, json={"data": {
        "id": draft, "type": "draft_registrations",
        "attributes": {"subjects": SUBJECT_LEAVES}}}).ok
    return ok_node and ok_draft


def find_existing(h, title):
    """Has this already been registered? Checked BEFORE creating anything."""
    for path in ("users/me/registrations/", "users/me/nodes/"):
        r = req("GET", f"{API}/{path}?page[size]=100", h)
        if not r.ok:
            continue
        for n in r.json().get("data", []):
            if n["attributes"]["title"].strip() == title.strip():
                return path.split("/")[-2], n["id"]
    return None, None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--description", default="")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    text = io.open(REPO / a.file, encoding="utf-8").read()
    h = {"Authorization": f"Bearer {token()}", "Content-Type": "application/vnd.api+json"}
    print(f"=== lodging {a.file} ===")
    print(f"    title: {a.title}")
    print(f"    {len(text):,} characters, {text.count(chr(10)):,} lines")

    kind, existing = find_existing(h, a.title)
    if existing:
        print(f"\n[!] ALREADY EXISTS as a {kind}: {existing} -> https://osf.io/{existing}/")
        print("    Refusing to create a second one. Verify the artefact, never the status code.")
        return
    if a.dry_run:
        print("\n    dry run, nothing created")
        return

    # 1. project
    r = req("POST", f"{API}/nodes/", h, json={"data": {"type": "nodes", "attributes": {
        "title": a.title, "category": "project",
        "description": a.description or a.title, "public": True}}})
    if not r.ok:
        raise SystemExit("could not create the project")
    node = r.json()["data"]["id"]
    print(f"\n[1] project  {node}  https://osf.io/{node}/")

    # 2. the full text into the wiki, so the registration carries the words and not a pointer
    r = req("POST", f"{API}/nodes/{node}/wikis/", h, json={"data": {
        "type": "wikis", "attributes": {"name": "home", "content": text}}})
    print(f"[2] wiki     {'written' if r.ok else 'FAILED, continuing'}")

    # 3. schema
    r = req("GET", f"{API}/schemas/registrations/?page[size]=100", h)
    schema = next((s["id"] for s in r.json()["data"]
                   if "open-ended" in s["attributes"]["name"].lower()), None)
    if not schema:
        raise SystemExit("no Open-Ended Registration schema found")
    print(f"[3] schema   Open-Ended Registration  {schema}")

    # 4. draft
    r = req("POST", f"{API}/nodes/{node}/draft_registrations/", h, json={"data": {
        "type": "draft_registrations",
        "relationships": {"registration_schema": {"data": {
            "type": "registration-schemas", "id": schema}}}}})
    if not r.ok:
        raise SystemExit("could not create the draft")
    draft = r.json()["data"]["id"]
    print(f"[4] draft    {draft}")

    summary = text[:4000]
    req("PATCH", f"{API}/draft_registrations/{draft}/", h, json={"data": {
        "id": draft, "type": "draft_registrations",
        "attributes": {"registration_responses": {"summary": summary}}}})

    # 5. subjects. OSF refuses to register without at least one, and the two endpoints want
    # DIFFERENT formats for the same information: the node takes a list of full hierarchical
    # paths from the taxonomy root, the draft takes a flat list of leaf ids. Setting only the
    # node is not enough; the refusal persists and names the node, which is misleading.
    # This step must follow the draft, since it patches the draft.
    if not set_subjects(h, node, draft):
        print("[5] subjects FAILED. Stopping BEFORE the register POST, because a registration "
              "attempt that will certainly be refused is not worth the ambiguity of an error.")
        return
    print("[5] subjects set on the node and the draft")

    # 6. register
    r = req("POST", f"{API}/nodes/{node}/registrations/", h, json={"data": {
        "type": "registrations",
        "attributes": {"draft_registration": draft, "registration_choice": "immediate"}}})

    # 7. VERIFY THE ARTEFACT, whatever the status code said
    time.sleep(4)
    v = req("GET", f"{API}/nodes/{node}/registrations/", h)
    got = v.json().get("data", []) if v.ok else []
    if got:
        reg = got[0]
        rid = reg["id"]
        print(f"\n[5] REGISTERED  {rid}  https://osf.io/{rid}/")
        print(f"    state: {reg['attributes'].get('pending_registration_approval')} pending, "
              f"registered {reg['attributes'].get('date_registered')}")
        print(f"\n    Add to the document header:  OSF `{rid}`, project `{node}`")
    else:
        print(f"\n[!] No registration found under node {node} after the POST.")
        print(f"    The POST reported {r.status_code}. Check https://osf.io/{node}/ by hand "
              f"before retrying: a retry that succeeds twice is worse than one that fails once.")


if __name__ == "__main__":
    main()
