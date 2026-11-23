"""Build excel/growth_experiment_tracker.xlsx (SIMULATED data, live formulas) and verify it.

Sheets: Backlog (ICE = AVERAGE, sorted), Sample_Size (two proportions, NORM.S.INV), Readouts (lift, CI, p, decision by
formula), Channel_Scorecard (CAC, payback), Checks (control sums vs SQL outputs, OK / MISMATCH).
Input cells are blue. File metadata is emptied.

Run:  python src/build_excel.py            (build + verify with LibreOffice headless if installed)
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ab_stats import prop_test, sample_size_prop  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT, XL = ROOT / "data" / "out", ROOT / "excel" / "growth_experiment_tracker.xlsx"
INK, MUTED, BLUE_IN, BAND = "0B0B0B", "6B6A65", "1F4E9A", "F0EFEC"
H = Font(name="Segoe UI", bold=True, color=INK, size=10)
TITLE = Font(name="Segoe UI", bold=True, color=INK, size=14)
NOTE = Font(name="Segoe UI", italic=True, color=MUTED, size=9)
BODY = Font(name="Segoe UI", color=INK, size=10)
INPUT_FONT = Font(name="Segoe UI", color=BLUE_IN, size=10, bold=True)
INPUT_FILL = PatternFill("solid", fgColor="E3EEFB")
HEAD = PatternFill("solid", fgColor=BAND)
THIN = Border(bottom=Side(style="thin", color="D9D6CF"))
PCT, PCT1, EUR, INT = "0%", "0.0%", '"EUR "#,##0', "#,##0"
TAG = "SIMULATED data for a fictional 4-app portfolio (APP_A-APP_D) - not HeroSoftware's figures."

NEW_IDEAS = [  # backlog ideas not tested yet (from docs/90_day_growth_plan.md)
    ("NEW01", "Spanish listing for APP_B (after FR/IT)", "App Store", "APP_B", 8, 7, 7),
    ("NEW02", "Reply policy: every review answered within 48 h", "App Store", "APP_B", 5, 6, 9),
    ("NEW03", "Free plan for APP_A in the Shipping shelf", "Pricing", "APP_A", 7, 5, 5),
    ("NEW04", "Comparison page per app (SEO)", "SEO", "All", 7, 6, 6),
    ("NEW05", "Agency partner kit (2 new agencies per month)", "Partners", "All", 6, 6, 6),
    ("NEW06", "Onboarding e-mail v2 for APP_D", "Email", "APP_D", 6, 7, 8),
]


def hdr(ws, row, cols):
    for c, v in enumerate(cols, 1):
        cell = ws.cell(row, c, v)
        cell.font, cell.fill, cell.border = H, HEAD, THIN
        cell.alignment = Alignment(wrap_text=True, vertical="center")


def put(ws, ref, v, fmt=None, inp=False, font=None):
    c = ws[ref]
    c.value = v
    c.font = font or (INPUT_FONT if inp else BODY)
    if inp:
        c.fill = INPUT_FILL
    if fmt:
        c.number_format = fmt
    return c


def widths(ws, w):
    for k, v in w.items():
        ws.column_dimensions[k].width = v


def title(ws, t, sub):
    put(ws, "A1", t, font=TITLE)
    put(ws, "A2", sub, font=NOTE)
    put(ws, "A3", TAG + " Blue cells are inputs.", font=NOTE)


def sheet_backlog(wb, exps):
    ws = wb.create_sheet("Backlog")
    title(ws, "Growth backlog - ICE score", "ICE = AVERAGE(Impact, Confidence, Ease), each 1-10. Rows sorted by ICE when built; Rank is a live formula.")
    hdr(ws, 5, ["ID", "Idea", "Channel", "App", "Impact", "Confidence", "Ease", "ICE", "Rank", "Status / decision"])
    rows = [(r.exp_id, r.title, r.channel, r.app, r.ice_impact, r.ice_confidence, r.ice_ease, r.decision) for r in exps.itertuples()]
    rows += [(i, t, c, a, im, co, ea, "Not tested yet") for i, t, c, a, im, co, ea in NEW_IDEAS]
    rows.sort(key=lambda r: -(r[4] + r[5] + r[6]) / 3)
    n = len(rows)
    for k, r in enumerate(rows):
        i = 6 + k
        for col, v in zip("ABCD", r[:4]):
            put(ws, f"{col}{i}", v)
        for col, v in zip("EFG", r[4:7]):
            put(ws, f"{col}{i}", int(v), inp=True)
        put(ws, f"H{i}", f"=ROUND(AVERAGE(E{i}:G{i}),2)", "0.00")
        put(ws, f"I{i}", f"=RANK(H{i},$H$6:$H${5 + n})")
        put(ws, f"J{i}", r[7])
    dv = DataValidation(type="whole", operator="between", formula1="1", formula2="10", showErrorMessage=True)
    ws.add_data_validation(dv)
    dv.add(f"E6:G{5 + n}")
    widths(ws, {"A": 8, "B": 52, "C": 11, "D": 13, "E": 9, "F": 11, "G": 8, "H": 8, "I": 7, "J": 16})
    ws.freeze_panes = "C6"
    return n


def sheet_sample(wb):
    ws = wb.create_sheet("Sample_Size")
    title(ws, "Sample size and test duration - two proportions", "Two-sided z-test (NORM.S.INV), 80% power by default: n = (z_a/2 + z_b)^2 (p1 q1 + p2 q2) / (p2 - p1)^2 per arm.")
    labels = [("Baseline conversion rate (control)", 0.0037, "0.00%"), ("Relative MDE (smallest lift worth detecting)", 0.25, PCT),
              ("Alpha (two-sided)", 0.05, "0.00"), ("Power", 0.80, PCT), ("Units per arm per week", 24000, INT)]
    for k, (lab, v, f) in enumerate(labels):
        put(ws, f"A{5 + k}", lab)
        put(ws, f"B{5 + k}", v, f, inp=True)
    calc = [("Treated rate p2 = p1 x (1 + MDE)", "=B5*(1+B6)", "0.000%"), ("z alpha/2", "=_xlfn.NORM.S.INV(1-B7/2)", "0.000"),
            ("z power", "=_xlfn.NORM.S.INV(B8)", "0.000"),
            ("Units needed per arm", "=ROUNDUP((B12+B13)^2*(B5*(1-B5)+B11*(1-B11))/(B11-B5)^2,0)", INT),
            ("Weeks needed (minimum 2 full weekly cycles)", "=MAX(2,ROUNDUP(B14/B9,0))", "0"),
            ("Units needed, both arms", "=2*B14", INT)]
    for k, (lab, fml, f) in enumerate(calc):
        put(ws, f"A{11 + k}", lab, font=H)
        put(ws, f"B{11 + k}", fml, f)
    put(ws, "A18", "Example: the Meta test (EXP06) ran 3 weeks with 72,000 reached stores per arm and a base trial rate of ~0.37%. "
                   "Change B6 from 25% to 8% to see why it was inconclusive.", font=NOTE)
    hdr(ws, 20, ["Relative MDE", "Units per arm", "Weeks"])
    for k, m in enumerate([0.05, 0.08, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]):
        i = 21 + k
        put(ws, f"A{i}", m, PCT, inp=True)
        put(ws, f"B{i}", f"=ROUNDUP(($B$12+$B$13)^2*($B$5*(1-$B$5)+$B$5*(1+A{i})*(1-$B$5*(1+A{i})))/($B$5*A{i})^2,0)", INT)
        put(ws, f"C{i}", f"=MAX(2,ROUNDUP(B{i}/$B$9,0))", "0")
    widths(ws, {"A": 48, "B": 16, "C": 10})


def sheet_readouts(wb, ro):
    ws = wb.create_sheet("Readouts")
    title(ws, "Experiment read-outs - lift, 95% CI, p-value and decision by formula",
          "Relative CI by the delta method. Rule: CI low > 0 -> Scale; CI high < 0 -> Kill; CI high < minimum worthwhile lift -> Kill; else Inconclusive.")
    put(ws, "A4", "Minimum worthwhile lift", font=H)
    put(ws, "C4", 0.10, PCT, inp=True)
    cols = ["Exp", "Title", "Unit", "n control", "conv. control", "n treatment", "conv. treatment", "Rate C", "Rate T",
            "Lift", "SE lift", "CI low", "CI high", "z", "p-value", "Decision (formula)", "Decision (log)", "Same?"]
    hdr(ws, 6, cols)
    arms = pd.read_parquet(ROOT / "data" / "sim" / "experiment_arms.parquet")
    q = pd.read_csv(OUT / "exp04_quality.csv").set_index("cohort")
    rv = pd.read_csv(OUT / "exp01_reviews.csv").set_index("arm")
    src = {e: (g[g.arm == "control"].iloc[0], g[g.arm == "treatment"].iloc[0]) for e, g in arms.groupby("exp_id")}
    data = {"EXP01": ("new installs prompted", rv.loc["day_2", "prompted"], rv.loc["day_2", "reviews"], rv.loc["value_moment", "prompted"], rv.loc["value_moment", "reviews"]),
            "EXP04": ("installs (paying per install)", q.loc["Organic + other", "installs"], q.loc["Organic + other", "paying"], q.loc["App Store ads", "installs"], q.loc["App Store ads", "paying"])}
    for e, (c, t) in src.items():
        data[e] = (c.unit, c.units, c.conversions, t.units, t.conversions)
    rows = ro[ro.exp_id.isin(data)].sort_values("exp_id")
    for k, r in enumerate(rows.itertuples()):
        i = 7 + k
        unit, nc, xc, nt, xt = data[r.exp_id]
        put(ws, f"A{i}", r.exp_id)
        put(ws, f"B{i}", r.title)
        put(ws, f"C{i}", unit)
        for col, v in zip("DEFG", (nc, xc, nt, xt)):
            put(ws, f"{col}{i}", int(v), INT, inp=True)
        put(ws, f"H{i}", f"=E{i}/D{i}", "0.00%")
        put(ws, f"I{i}", f"=G{i}/F{i}", "0.00%")
        put(ws, f"J{i}", f"=I{i}/H{i}-1", PCT1)
        put(ws, f"K{i}", f"=SQRT((I{i}*(1-I{i})/F{i})/H{i}^2+I{i}^2*(H{i}*(1-H{i})/D{i})/H{i}^4)", PCT1)
        put(ws, f"L{i}", f"=J{i}-_xlfn.NORM.S.INV(0.975)*K{i}", PCT1)
        put(ws, f"M{i}", f"=J{i}+_xlfn.NORM.S.INV(0.975)*K{i}", PCT1)
        put(ws, f"N{i}", f"=(I{i}-H{i})/SQRT(((E{i}+G{i})/(D{i}+F{i}))*(1-(E{i}+G{i})/(D{i}+F{i}))*(1/D{i}+1/F{i}))", "0.00")
        put(ws, f"O{i}", f"=2*(1-_xlfn.NORM.S.DIST(ABS(N{i}),TRUE))", "0.000")
        put(ws, f"P{i}", f'=IF(L{i}>0,"Scale",IF(M{i}<0,"Kill",IF(M{i}<$C$4,"Kill","Inconclusive")))')
        put(ws, f"Q{i}", r.decision)
        put(ws, f"R{i}", f'=IF(P{i}=Q{i},"yes","no - see log")')
    last = 6 + len(rows)
    put(ws, f"A{last + 2}", "EXP02 and EXP03 are difference-in-differences on installs (sql/05, sql/07): read in data/out, not a two-proportion test. "
                            "'no - see log' = business decision differs from the statistical call (reason in docs/experiment_log.md).", font=NOTE)
    widths(ws, {"A": 7, "B": 40, "C": 24, "D": 10, "E": 10, "F": 10, "G": 10, "H": 8, "I": 8, "J": 8, "K": 8, "L": 8, "M": 8,
                "N": 7, "O": 8, "P": 14, "Q": 13, "R": 13})
    ws.freeze_panes = "C7"
    return rows, data, last


def sheet_scorecard(wb, sc):
    ws = wb.create_sheet("Channel_Scorecard")
    title(ws, "Channel scorecard - CAC and payback", "CAC = spend / paying merchants; payback (months) = CAC / MRR per paying merchant at day 60. Cohort Nov 2025-Aug 2026.")
    hdr(ws, 5, ["Channel", "Spend (EUR)", "Installs", "Paying", "MRR / paying (EUR)", "Cost per install", "CAC", "Payback (months)", "Verdict"])
    p = sc[sc.spend_eur > 0].reset_index(drop=True)
    for k, r in enumerate(p.itertuples()):
        i = 6 + k
        put(ws, f"A{i}", r.channel)
        put(ws, f"B{i}", float(r.spend_eur), EUR, inp=True)
        put(ws, f"C{i}", int(r.installs), INT, inp=True)
        put(ws, f"D{i}", int(r.paying), INT, inp=True)
        put(ws, f"E{i}", float(r.mrr_per_paying_d60), "0.0", inp=True)
        put(ws, f"F{i}", f"=B{i}/C{i}", '"EUR "#,##0.0')
        put(ws, f"G{i}", f"=B{i}/D{i}", EUR)
        put(ws, f"H{i}", f"=G{i}/E{i}", "0.0")
        put(ws, f"I{i}", f'=IF(H{i}<=6,"Scale",IF(H{i}<=12,"Watch","Cut"))')
    last = 5 + len(p)
    put(ws, f"A{last + 1}", "Total paid", font=H)
    for col in "BCD":
        put(ws, f"{col}{last + 1}", f"=SUM({col}6:{col}{last})", EUR if col == "B" else INT)
    put(ws, f"G{last + 1}", f"=B{last + 1}/D{last + 1}", EUR)
    put(ws, f"A{last + 3}", "Verdict thresholds (payback): <= 6 months Scale, <= 12 Watch, > 12 Cut. Organic channels (no spend) are in data/out/channel_scorecard.csv.", font=NOTE)
    widths(ws, {"A": 22, "B": 13, "C": 10, "D": 9, "E": 16, "F": 14, "G": 11, "H": 15, "I": 10})
    return p, last


def sheet_checks(wb, n_backlog, ro_rows, ro_last, sc, sc_last):
    ws = wb.create_sheet("Checks")
    title(ws, "Checks - workbook vs SQL outputs", "Each row compares a sum computed in this workbook with the value exported by run_sql.py.")
    hdr(ws, 5, ["Check", "Workbook", "SQL output", "Status"])
    paid = sc
    checks = [
        ("Total paid spend (Channel_Scorecard)", f"=Channel_Scorecard!B{sc_last + 1}", round(float(paid.spend_eur.sum()), 2)),
        ("Total paid installs", f"=Channel_Scorecard!C{sc_last + 1}", int(paid.installs.sum())),
        ("Total paying merchants from paid channels", f"=Channel_Scorecard!D{sc_last + 1}", int(paid.paying.sum())),
        ("CAC App Store ads", "=INDEX(Channel_Scorecard!G:G,MATCH(\"app_store_ads\",Channel_Scorecard!A:A,0))",
         float(paid.set_index("channel").loc["app_store_ads", "cac_per_paying"])),
        ("Experiments in the backlog (tested)", f'=COUNTIF(Backlog!A6:A{5 + n_backlog},"EXP*")', 24),
        ("Read-outs with a two-proportion test", f"=COUNTA(Readouts!A7:A{ro_last})", len(ro_rows)),
        ("Lift EXP06 (Meta)", "=INDEX(Readouts!J:J,MATCH(\"EXP06\",Readouts!A:A,0))", float(ro_rows.set_index("exp_id").loc["EXP06", "lift"])),
        ("Units per arm for the default MDE (Sample_Size)", "=Sample_Size!B14", int(sample_size_prop(0.0037, 0.25))),
    ]
    for k, (lab, fml, want) in enumerate(checks):
        i = 6 + k
        put(ws, f"A{i}", lab)
        put(ws, f"B{i}", fml, "#,##0.00")
        put(ws, f"C{i}", want, "#,##0.00", inp=True)
        put(ws, f"D{i}", f'=IF(ABS(B{i}-C{i})<=0.005*MAX(1,ABS(C{i})),"OK","MISMATCH")')
    put(ws, f"A{7 + len(checks)}", "All checks", font=H)
    put(ws, f"D{7 + len(checks)}", f'=IF(COUNTIF(D6:D{5 + len(checks)},"OK")={len(checks)},"OK","MISMATCH")', font=H)
    widths(ws, {"A": 46, "B": 14, "C": 14, "D": 12})
    return checks


def build():
    XL.parent.mkdir(parents=True, exist_ok=True)
    ro = pd.read_csv(OUT / "experiment_readouts.csv")
    sc = pd.read_csv(OUT / "channel_scorecard.csv")
    exps = ro[["exp_id", "title", "channel", "app", "ice_impact", "ice_confidence", "ice_ease", "decision"]]
    wb = Workbook()
    wb.remove(wb.active)
    n_backlog = sheet_backlog(wb, exps)
    sheet_sample(wb)
    ro_rows, data, ro_last = sheet_readouts(wb, ro)
    p, sc_last = sheet_scorecard(wb, sc)
    checks = sheet_checks(wb, n_backlog, ro_rows, ro_last, p, sc_last)
    for ws in wb.worksheets:
        ws.sheet_view.showGridLines = False
    wb.properties.creator = ""
    wb.properties.lastModifiedBy = ""
    wb.properties.title = "Growth experiment tracker (simulated data)"
    wb.save(XL)
    print(f"written {XL.relative_to(ROOT)}")
    return ro_rows, data, checks


def verify(ro_rows, data) -> bool:
    soffice = shutil.which("soffice") or r"C:\Program Files\LibreOffice\program\soffice.exe"
    if not Path(soffice).exists():
        print("LibreOffice not found: formulas will compute when the file is opened in Excel (not verified here).")
        return True
    tmp = Path(tempfile.mkdtemp())
    profile = Path(tempfile.mkdtemp())
    subprocess.run([soffice, f"-env:UserInstallation={profile.as_uri()}", "--headless", "--calc", "--convert-to", "xlsx",
                    "--outdir", str(tmp), str(XL)], check=True, capture_output=True, timeout=240)
    wb = load_workbook(tmp / XL.name, data_only=True)
    rd, ss, ck = wb["Readouts"], wb["Sample_Size"], wb["Checks"]
    ok = True
    for k, e in enumerate(ro_rows.exp_id):
        i = 7 + k
        _, nc, xc, nt, xt = data[e]
        r = prop_test(xt, nt, xc, nc)
        for col, want in (("J", r["rel"]), ("L", r["rel_low"]), ("O", r["p"])):
            got = rd[f"{col}{i}"].value
            good = got is not None and abs(got - want) < 1e-6
            ok &= good
            if not good:
                print(f"  BAD {e} {col}: excel={got} python={want}")
    good = ss["B14"].value == sample_size_prop(0.0037, 0.25)
    ok &= good
    print(f"  {'OK ' if good else 'BAD'} sample size: excel={ss['B14'].value} python={sample_size_prop(0.0037, 0.25)} weeks={ss['B15'].value}")
    statuses = [ck[f"D{6 + k}"].value for k in range(8)]
    print("  checks sheet:", statuses, "| all:", ck["D15"].value)
    ok &= all(s == "OK" for s in statuses)
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(profile, ignore_errors=True)
    return ok


if __name__ == "__main__":
    rows, d, _ = build()
    good = verify(rows, d)
    print("verification:", "PASS" if good else "FAIL")
    sys.exit(0 if good else 1)
