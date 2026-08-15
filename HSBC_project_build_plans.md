# Build Plans — Financial Data Engineering Projects
### Supporting the HSBC *Analyst – Data Engineering* (Product Control Analytics) application

> **Read this first.** The three projects on the refactored resume are written as *specs you are about to build*, not as work already done. Before you send the resume, each one needs a real public GitHub repo with working code and a README. Recruiters at HSBC do click GitHub links for analyst-level hires, and a dead link is worse than no link. Each plan below is scoped to roughly **4–7 evenings** of work. If you only have time for one, build **Project 1** — it maps most directly to the JD's core responsibility (standardised data delivery, trade data analysis, SQL automation).
>
> Replace the placeholder `[Repo]` links in the `.tex` file (currently all pointing at your GitHub profile) with the real repo URLs as you create them.

---

## Why these three, specifically

The JD is unusual in that it names its stack and its domain very precisely. These projects were chosen so that between them they cover **every named technical requirement**:

| JD requirement | P1 Pipeline | P2 Valuation | P3 Microservice |
|---|---|---|---|
| Python + OOP principles | ✔ | ✔✔ | ✔ |
| pandas | ✔✔ | ✔ | ✔ |
| SQL (complex, automation, standardisation) | ✔✔ | — | ✔✔ |
| VBA | — | — | ✔✔ |
| Git, Jira, test-driven development | ✔ | ✔ | ✔ |
| Financial data: Trade, Position, PnL | ✔✔ | ✔ | — |
| Valuations / fair value adjustment methodology | — | ✔✔ | — |
| Microservice-driven architecture | — | — | ✔✔ |
| Citizen Developer framework (reusable components) | — | ✔ | ✔✔ |
| Controls, tolerances, audit trail | ✔✔ | ✔ | ✔✔ |

---

# Project 1 — Trade, Position & PnL Attribution Pipeline

**Resume claim it backs:** end-to-end trade/market-data ingestion → EOD positions → daily PnL attribution → T-1 vs T reconciliation with tolerance-based exception reporting, on a standardised data model, test-first with pytest.

**Repo name suggestion:** `trade-pnl-attribution-pipeline`

### Why it matters for this role
This *is* Product Control's daily job in miniature. PC takes trade and market data, revalues positions, explains the day's PnL, and investigates anything that doesn't explain. If you can talk fluently about "unexplained PnL" and "position breaks" in the interview, you will sound like someone who already understands the function — which is exactly what the JD means by *"Previous experience in Valuations or Product Control is not mandatory."* They will hire on aptitude plus evidence of interest, and this repo is the evidence.

### Data
No public trade blotters exist, so **generate synthetic trades** — this is normal and expected, just be explicit about it in the README.

- **Market data:** `yfinance` for equity and FX closes; FRED (`fredapi` or CSV download) for interest-rate curves.
- **Trades:** a `trade_generator.py` that emits a few thousand trades across ~20 instruments over ~60 business days — buys/sells, varying notionals, a handful of intraday amendments and cancellations (you *want* these: amendments are where real breaks come from).
- Deliberately inject defects so your controls have something to catch: one stale price, one duplicated trade ID, one trade booked with a settlement date before trade date, one position that doesn't roll forward.

### Data model (the "standardised data model" claim)
Five tables. Keep it boringly relational — that is the point.

```
dim_instrument   (instrument_id PK, ticker, asset_class, ccy, contract_size)
fct_trade        (trade_id PK, instrument_id FK, trade_date, settle_date,
                  side, quantity, price, ccy, book, trader, amended_from_id)
fct_market_price (instrument_id FK, price_date, close_price, source, PK(instrument_id, price_date))
fct_position     (as_of_date, instrument_id FK, book, quantity, avg_cost,
                  market_price, market_value, PK(as_of_date, instrument_id, book))
fct_pnl          (as_of_date, instrument_id FK, book, total_pnl, price_pnl,
                  fx_pnl, carry_pnl, new_trade_pnl, unexplained_pnl)
```

Then expose **SQL views** on top (`v_position_eod`, `v_pnl_by_book`, `v_exceptions`) so consumers never query base tables. That separation is literally what the JD means by *"support the proper and correct delivery of standardised data to teams across Product Control."* Say that phrase back to them in the interview.

### The PnL attribution logic — get this right, it's the interview question
Daily PnL decomposes so the components sum back to the total:

- **Price PnL** = opening quantity × (today's price − yesterday's price), converted at yesterday's FX rate
- **FX PnL** = opening local-currency market value × (today's FX rate − yesterday's FX rate)
- **Carry PnL** = accrued interest / financing / dividend over the day
- **New-trade PnL** = for trades booked today: quantity × (closing price − execution price)
- **Unexplained** = total PnL − the sum of the above

Two things to be careful about, because interviewers probe both:

1. **Don't double-count.** A trade executed today must be excluded from price PnL (it had no opening position) and captured only in new-trade PnL.
2. **Unexplained should be ~zero.** Non-zero unexplained is the *signal*, not a bug to hide — it means a missing price, a mis-booked trade, or an attribution term you haven't modelled. Your exception report should surface it. Write this in the README; it shows you understand *why* the control exists.

### Reconciliation engine
Config-driven tolerances in `tolerances.yaml`:

```yaml
position_break:      { absolute: 0.0,   description: "quantity must roll: qty_T = qty_T-1 + net_traded_T" }
stale_price:         { max_days: 1,     description: "flag prices unchanged >1 business day" }
unexplained_pnl:     { absolute: 100,   relative: 0.0001, description: "USD or % of market value" }
missing_price:       { absolute: 0.0 }
```

Each check returns a uniform result object — `check_name, as_of_date, instrument_id, book, expected, actual, difference, breached (bool), severity` — written to an `exceptions` table. Uniform shape is what makes the checks composable, and it's the bridge to Project 3.

Output a daily exception report (CSV and a simple HTML summary).

### Repo structure
```
trade-pnl-attribution-pipeline/
├── README.md
├── requirements.txt
├── docker-compose.yml          # postgres for local runs
├── sql/
│   ├── 01_schema.sql
│   ├── 02_views.sql
│   └── 03_indexes.sql
├── src/
│   ├── ingest/     market_data.py, trade_generator.py, loaders.py
│   ├── transform/  positions.py, pnl.py, attribution.py
│   ├── controls/   base.py, position_break.py, stale_price.py, unexplained_pnl.py
│   ├── report/     exception_report.py
│   └── pipeline.py              # orchestrator: python -m src.pipeline --as-of 2026-07-31
├── tests/          test_attribution.py, test_positions.py, test_controls.py, conftest.py
└── data/samples/
```

### Test-driven development — do this genuinely
You claim TDD on the resume, and your git history is the proof. Write the failing test first, commit it, then commit the implementation. A reviewer who scrolls your commits will see `test: expected price pnl for long position` followed by `feat: implement price pnl`. That pattern is worth more than any bullet point.

Cases worth testing: long and short positions; a position closed mid-period; a trade amendment superseding an earlier trade; a day with a missing price; FX PnL on a non-USD instrument; the assertion that components sum to total within a cent.

### Build order
1. Postgres in Docker + schema + a passing "can I connect" test
2. Market-data ingest, then synthetic trade generator
3. Position builder (test-first)
4. PnL attribution (test-first) — the hard part, budget the most time here
5. Controls + tolerance config
6. Exception report + orchestrator CLI
7. README with an architecture diagram and a sample exception report

---

# Project 2 — Derivative Valuation & Fair Value Adjustment Toolkit

**Resume claim it backs:** OOP instrument hierarchy with pluggable pricing engines (Black-Scholes / Monte Carlo / DCF), yield-curve bootstrapping, delta/vega/DV01 sensitivities, and configurable fair-value-adjustment modules regression-tested against benchmarks.

**Repo name suggestion:** `derivative-valuation-fva-toolkit`

### Why it matters for this role
The team you're applying to is *"a centralized specialist quantitative team dedicated to implementation and refinement of fair value adjustment methodologies."* Building a small, honest version of exactly that — with the methodology as a swappable, auditable module rather than hardcoded arithmetic — demonstrates you understood what the team does before you walked in. It also carries your OOP claim: this is where the design patterns live.

### Design — this is the OOP showcase
```python
# Abstract base classes; strategy pattern for pricers
class Instrument(ABC):
    @abstractmethod
    def payoff(self, spot): ...
    @abstractmethod
    def accept(self, pricer): ...        # double dispatch to the right engine

class EuropeanOption(Instrument): ...     # strike, expiry, call/put
class Forward(Instrument): ...
class InterestRateSwap(Instrument): ...   # fixed vs float legs, schedule

class PricingEngine(ABC):
    @abstractmethod
    def price(self, instrument, market): ...

class BlackScholesEngine(PricingEngine): ...
class MonteCarloEngine(PricingEngine): ...    # same instrument, different engine
class DiscountedCashFlowEngine(PricingEngine): ...

class MarketData:                             # curves, vols, spots, as-of date
    def discount_factor(self, date): ...
```

The point to make in interview: **the same instrument can be priced by multiple engines, and the same engine prices multiple instruments.** That decoupling is why Independent Model Review can swap a methodology without touching booking logic — and it's a real answer to "explain OOP principles you've applied," which the JD explicitly asks about.

### Yield-curve bootstrapping
Take deposit, futures and swap-rate quotes; solve for zero rates iteratively so each instrument reprices to par; interpolate log-linearly on discount factors. Expose `curve.discount_factor(date)` and `curve.forward_rate(start, end)`. Use SciPy's `brentq` for the root-finding — don't hand-roll it.

### Fair value adjustments — keep them modular and modest
Implement each as its own class with a documented methodology and its own config. **Label them clearly as illustrative, textbook-level implementations** in both the README and your interview answers. Overclaiming here is the fastest way to get caught out by a quant who does this for a living; saying "this is a simplified bid-offer reserve on a single-factor exposure, here's what a production version would add" is a strong answer.

- **Bid-offer reserve** — cost of unwinding net exposure at market bid-offer spreads
- **Funding adjustment (FVA)** — expected funding cost of uncollateralised exposure over its life
- **Credit reserve (CVA-style)** — expected exposure × default probability × loss given default

Each writes an audit record: inputs, methodology version, parameters, output. Auditability is a control-framework instinct, and it will read as one.

### Sensitivities
Delta and vega by finite difference (and closed-form for Black-Scholes, so you can assert they agree — a genuinely nice test). DV01 by bumping the curve 1bp and repricing.

### Validation — non-negotiable for credibility
Regression-test against published values. Hull's *Options, Futures and Other Derivatives* has worked examples with known answers; `QuantLib-Python` can be a dev-only reference (don't ship it as a runtime dependency, or the project looks like a QuantLib wrapper). Assert put-call parity holds. Assert Monte Carlo converges to Black-Scholes within tolerance as paths increase. That last test is the one that impresses.

### Repo structure
```
derivative-valuation-fva-toolkit/
├── README.md                    # methodology notes + benchmark comparison table
├── src/
│   ├── instruments/   base.py, options.py, forwards.py, swaps.py
│   ├── engines/       base.py, black_scholes.py, monte_carlo.py, dcf.py
│   ├── market/        curve.py, bootstrap.py, vol_surface.py, market_data.py
│   ├── adjustments/   base.py, bid_offer.py, fva.py, cva.py
│   └── risk/          sensitivities.py
├── tests/             test_black_scholes.py, test_parity.py, test_mc_convergence.py,
│                      test_bootstrap.py, test_adjustments.py
└── config/            adjustments.yaml, market_config.yaml
```

### Build order
Black-Scholes + tests → the class hierarchy (refactor BS behind the interface) → curve bootstrapping → DCF/swaps → Monte Carlo + convergence test → sensitivities → adjustment modules → README with a benchmark comparison table.

---

# Project 3 — Reusable Control-Automation Microservice

**Resume claim it backs:** microservice exposing reconciliation/tolerance/data-quality routines as versioned REST endpoints; YAML-configured "citizen developer" model; Excel/VBA client for business users; results and audit trail in SQL.

**Repo name suggestion:** `control-automation-service`

### Why it matters for this role
Two JD lines are almost a spec for this project: *"Participate in development and support of Citizen Developer framework, a coding environment easy to use and re-use components"* and *"Experience in designing microservice-driven system architectures would be an asset."* Add that it's the only one of the three carrying **VBA** — a named requirement most candidates will skip because it feels unglamorous. Banks still run on Excel. Being the candidate who took the VBA line seriously is a real differentiator here.

### The core idea
Project 1's controls are hardcoded in one pipeline. Here you generalise: a control becomes a **registered, versioned, reusable component**, and a *non-developer* composes new controls from a YAML file without writing Python.

```yaml
# controls/eod_position_check.yaml
name: eod_position_break
version: 2
component: reconciliation.two_way_match
description: EOD positions from risk system must match books & records
source:  { type: sql, connection: risk_db,  query_file: queries/risk_positions.sql }
target:  { type: sql, connection: books_db, query_file: queries/books_positions.sql }
keys:    [as_of_date, instrument_id, book]
compare: [quantity, market_value]
tolerance:
  quantity:     { absolute: 0 }
  market_value: { absolute: 50, relative: 0.0001 }
schedule: "0 18 * * 1-5"
owner: product_control_analytics
notify:  { on_breach: [pc-analytics@example.com] }
```

Ship 4–5 reusable components: `reconciliation.two_way_match`, `tolerance.threshold_check`, `quality.completeness`, `quality.referential_integrity`, `quality.staleness`.

### API surface (FastAPI)
```
POST /api/v1/controls                  register a control from YAML
GET  /api/v1/controls                  list registered controls + versions
POST /api/v1/controls/{name}/run       execute (async, returns run_id)
GET  /api/v1/runs/{run_id}             status + summary
GET  /api/v1/runs/{run_id}/exceptions  paginated breaches
GET  /api/v1/components               discoverable component catalogue
GET  /health  /metrics
```

Version endpoints from day one (`/v1/`) and version the controls themselves — when a methodology changes you need to know which version produced last quarter's numbers. That instinct is the whole job.

### Audit trail
Every run persists: run_id, control name + version, config hash, who/what triggered it, start and end time, row counts in and out, breach count, status, and the full result set. If someone asks "why did this control pass in June and fail in July," the config hash answers it. Build a `v_control_run_history` view for that question.

### The Excel/VBA client
A single `.xlsm` with a small ribbon or button panel:

- **Refresh Controls** — `GET /controls`, populate a dropdown
- **Run Control** — `POST /controls/{name}/run`, poll status, write exceptions to a sheet
- **View History** — pull last N runs for the selected control

Use `MSXML2.XMLHTTP` for the HTTP calls and a lightweight JSON parser (VBA-JSON by Tim Hall). Keep the VBA thin — it is a *client*, all logic stays server-side. Say that out loud in the interview: the reason you put logic behind an API instead of in the workbook is that spreadsheet logic can't be version-controlled, tested, or audited. That's the argument for the whole Citizen Developer framework, and it's the answer to "why does this team exist."

### Repo structure
```
control-automation-service/
├── README.md                    # architecture diagram, quickstart, component catalogue
├── docker-compose.yml           # api + postgres + scheduler
├── Dockerfile
├── src/
│   ├── api/         main.py, routes/, schemas.py, dependencies.py
│   ├── components/  base.py, reconciliation.py, tolerance.py, quality.py, registry.py
│   ├── engine/      loader.py, validator.py, executor.py, audit.py
│   ├── db/          models.py, session.py, migrations/
│   └── scheduler/   cron.py
├── excel_client/    ControlRunner.xlsm, modules/*.bas   # export .bas so VBA is diffable in git
├── controls/        *.yaml
└── tests/           test_components.py, test_api.py, test_loader.py, test_audit.py
```

> Export your VBA modules as `.bas` text files alongside the `.xlsm`. Binary workbooks are invisible to git; a reviewer who can't read your VBA has to take your word for it.

### Build order
Component base class + two components (test-first) → config loader with schema validation → executor + audit persistence → FastAPI endpoints → Docker Compose → VBA client → scheduler → README.

---

## Sequencing, if time is short

| Time available | Do this |
|---|---|
| 1 week | Project 1 only. Update the resume to two projects — one real beats three empty. |
| 2–3 weeks | Projects 1 and 3. Strongest JD coverage per hour spent (SQL + microservices + VBA + citizen developer). |
| 4+ weeks | All three. Project 2 is what makes you memorable to the quants on the panel. |

A shared thread worth building deliberately: Project 1's controls become Project 3's components, and Project 2's valuations feed Project 1's positions. If you can draw that on a whiteboard as one coherent platform rather than three unrelated exercises, you'll be describing something very close to what PC Analytics actually operates.

---

## Before you hit send

- [ ] Every `[Repo]` link in `resume_hsbc.tex` points to a real, public, non-empty repo
- [ ] Each README opens with what the project does, why it exists, and how to run it in under 5 minutes
- [ ] Synthetic data is labelled as synthetic; simplified methodologies are labelled as illustrative
- [ ] `pytest` passes from a clean clone (add a GitHub Actions workflow — it's 15 lines and it renders as a green badge)
- [ ] Commit history shows tests landing before implementations
- [ ] You can explain any number on the resume — 40%, 99.9%, 35%, 25% — with the actual measurement behind it
- [ ] Pin down whether you can name the healthcare client, or must say "a large US healthcare payer"
- [ ] LinkedIn title matches the resume exactly (designation + function), not your old project-role title
- [ ] Confirmed "Programmer Analyst" is what Cognizant HR would state on a verification request

## On the job title

Your resume shows **"Data Engineering & Automation — Programmer Analyst"**, which is your actual Cognizant HR designation with a functional descriptor. That's accurate and it survives background verification. Two consequences worth planning for:

- Your **project role** is SDET / test engineering, and that will come up — in a reference call, in a conversation with your Cognizant manager, or if the interviewer asks "what does your day look like?" Don't hide it. "My designation is Programmer Analyst; on my current project I own the data validation and automation layer" is a completely clean answer, and it's true.
- Keep **LinkedIn consistent** with the resume. If LinkedIn says "AI Augmented SDET" and the resume says "Programmer Analyst," a recruiter notices, and it reads as concealment rather than framing. Update LinkedIn to the same designation-plus-function format.

## One thing to prepare for the interview

They will ask why someone from a quality-and-validation engineering background is applying for a data engineering role in Product Control. Don't be defensive about it — the honest answer is strong. You've spent your career so far making sure data is correct: reconciling sources, catching breaks, automating manual checks, building the controls that stop bad numbers reaching people who rely on them. Product Control is the same discipline pointed at trading data instead of healthcare data. The projects are how you closed the domain gap on your own time. Rehearse a 40-second version of that.

## Where the resume is thin, honestly

Three gaps worth knowing before you're asked. **Jira** appears on the resume via your Agile/Scrum work, which is fair, but if you've only ever been a ticket consumer rather than someone who's structured a board or written the acceptance criteria, don't oversell it. **VBA** currently rests entirely on Project 3 — if you don't build that project, take VBA off the skills line rather than risk a screening question you can't answer. And **pandas** appears in your experience section on the strength of dataframe-based reconciliation; make sure you can actually write a `merge` with an indicator column and explain a `groupby().agg()` under pressure, because for this role it will be tested. A recruiter who finds one hollow claim starts doubting the rest of the page.
