"""Offline tests for the multi-vendor scraper: pagination (10+ pages), login, scoping, PDFs."""
import io, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import vendor_scraper as vs

# ----------------------------------------------------------------------------- fake HTTP layer
class Resp:
    def __init__(self, status=200, body=b"", ctype="text/html", headers=None):
        self.status_code = status; self._b = body if isinstance(body, bytes) else body.encode()
        self.headers = {"Content-Type": ctype, **(headers or {})}; self.content = self._b
        loc = self.headers.get("Location"); self.is_redirect = bool(loc) and 300 <= status < 400; self.is_permanent_redirect = False
    def iter_content(self, n): yield self._b
    def __enter__(self): return self
    def __exit__(self, *a): return False

class FakeHttp:
    def __init__(self, routes): self.routes = routes; self.calls = []; self.posts = []; self.signed_in = False
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def get(self, url, **kw):
        self.calls.append((url, kw)); r = self.routes(url, self, kw)
        return r
    def post(self, url, data=None, **kw):
        self.posts.append((url, dict(data or {})))
        if data and data.get("pw") == "good-pass" and data.get("uid") == "alice":
            self.signed_in = True; return Resp(200, "<html><body>Welcome. Support content.</body></html>")
        return Resp(200, "<html><body><form action='/login' method='post'><input name='uid'><input type='password' name='pw'></form>Sign in failed</body></html>")

def page(n, last=12):
    rows = "".join(f"<tr><td>Filler Product {n}-{i}</td><td>1.{i}</td><td>no maintenance</td></tr>" for i in range(3))
    if n == 7:
        rows += "<tr><td>Rocket TMON for z/OS</td><td>Your release</td><td>z/OS 3.2 requires PTF RT12345 and PTF RT12346; z/OS 2.5 requires PTF RT10001</td></tr>"
    if n == 11:
        rows += "<tr><td>Rocket Deep Product</td><td>2.0</td><td>z/OS 3.2: apply PTF RD55555</td></tr>"
    nxt = f'<a rel="next" href="/list?page={n+1}">Next</a>' if n < last else ""
    return f"<html><head><title>Compat list</title></head><body><table><tr><th>Product</th><th>Version</th><th>Note</th></tr>{rows}</table>{nxt}</body></html>"

def rocket_routes(url, http, kw):
    if url.startswith("https://www.rocketsoftware.com/list"):
        n = int(url.split("page=")[1]) if "page=" in url else 1
        return Resp(200, page(n))
    if url.startswith("https://www.rocketsoftware.com/node/9"):
        return Resp(200, "<html><body><p>Fix list: PTF RL99999 applies.</p></body></html>")
    return Resp(404, "")

ROWS_ROCKET = [{"product": "Rocket TMON for z/OS", "vrm": "Your release", "link": "https://www.rocketsoftware.com/list?page=1",
                "zos32": "Yes", "zos31": "Yes", "zos25": "Unverified"},
               {"product": "Rocket Deep Product", "vrm": "2.0", "link": "https://www.rocketsoftware.com/list?page=1",
                "zos32": "Yes", "zos31": "Unverified", "zos25": "Unverified"}]

def test_ids_ibm_and_generic():
    p, m, a = vs.extract_ids("Apply PTF UJ12345 and APAR PH45678 for z/OS 3.2. USERMOD UM00012 is optional.", "IBM")
    assert p == ["UJ12345"] and a == ["PH45678"] and m == ["UM00012"], (p, m, a)
    p, m, a = vs.extract_ids("Fix BPK1234 required. See ISO27001 and RFC1234.", "BMC")
    assert p == ["BPK1234"], p
    p, m, a = vs.extract_ids("Model ABC1234 shipped in 2024", "BMC")           # no fix keyword -> ignored
    assert p == [] and m == [] and a == []
    assert vs.zos_releases_in("Requires z/OS 3.2 and V2R5 but not z/OS 4.1") == ["3.2", "2.5"]

def test_pagination_ten_pages():
    http = FakeHttp(rocket_routes)
    res = vs.scrape_vendor("Rocket", ROWS_ROCKET, http=http, max_pages=10, follow_links=False)
    scraped = [p for p in res.pages if p.status == "Scraped"]
    assert len(scraped) == 10, len(scraped)                                      # page 1..10 searched
    tmon = res.rows[0]
    assert tmon.releases["3.2"].ptfs == ["RT12345", "RT12346"], tmon.releases["3.2"].ptfs
    assert tmon.releases["2.5"].ptfs == ["RT10001"] and "3.1" not in tmon.releases
    assert res.rows[1].note == "Product not found in the pages searched"          # lives on page 11
    res2 = vs.scrape_vendor("Rocket", ROWS_ROCKET, http=FakeHttp(rocket_routes), max_pages=12, follow_links=False)
    assert res2.rows[1].releases["3.2"].ptfs == ["RD55555"] and len([p for p in res2.pages if p.status == "Scraped"]) == 12
    res3 = vs.scrape_vendor("Rocket", ROWS_ROCKET, http=FakeHttp(rocket_routes), max_pages=3, follow_links=False)   # below minimum -> raised to 10
    assert len([p for p in res3.pages if p.status == "Scraped"]) == 10 and res3.max_pages == 10

def test_single_page_not_paginated():
    def routes(url, http, kw): return Resp(200, "<html><body><p>Fix UJ11111 for Foo Bar</p></body></html>")
    res = vs.scrape_vendor("IBM", [{"product": "Foo Bar", "vrm": "1.0", "link": "https://www.ibm.com/x", "zos32": "Yes", "zos31": "", "zos25": ""}],
                           http=FakeHttp(routes), follow_links=False)
    assert len(res.pages) == 1 and res.pages[0].note == "single page"
    assert res.rows[0].releases[vs.UNSPECIFIED].ptfs == ["UJ11111"]                  # no release named -> 'not stated'

def test_links_followed_and_kept_separate():
    def routes(url, http, kw):
        if url.endswith("/node/1"):
            return Resp(200, "<html><body><p>Product Zed 4.0: see <a href='/node/9'>fix list</a>. PTF RZ00001 for z/OS 3.2.</p></body></html>")
        return rocket_routes(url, http, kw)
    res = vs.scrape_vendor("Rocket", [{"product": "Product Zed", "vrm": "4.0", "link": "https://www.rocketsoftware.com/node/1",
                                       "zos32": "Yes", "zos31": "", "zos25": ""}], http=FakeHttp(routes))
    r = res.rows[0]
    assert r.releases["3.2"].ptfs == ["RZ00001"]
    assert r.linked[vs.UNSPECIFIED].ptfs == ["RL99999"]                               # from the hyperlinked page, release unknown
    flat = vs.flatten(res)
    ns = [f for f in flat if f["z/OS release"] == "Release not stated"][0]
    assert ns["Additional PTFs (linked pages)"] == "RL99999"

# ----------------------------------------------------------------------------- login
LOGIN_FORM = ("<html><body><form action='/login' method='post'><input type='hidden' name='csrf' value='tok'>"
              "<input type='text' name='uid'><input type='password' name='pw'></form></body></html>")

def bmc_routes(url, http, kw):
    if url == "https://docs.bmc.com/secure":
        if http.signed_in:
            return Resp(200, "<html><body><p>BMC AMI Ops for Db2 7.1: PTF BPK1234 for z/OS 3.2</p></body></html>")
        return Resp(200, LOGIN_FORM)
    if url == "https://docs.bmc.com/forbidden":
        return Resp(403, "")
    return Resp(404, "")

ROW_BMC = [{"product": "BMC AMI Ops for Db2", "vrm": "7.1", "link": "https://docs.bmc.com/secure", "zos32": "Yes", "zos31": "", "zos25": ""}]

def test_login_required_then_success():
    http = FakeHttp(bmc_routes)
    res = vs.scrape_vendor("BMC", ROW_BMC, http=http, follow_links=False)
    assert res.login_required == ["https://docs.bmc.com/secure"] and res.pages[0].status == "Login required"
    assert "user name and password" in res.pages[0].note and res.rows[0].note.startswith("Login required")
    http = FakeHttp(bmc_routes)
    res = vs.scrape_vendor("BMC", ROW_BMC, creds=vs.Credentials("alice", "good-pass"), http=http, follow_links=False)
    assert res.login_required == [] and res.rows[0].releases["3.2"].ptfs == ["BPK1234"], res.pages
    url, data = http.posts[0]
    assert url == "https://docs.bmc.com/login" and data == {"csrf": "tok", "uid": "alice", "pw": "good-pass"}   # hidden field carried over

def test_login_wrong_password_and_message():
    http = FakeHttp(bmc_routes)
    res = vs.scrape_vendor("BMC", ROW_BMC, creds=vs.Credentials("alice", "bad"), http=http, follow_links=False)
    assert res.login_required and "not accepted" in res.pages[0].note and res.rows[0].releases == {}
    assert "bad" not in repr(vs.Credentials("alice", "bad")) and "bad" not in str(res.pages) and "bad" not in str(vs.flatten(res))

def test_http_403_login_required_and_basic_auth_scoping():
    rows = [{"product": "X Y", "vrm": "1", "link": "https://docs.bmc.com/forbidden", "zos32": "", "zos31": "", "zos25": ""}]
    res = vs.scrape_vendor("BMC", rows, http=FakeHttp(bmc_routes), follow_links=False)
    assert res.login_required == ["https://docs.bmc.com/forbidden"]
    http = FakeHttp(bmc_routes)
    vs.scrape_vendor("BMC", rows, creds=vs.Credentials("u", "p", method="basic"), http=http, follow_links=False)
    assert http.calls[0][1]["auth"] == ("u", "p")
    # credentials are never offered to a host outside the vendor's list
    f = vs.Fetcher(vs.PROFILES["BMC"], vs.Credentials("u", "p", method="basic", cookie="SID=1"), FakeHttp(bmc_routes))
    assert f._auth("https://evil.example.com/x") is None and "Cookie" not in f._headers("https://evil.example.com/x")
    assert f.get("https://evil.example.com/x")[2].startswith("Blocked")

def test_redirect_to_foreign_sso_is_login_required():
    def routes(url, http, kw): return Resp(302, "", headers={"Location": "https://sso.thirdparty.example/login?next=1"})
    f = vs.Fetcher(vs.PROFILES["Rocket"], http=FakeHttp(routes))
    st = f.get("https://www.rocketsoftware.com/support")[2]
    assert st.startswith("Login required")

def test_login_form_posting_to_foreign_host_refused():
    form = "<form action='https://evil.example.com/steal'><input name='uid'><input type='password' name='pw'></form>"
    def routes(url, http, kw): return Resp(200, f"<html><body>{form}</body></html>")
    http = FakeHttp(routes)
    res = vs.scrape_vendor("BMC", ROW_BMC, creds=vs.Credentials("alice", "good-pass"), http=http, follow_links=False)
    assert http.posts == [] and "outside this vendor's approved hosts" in res.pages[0].note

# ----------------------------------------------------------------------------- PDFs
def make_pdf(pages):
    from reportlab.pdfgen import canvas
    buf = io.BytesIO(); c = canvas.Canvas(buf)
    for i in range(pages):
        c.drawString(72, 750, f"Page {i+1} filler text about nothing")
        if i == 8:
            c.drawString(72, 700, "Rocket Zeke 14.0 requires PTF RK00042 on z/OS 3.2")
        if i == 14:
            c.drawString(72, 700, "Rocket Late Product 1.0 requires PTF RK00099")
        c.showPage()
    c.save(); return buf.getvalue()

def test_pdf_ten_plus_pages():
    pdf = make_pdf(20)
    def routes(url, http, kw): return Resp(200, pdf, ctype="application/pdf")
    rows = [{"product": "Rocket Zeke", "vrm": "14.0", "link": "https://www.rocketsoftware.com/a.pdf", "zos32": "", "zos31": "", "zos25": ""},
            {"product": "Rocket Late Product", "vrm": "1.0", "link": "https://www.rocketsoftware.com/a.pdf", "zos32": "", "zos31": "", "zos25": ""}]
    res = vs.scrape_vendor("Rocket", rows, http=FakeHttp(routes), pdf_pages=10, follow_links=False)
    assert res.rows[0].releases["3.2"].ptfs == ["RK00042"]                       # on page 9: inside the first 10
    assert res.rows[1].evidence == 0 and "PDF pages searched: 10 of 20" in res.pages[0].note
    res = vs.scrape_vendor("Rocket", rows, http=FakeHttp(routes), pdf_pages=30, follow_links=False)
    assert res.rows[1].releases[vs.UNSPECIFIED].ptfs == ["RK00099"] and "20 of 20" in res.pages[0].note

if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("PASS", n)
