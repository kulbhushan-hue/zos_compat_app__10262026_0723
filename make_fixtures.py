"""Builds an offline copy of the Broadcom grid structure from rows copied from the public page
(snapshot fetched 2026-10-25) so the scraper can be tested without network access."""
BASE = "https://ftpdocs.broadcom.com/phpdocs/0/MSPSaccount/COMPAT/"
REL = [("IN000135", "3.2"), ("IN000119", "3.1"), ("IN000098", "2.5")]

# name, product page, code(for anchor ids), cells: per release (status, has_ptf, has_info)
ROWS = [
 ("ACF2 for z/OS 16.0", "ACF", "ACF160", [("YES",1,0),("YES",1,0),("YES",1,1)]),
 ("ACF2 for z/OS 17.0", "ACF", "ACF170", [("YES",0,0),("YES",0,0),("YES",0,1)]),
 ("ACF2 Option for Db2 1.3", "ACP", "ACP013", [("YES",0,0),("YES",0,0),("YES",0,0)]),
 ("Auditor for z/OS 12.0", "AUD", "AUD120", [("In Progress",0,0),("YES",0,0),("YES",0,0)]),
 ("Auditor for z/OS 12.1", "AUD", "AUD121", [("YES",1,0),("YES",1,0),("YES",1,0)]),
 ("Bundl 5.0 (End Of Life)", "BZV", "BZV050", [("YES",0,0),("YES",0,1),("YES",0,1)]),
 ("CA 1 Flexible Storage 15.0", "AL0", "AL0150", [("YES",1,1),("YES",0,0),("YES",0,0)]),
 ("CA 1 Tape Management 12.6 (End Of Service)", "AL0", "AL0126", [("NO",0,0),("NO",0,0),("N/A",0,0)]),
 ("CA 1 Tape Management 14.0 (End Of Service)", "AL0", "AL0140", [("YES",1,1),("YES",0,1),("YES",0,1)]),
 ("Compress Data Compression 5.5", "CVB", "CVB055", [("YES",0,1),("YES",1,1),("YES",1,1)]),
 ("Disk Backup and Restore 14.0", "CUW", "CUW140", [("YES",1,0),("YES",1,1),("YES",1,0)]),
 ("Dispatch 11.6", "ADS", "ADS116", [("YES",1,1),("YES",1,1),("YES",1,1)]),
 ("Dispatch 11.7", "ADS", "ADS117", [("YES",1,1),("YES",1,1),("YES",1,1)]),
 ("Earl 6.1", "ERL", "ERL061", [("YES",0,1),("YES",0,1),("YES",0,0)]),
 ("Easytrieve Report Generator 11.6", "EZT", "EZT116", [("YES",1,1),("YES",1,1),("YES",1,1)]),
 ("ESP Workload Automation 12.0", "D7Y", "D7Y120", [("YES",0,1),("YES",0,0),("YES",0,0)]),
 ("File Master Plus 11.0", "FMP", "FMP110", [("NO",0,0),("YES",0,1),("YES",0,1)]),
 ("JMR 4.6", "JMR", "JMR046", [("YES",0,0),("YES",0,1),("YES",0,1)]),
 ("JOBTRAC 11.0", "BRR", "BRR110", [("YES",1,1),("YES",0,0),("YES",0,1)]),
 ("Endevor SCM 18.1", "SCM", "SCM181", [("YES",1,0),("YES",1,0),("YES",1,0)]),
 ("DADS Plus 4.0", "EJT", "DAD040", [("YES",0,0),("YES",0,1),("YES",0,1)]),
 ("Datacom DB Core 15.1", "DCM", "DCM151", [("YES",0,0),("YES",0,0),("YES",0,1)]),
]
# Rows whose every linked cell has text copied from the live page snapshot (no invented IDs)
SNAPSHOT_CODES = {"ACF170","AL0150","AL0140","CVB055","ADS116","ADS117","ERL061","EZT116","D7Y120","FMP110","JMR046","BRR110","BZV050","DAD040","DCM151"}
# Sections invented ONLY for unit tests of the PTF-list code path (never used in the sample workbook)
SYNTHETIC = {("ACF160","3.2"),("ACF160","3.1"),("AUD121","3.2"),("AUD121","3.1"),("AUD121","2.5"),("SCM181","3.2"),("SCM181","3.1"),("SCM181","2.5")}

# Text of the "Additional Information"/"Required PTF(s)" sections, taken from the live page snapshot
# (key = (code, release) ). Where the PTF list was truncated in the snapshot the IDs come from the
# matching Fix Category entry of the same product/release.
SECTIONS = {
 ("ACF160","3.2"): ("ACF2 for z/OS 16.0","CA.TargetSystem-RequiredService.z/OS.V3R2","LU18900 LU18901", "ptf"),
 ("ACF160","3.1"): ("ACF2 for z/OS 16.0","CA.TargetSystem-RequiredService.z/OS.V3R1","LU11299", "ptf"),
 ("ACF160","2.5"): ("ACF2 for z/OS 16.0","CA.TargetSystem-RequiredService.z/OS.V2R5","Starting with z/OS 2.5, System Display and Search Facility (SDSF) only uses SAF for security decisions. See article to enable SDSFExternalSecurity", "info"),
 ("AL0150","3.2"): ("CA 1 Flexible Storage 15.0","CA.TargetSystem-RequiredService.z/OS.V3R2","LU18187","ptf"),
 ("AL0140","3.2"): ("CA 1 Tape Management 14.0","CA.TargetSystem-RequiredService.z/OS.V3R2","LU18196","ptf"),
 ("AL0140","3.1"): ("CA 1 Tape Management 14.0","CA.TargetSystem-RequiredService.z/OS.V3R1","RO94173","info"),
 ("AL0140","2.5"): ("CA 1 Tape Management 14.0","CA.TargetSystem-RequiredService.z/OS.V2R5","RO94642 RO94173","info"),
 ("CVB055","3.2"): ("Compress Data Compression 5.5","CA.TargetSystem-RequiredService.z/OS.V3R2","The following Solutions are required:\nRO60438 ( S0C4 WRITING SYSOUT TO DASD WITH WRONG DCB )\nRO90244 ( VARIOUS OPEN S0C4 AND SWA=ABOVE ABENDS )\nSO01425 ( S0C4 ABEND ACCESSING SVC REQUESTS RESIDING ABOVE THE LINE\nLU08340 ( SF6F ABEND UPDATING OR ADDING RECORDS ON Z/OS 2.5 )","info"),
 ("CVB055","3.1"): ("Compress Data Compression 5.5","CA.TargetSystem-RequiredService.z/OS.V3R1","The following Solutions are required:\nRO60438 ( S0C4 WRITING SYSOUT TO DASD WITH WRONG DCB )\nRO90244 ( VARIOUS OPEN S0C4 AND SWA=ABOVE ABENDS )\nSO01425 ( S0C4 ABEND ACCESSING SVC REQUESTS RESIDING ABOVE THE LINE\nLU08340 ( SF6F ABEND UPDATING OR ADDING RECORDS ON Z/OS 2.5 )","ptf"),
 ("CVB055","2.5"): ("Compress Data Compression 5.5","CA.TargetSystem-RequiredService.z/OS.V2R5","The following Solutions are required:\nRO60438 ( S0C4 WRITING SYSOUT TO DASD WITH WRONG DCB )\nRO90244 ( VARIOUS OPEN S0C4 AND SWA=ABOVE ABENDS )\nSO01425 ( S0C4 ABEND ACCESSING SVC REQUESTS RESIDING ABOVE THE LINE\nLU08340 ( SF6F ABEND UPDATING OR ADDING RECORDS ON Z/OS 2.5 )","ptf"),
 ("CUW140","3.1"): ("Disk Backup and Restore 14.0","CA.TargetSystem-RequiredService.z/OS.V3R1","Requires Disk 14.0 PTF LU11497, which provides the JCL to install SVC zaps for z/OS 3.1.","info"),
 ("ADS116","3.2"): ("Dispatch 11.6","CA.TargetSystem-RequiredService.z/OS.V3R2","Requires CA Dispatch 11.6 PTFs LU18024, LU18026 and LU02959.\nIf running z/OS 3.2 or upgrading to z/OS 3.2, all Dispatch users must define CA-Dispatch to run in an alternate storage protection key (0 thru 7).","info"),
 ("ADS117","3.2"): ("Dispatch 11.7","CA.TargetSystem-RequiredService.z/OS.V3R2","Requires CA Dispatch 11.7 PTFs LU18025, LU18027, LU02931 and LU11099.","info"),
 ("ERL061","3.2"): ("Earl 6.1","CA.TargetSystem-RequiredService.z/OS.V3R2","The following PTFs need to be installed:\nLU11148\nLU11149 (Required if FMID CEO6102 is installed)\nLU11150 (EARL-MVS Common Component)\nLU14752 (SRAM-MVS Common Component)\nLU14847 (EARL-MVS Common Component)\nLU14875 (EARL-MVS Common Component)","info"),
 ("EZT116","3.2"): ("Easytrieve Report Generator 11.6","CA.TargetSystem-RequiredService.z/OS.V3R2","Please ensure product solution RO94347 is installed.\nPlease note: Release 11.6 including 11.6-C has been certified.","info"),
 ("D7Y120","3.2"): ("ESP Workload Automation 12.0","CA.TargetSystem-RequiredService.z/OS.V3R2","ESP 12.0.08","info"),
 ("FMP110","3.1"): ("File Master Plus 11.0","CA.TargetSystem-RequiredService.z/OS.V3R1","SO04036","info"),
 ("FMP110","2.5"): ("File Master Plus 11.0","CA.TargetSystem-RequiredService.z/OS.V2R5","z/OS maintenance UA95552 for z/OS 2.1, UA95553 for z/OS 2.2 and UA95551 for z/OS 2.3 introduced an incompatibility. Apply following fixes to prevent the problem:\nSO04036 for File Master Plus version 11.0","info"),
 ("JMR046","3.1"): ("JMR 4.6","CA.TargetSystem-RequiredService.z/OS.V3R1","CA JMR r4.6 is certified with PTF RO37293 ,RO36167 and RO26783 applied.\nJMR cannot be run with DIAG TRAP STGINIT(FF).","info"),
 ("BRR110","3.2"): ("JOBTRAC 11.0","CA.TargetSystem-RequiredService.z/OS.V3R2","Need PTF LU17722 if using JCLTRAC","ptf"),
 ("BRR110","2.5"): ("JOBTRAC 11.0","CA.TargetSystem-RequiredService.z/OS.V2R5","RO90204 RO95872","info"),
 ("AUD121","3.2"): ("Auditor for z/OS 12.1","CA.TargetSystem-RequiredService.z/OS.V3R2","Auditor for z/OS (CAJ0C10)\nUSERMOD UO12345 must be applied for the SVC change.","ptf"),
 ("AUD121","3.1"): ("Auditor for z/OS 12.1","CA.TargetSystem-RequiredService.z/OS.V3R1","Auditor for z/OS (CAJ0C10)","ptf"),
 ("AUD121","2.5"): ("Auditor for z/OS 12.1","CA.TargetSystem-RequiredService.z/OS.V2R5","Auditor for z/OS (CAJ0C10)","ptf"),
 ("SCM181","3.2"): ("Endevor SCM 18.1","CA.TargetSystem-RequiredService.z/OS.V3R2","SO09911 SO09912","ptf"),
 ("SCM181","3.1"): ("Endevor SCM 18.1","CA.TargetSystem-RequiredService.z/OS.V3R1","SO09911","ptf"),
 ("SCM181","2.5"): ("Endevor SCM 18.1","CA.TargetSystem-RequiredService.z/OS.V2R5","SO09910","ptf"),

 ("ADS116","3.1"): ("Dispatch 11.6","CA.TargetSystem-RequiredService.z/OS.V3R1","Requires CA Dispatch 11.6 PTFs LU10976, LU10977 and LU02959.","info"),
 ("ADS116","2.5"): ("Dispatch 11.6","CA.TargetSystem-RequiredService.z/OS.V2R5","Requires CA Dispatch 11.6 PTFs LU02788, LU02789 and LU02959.","info"),
 ("ADS117","3.1"): ("Dispatch 11.7","CA.TargetSystem-RequiredService.z/OS.V3R1","Requires CA Dispatch 11.7 PTFs LU10974, LU10975, LU02931 and LU11099.","info"),
 ("ADS117","2.5"): ("Dispatch 11.7","CA.TargetSystem-RequiredService.z/OS.V2R5","Requires CA Dispatch 11.7 PTFs LU02786, LU02787, LU02931 and LU11099.","info"),
 ("ERL061","3.1"): ("Earl 6.1","CA.TargetSystem-RequiredService.z/OS.V3R1","The following PTFs need to be installed:\nLU11148\nLU11149 (Required if FMID CEO6102 is installed)\nLU11150 (EARL-MVS Common Component)\nLU14752 (SRAM-MVS Common Component)\nLU14847 (EARL-MVS Common Component)\nLU14875 (EARL-MVS Common Component)","info"),
 ("EZT116","3.1"): ("Easytrieve Report Generator 11.6","CA.TargetSystem-RequiredService.z/OS.V3R1","Please ensure product solution RO94347 is installed.\nPlease note: Release 11.6 including 11.6-C has been certified.","info"),
 ("EZT116","2.5"): ("Easytrieve Report Generator 11.6","CA.TargetSystem-RequiredService.z/OS.V2R5","Please ensure product solution RO94347 is installed.","info"),
 ("JMR046","2.5"): ("JMR 4.6","CA.TargetSystem-RequiredService.z/OS.V2R5","CA JMR r4.6 is certified with PTF RO37293 ,RO36167 and RO26783 applied.\nJMR cannot be run with DIAG TRAP STGINIT(FF).","info"),
 ("BZV050","3.1"): ("Bundl 5.0 (End Of Life","CA.TargetSystem-RequiredService.z/OS.V3R1","Requires L-Serv 14.0 Common component w/TNG Framew (CBUJE00) PTF LU00348","info"),
 ("BZV050","2.5"): ("Bundl 5.0 (End Of Life","CA.TargetSystem-RequiredService.z/OS.V2R5","Requires L-Serv 14.0 Common component w/TNG Framew (CBUJE00) PTF LU00348","info"),
 ("ACF170","2.5"): ("ACF2 for z/OS 17.0","CA.TargetSystem-RequiredService.z/OS.V2R5","Starting with z/OS 2.5, System Display and Search Facility (SDSF) only uses SAF for security decisions. See article to enable SDSFExternalSecurity","info"),
 ("DAD040","3.1"): ("DADS Plus 4.0","CA.TargetSystem-RequiredService.z/OS.V3R1","All service packs + QO91208","info"),
 ("DAD040","2.5"): ("DADS Plus 4.0","CA.TargetSystem-RequiredService.z/OS.V2R5","All service packs + QO91208","info"),
 ("DCM151","2.5"): ("Datacom DB Core 15.1","CA.TargetSystem-RequiredService.z/OS.V2R5","CA DATACOM/DB AND CA DATACOM/AD BOTH REQUIRE THE FOLLOWING PTF:\nLU02640 DB 15.1 S047 ABEND RUNNING COBOL PRECOMPILER DBXMMPR IN Z/OS 2.5","info"),
}
EXT_LINKS = {("ACF160","2.5"): "https://knowledge.broadcom.com/external/article/999999/sdsf-external-security.html"}


def grid_html(snapshot_only=False):
    head = "".join(f"<th>{n}</th>" for n in ["Z/OS V3R2", "Z/OS V3R1", "z/OS V2R5"])
    body = []
    rows = [r for r in ROWS if (not snapshot_only) or r[2] in SNAPSHOT_CODES]
    for name, page, code, cells in rows:
        tds = [f'<td><a href="{BASE}{page}.HTML"><b>{name}</b></a></td>']
        for (rid, rel), (st, ptf, info) in zip(REL, cells):
            parts = [st]
            if ptf: parts.append(f'<a href="#{rid}_{code}_PTFLIST">PTFs</a>')
            if info: parts.append(f'<a href="#{rid}_{code}_ADDINFO">Additional Information</a>')
            tds.append("<td>" + "<br>".join(parts) + "</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    # sections: PTF lists use <li id> blocks, additional information uses <h4 id> + pre (two layouts)
    ptf_items, info_items = [], []
    for (code, rel), (prod, cat, text, kind) in SECTIONS.items():
        if snapshot_only and (code not in SNAPSHOT_CODES or (code, rel) in SYNTHETIC):
            continue
        rid = dict((r, i) for i, r in REL)[rel]
        ext = EXT_LINKS.get((code, rel))
        link = f'<p>See <a href="{ext}">this article</a>.</p>' if ext else ""
        ptf_row = next(c for n, p, c, cs in ROWS if c == code)
        cell = next(cs for n, p, c, cs in ROWS if c == code)[[r for _, r in REL].index(rel)]
        if cell[1] and not snapshot_only:   # PTFs link exists -> goes to the PTF list
            ptf_items.append(f'<li id="{rid}_{code}_PTFLIST"><h4>{prod}</h4>Fix Category: <code>{cat}</code><pre>{text}</pre>{link}</li>')
        if cell[2] or (snapshot_only and kind == "info"):   # Additional information link exists
            info_items.append(f'<h4 id="{rid}_{code}_ADDINFO">{prod}</h4><p>Fix Category: <code>{cat}</code></p><pre>{text}</pre>{link}')
    return f"""<html><head><title>Broadcom Product Features And Defects Page</title></head><body>
<h1>z/OS Compatibility Matrix</h1>
<table><tr><td>IN PROGRESS</td><td>The validation of the product is in progress.</td></tr><tr><td>YES</td><td>The product has been certified.</td></tr></table>
<table><tr><th>Product/Release</th>{head}</tr>{''.join(body)}</table>
<h2>Required PTF(s)</h2><ul>{''.join(ptf_items)}</ul>
<h2>Additional Information</h2><div>{''.join(info_items)}</div>
</body></html>"""


def product_page(code_prefix, title, vrm_cols, fix_blocks, matrix_rows):
    """Per-product page like AL0.HTML: matrix + Fix Category blocks."""
    cols = "".join(f"<th>{v}</th>" for v in vrm_cols)
    rows = "".join(f"<tr><td>{r}</td>{''.join(c)}</tr>" for r, c in matrix_rows)
    blocks = "".join(f"<p>Fix Category: {cat}</p><pre>{txt}</pre>" for cat, txt in fix_blocks)
    return f"<html><body><h1>{title}</h1><table><tr><th>Compatibility/Release</th>{cols}</tr>{rows}</table>{blocks}<p>This page last updated 22 Nov 2024</p></body></html>"


def pages():
    out = {}
    out["AL0.HTML"] = product_page("AL0", "CA 1", ["12.6","14.0","15.0"], [
        ("CA.TargetSystem-RequiredService.z/OS.V2R5", "RO94642 RO94173"),
        ("CA.TargetSystem-RequiredService.z/OS.V3R1", "RO94173"),
        ("CA.TargetSystem-RequiredService.z/OS.V3R2", "LU18187 LU18196")],
        [("Z/OS V3R2", ["<td>NO</td>", '<td>YES<br><a href="#a">PTFs</a></td>', "<td>YES</td>"])])
    out["ADS.HTML"] = "<html><body><h1>Dispatch</h1><p>Fix Category: CA.TargetSystem-RequiredService.z/OS.V3R2</p><pre>Requires CA Dispatch PTFs LU18024 LU18026 LU18025 LU18027 LU02959 LU02931 LU11099</pre></body></html>"
    out["ACF.HTML"] = "<html><body><h1>ACF2</h1><p>Fix Category: CA.TargetSystem-RequiredService.z/OS.V3R2</p><pre>LU18900 LU18901</pre></body></html>"
    out["ARTICLE"] = "<html><head><title>Enable SDSF external security</title></head><body><p>Apply PTF LU99887 before enabling SDSFExternalSecurity on z/OS 2.5.</p><p>Unrelated text with RO11111.</p></body></html>"
    return out

if __name__ == "__main__":
    import pathlib
    d = pathlib.Path(__file__).parent / "fixtures"
    (d / "grid.html").write_text(grid_html(), encoding="utf-8")
    (d / "grid_snapshot.html").write_text(grid_html(snapshot_only=True), encoding="utf-8")
    for k, v in pages().items():
        (d / f"{k}").write_text(v, encoding="utf-8")
    print("fixtures written:", sorted(p.name for p in d.iterdir()))
