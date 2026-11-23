"""Write and execute notebooks/herosoftware_growth.ipynb (collection -> public data -> simulation -> channels ->
experiments -> traps -> plan). Outputs are kept short (shapes, counts, small tables).

Run:  python src/build_notebook.py
"""
from pathlib import Path

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks" / "herosoftware_growth.ipynb"

CELLS = [
    ("md", "# HeroSoftware: where the next 1,000 merchants come from\n"
           "Independent case study based on public data · not affiliated with or endorsed by HeroSoftware GmbH or Shopify.\n\n"
           "**PUBLIC DATA** = Shopify App Store pages, Eurostat, ECB (observed 2026-11-23). **SIMULATED** = a fictional 4-app "
           "portfolio (APP_A-APP_D); never HeroSoftware's figures."),
    ("code", "import sys, json, subprocess\nfrom pathlib import Path\nimport pandas as pd\nROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()\n"
             "sys.path.insert(0, str(ROOT / 'src'))\npd.set_option('display.width', 160)\n"
             "def run(script):\n    r = subprocess.run([sys.executable, str(ROOT / 'src' / script)], cwd=ROOT, capture_output=True, text=True)\n"
             "    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-500:])\n"
             "def out(name):\n    return pd.read_csv(ROOT / 'data' / 'out' / f'{name}.csv')"),
    ("md", "## 1. Collection (PUBLIC DATA)\nOne polite pass (robots.txt, 1 request / 1.5 s, cached). Without the raw cache, the delivered CSVs in `data/public/` are used."),
    ("code", "run('collect_public.py')\nfor f in sorted((ROOT / 'data' / 'public').glob('*.csv')):\n    print(f.name, pd.read_csv(f).shape)"),
    ("md", "## 2. The real shelf (PUBLIC DATA)"),
    ("code", "run('simulate_growth.py')\nrun('run_sql.py')\nout('reviews_totals').T"),
    ("code", "out('reviews_by_app')[['app', 'reviews', 'share_dach', 'reply_rate', 'last_review', 'reviews_since_2026_03']]"),
    ("code", "out('category_summary')[['herosoftware_app', 'apps_listed', 'hero_position', 'hero_review_rank', 'free_plan_top30', 'free_plan_rest']]"),
    ("code", "out('eurostat')[['geo', 'pct_enterprises_selling_online_b2c']].T"),
    ("md", "## 3. Simulation (SIMULATED)\nSeed 42, 2025-11-01 -> 2026-10-31. Assumptions in `docs/assumptions.md`."),
    ("code", "for f in sorted((ROOT / 'data' / 'sim').glob('*.parquet')):\n    print(f.stem, pd.read_parquet(f).shape)\nout('dq_summary')[['item', 'n']]"),
    ("md", "## 4. Channels (SIMULATED)"),
    ("code", "out('channel_scorecard')[['channel', 'installs', 'uninstall_48h_rate', 'trial_to_paid', 'spend_eur', 'cac_per_paying', 'payback_months']]"),
    ("md", "## 5. Experiments (SIMULATED)"),
    ("code", "ro = out('experiment_readouts')\nprint(ro.decision.value_counts().to_dict())\nro[['exp_id', 'title', 'lift', 'ci_low', 'ci_high', 'rule_call', 'decision']].round(2).head(8)"),
    ("code", "out('exp03_did')"),
    ("code", "out('exp04_quality')"),
    ("md", "## 6. Traps (SIMULATED)"),
    ("code", "display(out('bfcm_did')); display(out('brand_holdout')[['claimed', 'incremental_share', 'incr_ci_low', 'incr_ci_high', 'incremental_conversions']])\n"
             "out('simpson').query(\"level != 'country'\")"),
    ("code", "out('tests')"),
    ("md", "## 7. Deliverables and plan\nExcel tracker (verified by recalculation), dashboard, PDF. The plan is in `docs/90_day_growth_plan.md`."),
    ("code", "for s in ('build_excel.py', 'build_dashboard.py', 'build_pdf.py'):\n    run(s)"),
]


def main():
    nb = nbformat.v4.new_notebook()
    nb.cells = [nbformat.v4.new_markdown_cell(t) if k == "md" else nbformat.v4.new_code_cell(t) for k, t in CELLS]
    nb.metadata = {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}}
    NB.parent.mkdir(exist_ok=True)
    ExecutePreprocessor(timeout=900, kernel_name="python3").preprocess(nb, {"metadata": {"path": str(NB.parent)}})
    nbformat.write(nb, NB)
    print(f"executed {NB.relative_to(ROOT)} ({len(nb.cells)} cells)")


if __name__ == "__main__":
    main()
