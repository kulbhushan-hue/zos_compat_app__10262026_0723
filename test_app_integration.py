"""Runs the real Streamlit app headlessly with the network replaced by the offline fixtures."""
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tests"))
import requests
import broadcom_scraper as bs
import test_scraper as t

def no_network(*a, **k):
    raise requests.ConnectionError("offline test")
requests.get = no_network
requests.Session.get = no_network

def fake(url, session=None):
    if url.split("#")[0].endswith("zos_compat.HTML"):
        return (t.FX / "grid.html").read_bytes(), "text/html", "Fetched"
    return t.fake_fetch(url, session)
bs.fetch = fake

import vendor_scraper as vsc
import test_vendor_scraper as tv

def vendor_routes(url, http, kw):
    if "rocketsoftware.com" in url:
        return tv.Resp(200, "<html><body><p>Rocket TMON for z/OS: z/OS 3.2 requires PTF RT12345.</p><p>ASG-Zeke now Rocket Zeke needs PTF RK77777 on z/OS 3.1.</p></body></html>")
    if "bmc.com" in url:
        if http.signed_in:
            return tv.Resp(200, "<html><body><p>BMC AMI Ops for Db2 7.1: PTF BPK1234 for z/OS 3.2</p></body></html>")
        return tv.Resp(200, tv.LOGIN_FORM)
    return tv.Resp(404, "")
vsc.requests.Session = lambda: tv.FakeHttp(vendor_routes)

from streamlit.testing.v1 import AppTest
import os
os.chdir(ROOT)
at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
assert not at.exception, [e.value for e in at.exception]
print("app ran; tabs:", [t_.label for t_ in at.tabs])

import vendor_details as vd
df = vd.CompatibilityDB.load(str(ROOT / "data")).df if hasattr(vd, "CompatibilityDB") else None
from compatibility_db import CompatibilityDB, to_output, build_excel
db = CompatibilityDB.load(str(ROOT / "data"))
enriched, stats = vd.enrich_vendor_details(db.df)
print(stats)
sub = enriched[enriched["vendor"] == "Broadcom"]
hit = sub[(sub["ptf_ids_32"] != "") | (sub["ptf_ids_31"] != "") | (sub["ptf_ids_25"] != "")]
print("broadcom rows with IDs:", len(hit))
print(hit[["product", "vrm", "ptf_required", "ptf_ids_32", "usermod_ids_32", "ptf_ids_31", "ptf_ids_25"]].head(8).to_string())
row = enriched[(enriched["product"] == "Dispatch") & (enriched["vrm"] == "11.7")].iloc[0]
assert row["ptf_ids_32"] == "LU18025, LU18027, LU02931, LU11099", row["ptf_ids_32"]
assert row["ptf_required"].startswith("Yes - LU18025"), row["ptf_required"]
aud = enriched[(enriched["product"] == "Auditor for z/OS") & (enriched["vrm"] == "12.1")].iloc[0]
assert aud["usermod_ids_32"] == "UO12345", aud["usermod_ids_32"]
out = to_output(hit, version="3.2")
assert list(out.columns)[5:8] == ["PTF IDs", "USERMOD / SYSMOD IDs", "Additional PTFs (linked pages)"]
xl = build_excel({"Test": hit}, version="3.2")
open("/home/claude/dashboard_excel_test.xlsx", "wb").write(xl)
# untouched vendors keep working
assert (enriched[enriched["vendor"] == "IBM"]["maintenance_details"].str.len() > 0).all()
print("INTEGRATION OK")

# ---- scraper tab + PTF detail table through the real UI
at.button(key="sc_run").click().run()
assert not at.exception, [e.value for e in at.exception]
assert len(at.session_state["scrape_result"].records) > 0
at.button(key="pt_run").click().run()
assert not at.exception, [e.value for e in at.exception]
table, msg = at.session_state["ptf_table"]
print(msg); print(table[["#","Product / Release","PTF ID","FMID","PTF publish date","Detail Extraction Status"]].head(10).to_string())
assert len(table) == 10 and list(table.columns[:10]) == __import__("ptf_details").TABLE_COLUMNS
assert (table["FMID"] == "Not accessible").all()
print("UI TABLE OK")


# ---- all-vendors tab: login required -> enter credentials -> retry
at.button(key="vs_run").click().run()
assert not at.exception, [e.value for e in at.exception]
sc = at.session_state["vendor_scrapes"]
assert sc["BMC"].login_required, "BMC pages should ask for a login"
assert any("Login required" in w.value for w in at.warning), [w.value for w in at.warning]
rk = next(r for r in sc["Rocket"].rows if r.product == "Rocket TMON for z/OS")
assert rk.releases["3.2"].ptfs == ["RT12345"], rk.releases
at.text_input(key="vs_user_BMC").set_value("alice")
at.text_input(key="vs_pw_BMC").set_value("good-pass")
at.button(key="vs_run").click().run()
assert not at.exception, [e.value for e in at.exception]
bmc = at.session_state["vendor_scrapes"]["BMC"]
assert not bmc.login_required, bmc.pages
hit = next(r for r in bmc.rows if r.product == "BMC AMI Ops for Db2" and r.vrm == "7.1")
assert hit.releases["3.2"].ptfs == ["BPK1234"], hit.releases
print("VENDOR TAB OK")

# ---- start-up enrichment fills the dashboard columns for the other vendors too
enriched2, stats2 = vd.enrich_vendor_details(db.df)
print(stats2["vendors"])
roc = enriched2[(enriched2["vendor"] == "Rocket") & (enriched2["product"] == "Rocket TMON for z/OS")].iloc[0]
assert roc["ptf_ids_32"] == "RT12345", roc["ptf_ids_32"]
print("STARTUP VENDOR ENRICH OK")
