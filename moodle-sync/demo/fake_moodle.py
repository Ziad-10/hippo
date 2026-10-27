#!/usr/bin/env python3
"""A tiny stand-in for Moodle's web-service API, for demos and testing.

Serves three made-up courses with generated PDFs, so moodle_sync.py can be
shown end to end without a real university account.

  python3 fake_moodle.py            # http://127.0.0.1:8765, token: 0 x 32
"""

import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8765
TOKEN = "0" * 32
SITE = f"http://127.0.0.1:{PORT}"

COURSES = {
    1234: ("Example Module WiSe 26/27", {
        "Lectures": ["01-searching.pdf", "02-sorting.pdf"],
        "Exercises": ["Sheet-01.pdf"],
    }),
    2001: ("Linear Algebra WiSe 26/27", {
        "Lectures": ["LA-04-eigenvalues.pdf"],
        "Exercises": ["LA-Sheet-04.pdf"],
    }),
    2002: ("Web Development WiSe 26/27", {
        "Project": ["Project brief.pdf"],
    }),
}
MTIME = 1793000000


def make_pdf(title):
    """A minimal one-page PDF showing the title."""
    text = title.replace("(", "").replace(")", "")
    stream = f"BT /F1 28 Tf 72 720 Td ({text}) Tj ET".encode()
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    # Pad with a comment so files have realistic, distinct sizes (150-900 KB).
    pad = 150_000 + sum(map(ord, title)) * 997 % 750_000
    out, offsets = bytearray(b"%PDF-1.4\n" + (b"%" + b"0" * 98 + b"\n") * (pad // 100)), []
    for i, obj in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + obj + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return bytes(out)


def file_url(course_id, name):
    return f"{SITE}/webservice/pluginfile.php/{course_id}/{urllib.parse.quote(name)}"


def contents(course_id):
    sections = []
    for i, (section, files) in enumerate(COURSES[course_id][1].items()):
        modules = [{
            "modname": "resource", "name": name.rsplit(".", 1)[0], "visible": 1,
            "contents": [{
                "type": "file", "filename": name, "filepath": "/",
                "filesize": len(make_pdf(name)), "timemodified": MTIME,
                "fileurl": file_url(course_id, name),
            }],
        } for name in files]
        sections.append({"section": i, "name": section, "modules": modules})
    return sections


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, body, ctype):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        form = urllib.parse.parse_qs(self.rfile.read(length).decode())
        fn = form.get("wsfunction", [""])[0]
        if form.get("wstoken", [""])[0] != TOKEN:
            result = {"exception": "moodle_exception", "errorcode": "invalidtoken", "message": "Invalid token"}
        elif fn == "core_webservice_get_site_info":
            result = {"userid": 7, "fullname": "Demo Student", "sitename": "Demo Moodle"}
        elif fn == "core_enrol_get_users_courses":
            result = [{"id": cid, "fullname": name} for cid, (name, _) in COURSES.items()]
        elif fn == "core_course_get_contents":
            result = contents(int(form["courseid"][0]))
        else:
            result = {"exception": "moodle_exception", "errorcode": "unknown", "message": fn}
        self.send(json.dumps(result).encode(), "application/json")

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if urllib.parse.parse_qs(url.query).get("token", [""])[0] != TOKEN:
            return self.send(b'{"error":"invalid token"}', "application/json")
        name = urllib.parse.unquote(url.path.rsplit("/", 1)[-1])
        self.send(make_pdf(name), "application/pdf")


if __name__ == "__main__":
    print(f"Fake Moodle on {SITE}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
