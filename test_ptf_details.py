import pathlib, sys, io, os
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import broadcom_scraper as bs
import ptf_details as pd_

# --- rows copied from the live "Mainframe Products Solutions List" page (2026-10-25 fetch)
CATALOG_TEXT = ("Product Name Release Published Date PTF Description Feature HIPER PE CARSID SECINT "
 "DYNAMIC CAPACITY INTELLIGENCE 2.0 2023-10-26 LU11787 DCI 2.0 WEB UI - FIX FOR SAVED URL ISSUES N N N CAR2311 N "
 "Deliver 14.0 2023-10-26 LU11750 ERRONEOUS RMOCPT17 MESSAGES AFTER APAR LU09773 N N N CAR2311 N "
 "SYSVIEW Performance Management Option for Db2 for z/OS 20.0 2023-10-27 LU11619 SUPPORT FOR ADDITIONAL OP BUFFER DESTINATIONS OP9 TO OP16 Y N Y CAR2311 N "
 "Top Secret for z/OS 16.0 2023-10-31 LU11668 SECURITY OR INTEGRITY PROBLEM N N N CAR2311 Y "
 "z/OS APM Bridge 1.0 2023-10-30 LU11810 VULNERABILITIES REPORTED ON SEVERAL PACKAGES N N N N "
 "WLA Agent Manager 1.0 2023-12-07 LU12175 WLA AGENT MANAGER RELEASE 1.0.1 N N N CAR2509 Y")

def test_catalog_text():
    c = pd_.parse_catalog(CATALOG_TEXT)
    assert set(c) == {"LU11787","LU11750","LU11619","LU11668","LU11810","LU12175"}, sorted(c)
    e = c["LU11619"]
    assert (e.product, e.release, e.published, e.feature, e.hiper, e.pe, e.carsid) == (
        "SYSVIEW Performance Management Option for Db2 for z/OS", "20.0", "2023-10-27", "Y", "N", "Y", "CAR2311"), e
    assert c["LU11668"].secint == "Y" and c["LU11668"].description == "SECURITY OR INTEGRITY PROBLEM"
    assert c["LU11810"].carsid == "" and c["LU11810"].description.startswith("VULNERABILITIES")

def test_catalog_html_table():
    html = ("<table><tr><th>Product Name</th><th>Release</th><th>Published Date</th><th>PTF</th><th>Description</th>"
            "<th>Feature</th><th>HIPER</th><th>PE</th><th>CARSID</th><th>SECINT</th></tr>"
            "<tr><td>File Master Plus</td><td>12.0</td><td>2026-10-22</td><td>LU22137</td><td>SOME FIX</td><td>N</td><td>Y</td><td>N</td><td>CAR2611</td><td>N</td></tr></table>")
    c = pd_.parse_catalog(html)
    assert c["LU22137"].product_release == "File Master Plus 12.0" and c["LU22137"].hiper == "Y" and c["LU22137"].published == "2026-10-22"

def test_detail_parse_and_classify():
    page = """PTF: LU22137
FMID: CDBIC01
Published Date: 2026-10-22
APAR: RO12345
Prerequisites: LU22000, LU22001
Superseded by: LU22200
Description: ABEND S0C4 IN MODULE XYZ WHEN LOADING"""
    v = pd_.parse_detail_text(page)
    assert v["fmid"] == "CDBIC01" and v["published"] == "2026-10-22"
    assert v["prerequisites"] == "LU22000, LU22001" and v["superseded_by"] == "LU22200"
    assert v["description"].startswith("ABEND S0C4") and pd_.classify(v) == "Verified"
    assert pd_.classify({"fmid": "CDBIC01"}) == "Partial" and pd_.classify({}) == "Not found in source"
    assert "fmid" not in pd_.parse_detail_text("nothing useful here")

def test_smpe():
    v = pd_.parse_smpe_ver("++PTF(LU22137) . ++VER(Z038) FMID(CDBIC01) PRE(LU22000 LU22001) SUP(LU11111,LU11112) .")
    assert v == {"fmid": "CDBIC01", "prerequisites": "LU22000, LU22001", "supersedes": "LU11111, LU11112"}, v

def test_access_denied_and_fetch(monkeypatch=None):
    os.environ["BROADCOM_PTF_DETAIL_URL"] = "https://support.broadcom.com/solution/{ptf}"
    os.environ["BROADCOM_SUPPORT_COOKIE"] = "SESSION=abc"
    seen = {}
    def fake(url, session=None, headers=None):
        seen[url] = headers
        if url.endswith("LU1"+"0001"): return b"", "", "HTTP 403"
        if url.endswith("LU10002"): return b"<html><body>Please sign in to continue</body></html>", "text/html", "Fetched"
        if url.endswith("LU10003"): return b"", "", "Fetch failed: ConnectionError"
        if url.endswith("LU10004"): return b"<html><body><p>LU10004</p><p>FMID: CABCD01</p><p>Description: GOOD FIX</p></body></html>", "text/html", "Fetched"
        return b"<html><body><p>LU10005 has no labelled fields</p></body></html>", "text/html", "Fetched"
    bs.fetch = fake
    r = pd_.gather_details(["LU10001","LU10002","LU10003","LU10004","LU10005"])
    assert r["LU10001"].status == "Access denied"
    assert r["LU10002"].status == "Access denied"
    assert r["LU10003"].status == "Fetch failed"
    assert r["LU10004"].status == "Partial" and r["LU10004"].values["fmid"] == "CABCD01"
    assert r["LU10005"].status == "Not found in source"
    assert seen["https://support.broadcom.com/solution/LU10004"] == {"Cookie": "SESSION=abc"}
    os.environ.pop("BROADCOM_PTF_DETAIL_URL"); os.environ.pop("BROADCOM_SUPPORT_COOKIE")
    assert pd_.fetch_detail("LU10009").status == "Not attempted"

def test_table_layout():
    cat = pd_.parse_catalog(CATALOG_TEXT)
    det = {"LU11787": pd_.PtfDetail("LU11787", {"fmid": "CXYZ100", "published": "2023-10-26"}, "Partial", "uploaded detail export"),
           "LU11750": pd_.PtfDetail("LU11750", {}, "Access denied", "", "HTTP 403")}
    sel = [("LU11787","DCI 2.0","z/OS 3.2"),("LU11750","Deliver 14.0",""),("LU99999","Mystery 1.0","z/OS 3.1")]
    t = pd_.build_table(sel, cat, det)
    assert list(t.columns[:10]) == pd_.TABLE_COLUMNS
    r0, r1, r2 = t.iloc[0], t.iloc[1], t.iloc[2]
    assert r0["FMID"] == "CXYZ100" and r0["APAR ID"] == "Not found in source" and r0["Detail Extraction Status"].startswith("Partial")
    assert r1["FMID"] == "Not accessible" and r1["Detail Extraction Status"].startswith("Access denied")
    assert r1["PTF publish date"] == "2023-10-26"            # from the public catalog
    assert r2["Product / Release"] == "Mystery 1.0" and r2["PTF publish date"] == "Not accessible"

def test_export_roundtrip():
    csv = "PTF ID,FMID,PTF publish date\nLU22137,CDBIC01,2026-10-22\nbad,X,Y\n"
    d = pd_.load_detail_export(io.StringIO(csv))
    assert list(d) == ["LU22137"] and d["LU22137"].values == {"fmid": "CDBIC01", "published": "2026-10-22"} and d["LU22137"].status == "Partial"

if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("PASS", n)
