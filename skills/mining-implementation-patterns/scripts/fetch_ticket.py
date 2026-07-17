#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Fetch a ticket from Azure DevOps or Jira and write it as requirements.md.

Auth (environment variables):
  Azure DevOps : AZURE_DEVOPS_PAT   (PAT with Work Items: Read scope)
  Jira Cloud   : JIRA_EMAIL + JIRA_API_TOKEN

Exit codes:
  0 ok
  2 invalid arguments / unrecognized URL shape
  3 missing credentials (message names the exact env vars)
  4 HTTP error from the ticket API (401/403/404 explained)
"""
import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request

TIMEOUT_S = 30  # generous; both APIs normally answer in <2s


def die(code, msg):
    print(msg, file=sys.stderr)
    sys.exit(code)


def http_json(url, auth_header):
    req = urllib.request.Request(url, headers={
        "Authorization": auth_header, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        hints = {
            401: "credentials rejected — check the token value and that it has not expired",
            403: "token lacks scope — ADO needs 'Work Items: Read'; Jira needs project access",
            404: "ticket not found — check the id/key and that the URL's org/project is right",
        }
        die(4, f"HTTP {e.code} from {url}: {hints.get(e.code, e.reason)}")
    except urllib.error.URLError as e:
        die(4, f"Could not reach {url}: {e.reason}")


def strip_html(s):
    s = re.sub(r"<br\s*/?>|</p>|</div>|</li>", "\n", s or "", flags=re.I)
    s = re.sub(r"<li[^>]*>", "- ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def adf_to_text(node):
    """Flatten Jira's Atlassian Document Format into plain text."""
    if node is None:
        return ""
    if isinstance(node, str):  # API v2 (Server/DC) returns a plain string
        return node
    if isinstance(node, list):
        return "".join(adf_to_text(n) for n in node)
    t = node.get("type")
    if t == "text":
        return node.get("text", "")
    inner = adf_to_text(node.get("content", []))
    if t in ("paragraph", "heading"):
        return inner + "\n\n"
    if t == "listItem":
        return "- " + inner
    if t == "hardBreak":
        return "\n"
    return inner


def fetch_ado(url):
    m = re.search(r"(?:dev\.azure\.com/([^/]+)|([^./]+)\.visualstudio\.com)"
                  r"/([^/]+)/(?:_workitems/edit/(\d+)|.*[?&]workitem=(\d+))", url)
    if not m:
        die(2, "Unrecognized Azure DevOps URL. Expected shapes: "
               "https://dev.azure.com/<org>/<project>/_workitems/edit/<id>, "
               "or a board/sprint link with ?workitem=<id>")
    org = m.group(1) or m.group(2)
    project, wid = m.group(3), m.group(4) or m.group(5)
    pat = os.environ.get("AZURE_DEVOPS_PAT")
    if not pat:
        die(3, "Missing env var AZURE_DEVOPS_PAT (a PAT with Work Items: Read). "
               "Export it and re-run.")
    auth = "Basic " + base64.b64encode(f":{pat}".encode()).decode()
    api = (f"https://dev.azure.com/{org}/{project}/_apis/wit/workitems/{wid}"
           f"?api-version=7.1")
    data = http_json(api, auth)
    f = data.get("fields", {})
    title = f.get("System.Title", f"Work item {wid}")
    body = strip_html(f.get("System.Description", ""))
    ac = strip_html(f.get("Microsoft.VSTS.Common.AcceptanceCriteria", ""))
    md = f"# {title}\n\nSource: {url}\nType: {f.get('System.WorkItemType', '?')}  " \
         f"State: {f.get('System.State', '?')}\n\n## Description\n\n{body or '(empty)'}\n"
    if ac:
        md += f"\n## Acceptance criteria\n\n{ac}\n"
    return md


def fetch_jira(url):
    m = re.search(r"https://([^?#]+?)/browse/([A-Z][A-Z0-9]+-\d+)", url)
    if not m:
        die(2, "Unrecognized Jira URL. Expected shape: "
               "https://<site>.atlassian.net/browse/<KEY-123> "
               "(a context path before /browse/ is fine, e.g. /jira/browse/)")
    base, key = m.group(1), m.group(2)
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_API_TOKEN")
    if not (email and token):
        missing = [v for v in ("JIRA_EMAIL", "JIRA_API_TOKEN")
                   if not os.environ.get(v)]
        die(3, f"Missing env var(s): {', '.join(missing)}. "
               "Create an API token at id.atlassian.com and export both.")
    auth = "Basic " + base64.b64encode(f"{email}:{token}".encode()).decode()
    ver = "3" if base.endswith(".atlassian.net") else "2"  # Server/DC has no v3
    api = f"https://{base}/rest/api/{ver}/issue/{key}?fields=summary,description,status,issuetype"
    data = http_json(api, auth)
    f = data.get("fields", {})
    title = f.get("summary", key)
    body = adf_to_text(f.get("description")).strip()
    md = f"# {key}: {title}\n\nSource: {url}\n" \
         f"Type: {(f.get('issuetype') or {}).get('name', '?')}  " \
         f"Status: {(f.get('status') or {}).get('name', '?')}\n\n" \
         f"## Description\n\n{body or '(empty)'}\n"
    return md


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", required=True, help="ticket URL (ADO or Jira)")
    ap.add_argument("--out", required=True, help="markdown output path")
    a = ap.parse_args()

    if "dev.azure.com" in a.url or "visualstudio.com" in a.url:
        md = fetch_ado(a.url)
    elif "/browse/" in a.url:
        md = fetch_jira(a.url)
    else:
        die(2, "Could not identify the tracker from the URL. Supported: "
               "Azure DevOps (dev.azure.com/.../_workitems/edit/<id>) and "
               "Jira (<site>/browse/<KEY-123>). For other trackers, paste "
               "the requirements text instead.")

    md += ("\n## Normalized requirements\n\n"
           "<!-- Fill in: R1..Rn, one atomic testable requirement per line -->\n")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as fh:
        fh.write(md)
    print(json.dumps({"out": a.out, "chars": len(md)}))


if __name__ == "__main__":
    main()
