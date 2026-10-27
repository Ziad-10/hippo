#!/usr/bin/env python3
"""Download new course files from a Moodle site into an Obsidian vault.

Talks to Moodle's web-service API (the one the official Moodle app uses), so
it works with university single sign-on and never sees your password.

- Each Moodle course is mapped to a module folder in config.json; new files
  land in  <vault modules dir>/<Module>/Materials/<Moodle section>/<file>.
- Files already present anywhere under that Materials/ folder (same name or
  same size) are skipped, so existing curated copies are not duplicated.
- Brand-new PDFs are also copied into an iCloud "To GoodNotes" folder,
  which an iOS Shortcut imports into GoodNotes on the iPad.
- A short report note in the vault lists what arrived.

Usage:
  moodle_sync.py login              get and save an access key (once)
  moodle_sync.py courses            list your Moodle courses and their ids
  moodle_sync.py sync --dry-run     show what would be downloaded
  moodle_sync.py sync               download
  moodle_sync.py sync --no-goodnotes   download without copying to GoodNotes
"""

import argparse
import base64
import datetime as dt
import json
import os
import re
import secrets
import shutil
import sys
import urllib.parse
import urllib.request
from pathlib import Path

HOME = Path(os.environ.get("MOODLE_SYNC_HOME", Path(__file__).resolve().parent))
CONFIG_PATH = HOME / "config.json"
STATE_PATH = HOME / "state.json"
# Kept outside the sync folder and the vault so it never ends up in git or a cloud drive.
TOKEN_PATH = Path.home() / ".config" / "moodle-sync" / "token"
TIMEOUT = 60


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def save_json(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def read_token():
    try:
        token = TOKEN_PATH.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        sys.exit(f"No access key found at {TOKEN_PATH}")
    if not re.fullmatch(r"[0-9a-f]{32}", token):
        sys.exit(f"The access key in {TOKEN_PATH} does not look valid")
    return token


class Moodle:
    def __init__(self, site, token):
        self.site = site.rstrip("/")
        self.token = token

    def call(self, function, **params):
        data = {"wstoken": self.token, "wsfunction": function, "moodlewsrestformat": "json"}
        data.update(params)
        req = urllib.request.Request(
            f"{self.site}/webservice/rest/server.php",
            data=urllib.parse.urlencode(data).encode(),
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            result = json.load(resp)
        if isinstance(result, dict) and "exception" in result:
            raise RuntimeError(f"{function}: {result.get('message')} ({result.get('errorcode')})")
        return result

    def download(self, fileurl, dest):
        sep = "&" if "?" in fileurl else "?"
        url = f"{fileurl}{sep}token={urllib.parse.quote(self.token)}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        part = dest.with_name(dest.name + ".part")
        with urllib.request.urlopen(url, timeout=TIMEOUT) as resp, open(part, "wb") as out:
            ctype = resp.headers.get("Content-Type", "")
            shutil.copyfileobj(resp, out)
        # Moodle answers errors with a JSON body instead of the file.
        if "application/json" in ctype and not dest.suffix.lower() == ".json":
            msg = part.read_text(errors="replace")[:200]
            part.unlink()
            raise RuntimeError(f"download refused: {msg}")
        part.replace(dest)


def clean(name):
    name = re.sub(r'[/\\:*?"<>|\x00-\x1f]', "_", name).strip().strip(".")
    return name[:150] or "unnamed"


def course_files(moodle, course_id, skip_ext, max_mb):
    """Yield (section, relative subpath, content) for every file in a course."""
    for section in moodle.call("core_course_get_contents", courseid=course_id):
        section_name = clean(section.get("name") or f"Section {section.get('section')}")
        for mod in section.get("modules", []):
            if mod.get("visible") == 0 or mod.get("uservisible") is False:
                continue
            for content in mod.get("contents") or []:
                if content.get("type") != "file":
                    continue
                filename = content.get("filename") or ""
                ext = Path(filename).suffix.lower()
                if ext in skip_ext or content.get("filesize", 0) > max_mb * 1024 * 1024:
                    continue
                parts = [section_name]
                if mod.get("modname") == "folder":
                    parts.append(clean(mod.get("name", "Folder")))
                    parts += [clean(p) for p in (content.get("filepath") or "/").split("/") if p]
                parts.append(clean(filename))
                yield Path(*parts), content


def existing_index(materials):
    names, sizes = set(), set()
    if materials.exists():
        for p in materials.rglob("*"):
            if p.is_file() and not p.name.endswith(".part"):
                names.add(p.name.lower())
                size = p.stat().st_size
                if size > 10 * 1024:
                    sizes.add(size)
    return names, sizes


def cmd_login(cfg):
    """Moodle hands an app token to a custom URL scheme after a browser login.
    The browser cannot open moodlemobile://, but shows the URL in its error."""
    url = (f"{cfg['site'].rstrip('/')}/admin/tool/mobile/launch.php"
           f"?service=moodle_mobile_app&passport={secrets.randbelow(10**6)}&urlscheme=moodlemobile")
    print("1. Sign in to Moodle in Chrome.")
    print("2. Open DevTools (Console tab), then open this link in the same tab:")
    print(f"   {url}")
    print("3. Copy the 'moodlemobile://token=...' link from the console error and paste it here.")
    raw = input("> ").strip()
    if re.fullmatch(r"[0-9a-f]{32}", raw):
        token = raw
    else:
        b64 = raw.split("token=", 1)[-1].strip("'\" ")
        try:
            parts = base64.b64decode(b64).decode().split(":::")
            token = parts[1]
        except Exception:
            sys.exit("Could not read a token from that link")
    if not re.fullmatch(r"[0-9a-f]{32}", token):
        sys.exit("That does not look like a Moodle token")
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(TOKEN_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(token + "\n")
    name = Moodle(cfg["site"], token).call("core_webservice_get_site_info")["fullname"]
    print(f"Saved. Signed in as {name}.")


def cmd_courses(cfg, moodle):
    info = moodle.call("core_webservice_get_site_info")
    courses = moodle.call("core_enrol_get_users_courses", userid=info["userid"])
    mapped = cfg.get("courses", {})
    for c in sorted(courses, key=lambda c: c["id"]):
        target = mapped.get(str(c["id"]), {}).get("module", "-")
        print(f"{c['id']:>7}  {c['fullname']}  ->  {target}")


def cmd_sync(cfg, moodle, dry_run, goodnotes):
    modules_dir = Path(cfg["modules_dir"]).expanduser()
    gn_dir = Path(cfg["goodnotes_dir"]).expanduser()
    gn_ext = {e.lower() for e in cfg.get("goodnotes_extensions", [".pdf"])}
    skip_ext = {e.lower() for e in cfg.get("skip_extensions", [])}
    max_mb = cfg.get("max_file_mb", 200)
    state = load_json(STATE_PATH, {"files": {}})
    seen = state["files"]
    new, updated, errors = [], [], []

    for course_id, course in cfg.get("courses", {}).items():
        if not course.get("enabled", True):
            continue
        module = course["module"]
        materials = modules_dir / module / "Materials"
        names, sizes = existing_index(materials)
        try:
            files = list(course_files(moodle, int(course_id), skip_ext, max_mb))
        except Exception as e:
            errors.append(f"{module}: {e}")
            continue
        for rel, content in files:
            key = content["fileurl"].split("?")[0]
            mtime = content.get("timemodified", 0)
            size = content.get("filesize", 0)
            known = seen.get(key)
            if known and known["timemodified"] >= mtime:
                continue
            if known:
                dest = modules_dir / known["path"]
                kind = "updated"
            else:
                if rel.name.lower() in names or (size > 10 * 1024 and size in sizes):
                    # Already in the vault under some name: remember it, don't fetch.
                    if not dry_run:
                        seen[key] = {"path": None, "timemodified": mtime, "filesize": size}
                    continue
                dest = materials / rel
                kind = "new"
            relpath = dest.relative_to(modules_dir)
            if dry_run:
                if kind == "new" and dest.name.lower() in names:
                    continue
                names.add(dest.name.lower())
                print(f"[{kind}] {relpath}  ({size // 1024} KB)")
                continue
            if dest.exists() and kind == "new":
                continue
            try:
                moodle.download(content["fileurl"], dest)
            except Exception as e:
                errors.append(f"{relpath}: {e}")
                continue
            seen[key] = {"path": str(relpath), "timemodified": mtime, "filesize": size}
            names.add(dest.name.lower())
            (new if kind == "new" else updated).append(relpath)
            if kind == "new" and goodnotes and dest.suffix.lower() in gn_ext:
                gn_dir.mkdir(parents=True, exist_ok=True)
                gn_target = gn_dir / f"{module} - {dest.name}"
                if not gn_target.exists():
                    shutil.copy2(dest, gn_target)
            save_json(STATE_PATH, state)

    if not dry_run:
        state["last_run"] = dt.datetime.now().isoformat(timespec="seconds")
        save_json(STATE_PATH, state)
        if new or updated or errors:
            write_report(cfg, new, updated, errors)
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"{stamp}  new: {len(new)}  updated: {len(updated)}  errors: {len(errors)}")
    for e in errors:
        print("  error:", e)
    return 1 if errors else 0


def write_report(cfg, new, updated, errors):
    """Prepend this run's results to the vault report note (keeps last 40 runs)."""
    note = Path(cfg["report_note"]).expanduser()
    header = "# Moodle downloads\n\nWritten automatically by the Moodle sync script (see [[Moodle sync setup]]). Newest first.\n"
    prefix = cfg.get("link_prefix", "")
    lines = [f"\n## {dt.datetime.now():%Y-%m-%d %H:%M}\n"]
    lines += [f"- New: [[{prefix}{p.as_posix()}|{p.name}]] ({p.parts[0]})" for p in new]
    lines += [f"- Updated on Moodle: [[{prefix}{p.as_posix()}|{p.name}]] ({p.parts[0]})" for p in updated]
    lines += [f"- Error: {e}" for e in errors]
    old_runs = []
    if note.exists():
        body = note.read_text(encoding="utf-8")
        old_runs = re.split(r"\n(?=## \d{4}-\d{2}-\d{2})", body)[1:]
    runs = ["\n".join(lines).strip("\n")] + [r.strip("\n") for r in old_runs][:39]
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text(header + "\n" + "\n\n".join(runs) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("login")
    sub.add_parser("courses")
    s = sub.add_parser("sync")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--no-goodnotes", action="store_true")
    args = ap.parse_args()

    cfg = load_json(CONFIG_PATH, None)
    if cfg is None:
        sys.exit(f"Missing {CONFIG_PATH} (copy config.example.json to start)")
    if args.cmd == "login":
        return cmd_login(cfg)
    moodle = Moodle(cfg["site"], read_token())
    if args.cmd == "courses":
        cmd_courses(cfg, moodle)
    else:
        sys.exit(cmd_sync(cfg, moodle, args.dry_run, not args.no_goodnotes))


if __name__ == "__main__":
    main()
