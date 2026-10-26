"""Offline tests: run with  python tests/test_scraper.py   (or pytest)."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import broadcom_scraper as bs

FX = pathlib.Path(__file__).parent / "fixtures"
BASE = "https://ftpdocs.broadcom.com/phpdocs/0/MSPSaccount/COMPAT/"
ART = "https://knowledge.broadcom.com/external/article/999999/sdsf-external-security.html"


def fake_fetch(url, session=None):
    url = url.split("#")[0]
    if url == ART:
        return (FX / "ARTICLE").read_bytes(), "text/html", "Fetched"
    if url.startswith(BASE) and (FX / url.rsplit("/", 1)[1]).exists():
        return (FX / url.rsplit("/", 1)[1]).read_bytes(), "text/html", "Fetched"
    return b"", "", "HTTP 404"


def run(name="grid.html", **kw):
    bs.fetch = fake_fetch
    return bs.scrape_grid(html=(FX / name).read_bytes(), **kw)


def by_name(res, needle):
    return next(r for r in res.records if needle in r.name)


def test_ids():
    p, u, o = bs.extract_ids("Requires CA Dispatch 11.6 PTFs LU18024, LU18026 and LU02959.")
    assert p == ["LU18024", "LU18026", "LU02959"], p
    p, u, o = bs.extract_ids("z/OS maintenance UA95552 for z/OS 2.1 introduced an incompatibility. Apply SO04036")
    assert p == ["SO04036"] and o == ["UA95552"], (p, o)
    p, u, o = bs.extract_ids("USERMOD UO12345 must be applied")
    assert u == ["UO12345"] and p == [], (p, u)
    p, u, o = bs.extract_ids("ESP 12.0.08 and S0C4 ABEND B78 STGINIT(00) CAJ0C10")
    assert (p, u, o) == ([], [], []), (p, u, o)


def test_grid_parse_and_sections():
    res = run()
    assert len(res.records) == 22, len(res.records)
    cvb = by_name(res, "Compress Data Compression 5.5")
    assert set(cvb.releases) == {"3.2", "3.1", "2.5"}
    assert cvb.releases["3.2"].ptfs == ["RO60438", "RO90244", "SO01425", "LU08340"], cvb.releases["3.2"].ptfs
    disp = by_name(res, "Dispatch 11.6")
    assert disp.releases["3.2"].ptfs == ["LU18024", "LU18026", "LU02959"], disp.releases["3.2"].ptfs
    assert by_name(res, "Dispatch 11.7").releases["3.1"].ptfs == ["LU10974", "LU10975", "LU02931", "LU11099"]
    assert by_name(res, "Earl 6.1").releases["3.2"].ptfs[:2] == ["LU11148", "LU11149"]
    aud = by_name(res, "Auditor for z/OS 12.1")
    assert aud.releases["3.2"].usermods == ["UO12345"], aud.releases["3.2"].usermods
    assert by_name(res, "Auditor for z/OS 12.0").releases["3.2"].status == "In Progress"
    ca1 = by_name(res, "Tape Management 12.6")
    assert ca1.name.endswith("(End Of Service)") and ca1.clean_name == "CA 1 Tape Management 12.6" and ca1.vrm == "12.6"
    assert ca1.releases["2.5"].status == "N/A"
    fm = by_name(res, "File Master Plus 11.0")
    assert fm.releases["2.5"].ptfs == ["SO04036"] and fm.releases["2.5"].other_ids == ["UA95552", "UA95553", "UA95551"], fm.releases["2.5"]
    assert by_name(res, "Bundl 5.0").clean_name == "Bundl 5.0"


def test_follow_links():
    res = run(follow_links=True)
    acf = by_name(res, "ACF2 for z/OS 16.0")
    r = acf.releases["2.5"]
    assert ART in r.linked_urls, r.linked_urls
    assert "LU99887" in r.linked_ptfs and "RO11111" not in r.linked_ptfs, r.linked_ptfs   # irrelevant ID on same page ignored
    ca1 = by_name(res, "Flexible Storage 15.0")
    assert "LU18196" in ca1.releases["3.2"].linked_ptfs and "LU18187" not in ca1.releases["3.2"].linked_ptfs   # grid PTFs not repeated
    disp = by_name(res, "Dispatch 11.6")
    assert "LU18027" in disp.releases["3.2"].linked_ptfs


def test_snapshot_no_follow():
    res = run("grid_snapshot.html", follow_links=False)
    assert 10 <= len(res.records) <= 16
    for rec in res.records:
        for rel in rec.releases.values():
            assert rel.linked_ptfs == []
    ca1 = by_name(res, "Flexible Storage 15.0").releases["3.2"]
    assert ca1.ptfs == ["LU18187"], ca1.ptfs


def test_url_policy():
    assert bs.allowed_url("https://ftpdocs.broadcom.com/phpdocs/x.HTML")
    assert not bs.allowed_url("http://ftpdocs.broadcom.com/x")
    assert not bs.allowed_url("https://evil.example.com/x")
    assert not bs.allowed_url("https://broadcom.com.evil.example.com/x")
    assert not bs.allowed_url("https://user:pw@ftpdocs.broadcom.com/x")


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("PASS", n)
