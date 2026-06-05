# Image Generation Prompts (for ChatGPT / image models)

Create each image below and save it to the `docs/` folder using the **exact
filename** shown. Every README image reference maps to one of these.

**Global style for ALL images** (append to each prompt if needed):

> Clean, professional, modern flat-design infographic on a **pure white
> background**. Use crisp vector-style icons and the **official brand logos** of
> the named tools (Google Analytics 4, BigQuery, Google Cloud Pub/Sub, dbt,
> Python, SciPy, LangChain, Groq, Google Ads, Meta, Streamlit, Looker Studio,
> Tableau, GitHub) where mentioned. Balanced spacing, thin connector arrows,
> a restrained blue / green / slate palette, legible sans-serif labels, no
> clutter, high resolution, 16:9 unless stated otherwise.

> Note: charts 10–15 are also produced as real PNGs in `outputs/` when you run
> `python main.py run` — you may use those directly instead of generating them.

---

### 1. `docs/project-overview.png` — End-to-end platform architecture
> A horizontal end-to-end architecture diagram of a multi-touch marketing
> attribution platform, left to right in four stages: (1) "Journey Tracking" —
> Google Analytics 4 + tag manager + ad pixels icons; (2) "Warehouse + Transform"
> — Pub/Sub streaming into BigQuery, then dbt doing session stitching and path
> construction; (3) "Attribution Engines" — a Shapley-value game-theory block and
> a Markov-chain block feeding a composite score; (4) "Optimization & Activation"
> — a SciPy budget optimizer and an AI advisor agent pushing bid changes to
> Google Ads and Meta. Thin arrows connect the stages. White background, clean
> logos, professional infographic.

### 2. `docs/setup-env-overview.png` — Local environment setup
> A clean diagram showing local project setup on a developer machine: a Python
> virtual environment (venv) box containing the project modules (ingestion,
> attribution, optimization, agent), with a config.yaml file and a .env secrets
> file feeding into it, and a terminal icon running the pipeline. Show pip
> installing requirements. White background, flat icons, Python logo,
> professional.

### 3. `docs/terminal-pipeline-run.png` — Terminal screenshot of a pipeline run
> A realistic screenshot of a developer terminal on a white/light theme showing
> the output of running a marketing-attribution pipeline command. Include neat
> ASCII tables titled "ATTRIBUTION MODEL COMPARISON", "BUDGET OPTIMISATION", and
> "ATTRIBUTION ADVISOR AGENT", with channel names (Paid Search, Organic Search,
> Email, Display) and percentage / dollar values, and a final line
> "Pipeline complete." Monospaced font, clean, professional, white background.

### 4. `docs/cloud-auth-overview.png` — Cloud authentication overview
> A diagram explaining optional cloud authentication for a data platform: a
> developer using gcloud Application Default Credentials (ADC) to authenticate to
> Google Cloud (BigQuery), plus API-key boxes for Groq, Google Ads and Meta, each
> with a small "optional / falls back to local mock" tag. Emphasise that missing
> credentials safely fall back to local mode. White background, brand logos,
> clean flat design.

### 5. `docs/data-flow.png` — GA4 → BigQuery real-time data flow
> A left-to-right real-time data-flow diagram: Google Analytics 4 events →
> Google Cloud Pub/Sub (stream) → Dataflow → BigQuery warehouse → dbt transform →
> a "customer journeys" table. Label the stream "intraday / real-time". White
> background, official logos, thin arrows, professional infographic.

### 6. `docs/dbt-lineage.png` — dbt model lineage
> A dbt model lineage graph (DAG) with three connected nodes left to right:
> "stg_ga4_events (staging: clean & dedupe)" → "int_session_stitched (apply
> 30-day attribution window)" → "customer_journeys (ordered channel path)".
> Include the dbt logo and small data-quality test check-marks on nodes. White
> background, clean, professional.

### 7. `docs/attribution-methodology.png` — Attribution methodology
> An infographic explaining a composite attribution score: two input methods on
> the left — "Shapley Values (cooperative game theory, fair marginal credit)" and
> "Markov Chain (removal effect, path necessity)" — combining with weights
> "70% + 30%" into a single "Composite Attribution Score" on the right, which
> then feeds budget optimization. White background, icons, clean flat design.

### 8. `docs/shapley-game-theory.png` — Shapley value concept
> A clean conceptual illustration of Shapley value attribution: marketing
> channels (Paid Search, Email, Display, Social) shown as players in a
> cooperative game, with small diagrams of channel coalitions and a formula
> caption "average marginal contribution across all orderings". Emphasise
> "fair credit distribution" and "exact, up to 8 channels". White background,
> minimal, professional, blue/slate palette.

### 9. `docs/markov-chain.png` — Markov chain path model
> A directed-graph diagram of an absorbing Markov chain for customer journeys:
> a START node, several channel nodes (Paid Search, Email, Display, Social) with
> transition-probability arrows between them, leading to two absorbing nodes
> "CONVERSION" and "NULL". Add a callout explaining "removal effect = drop in
> conversion probability when a channel is removed". White background, clean,
> professional.

### 10. `docs/markov-transition-heatmap.png` — Transition matrix heat-map
> A clean heat-map (matrix) screenshot titled "Markov Chain Channel Transition
> Matrix", rows and columns labelled with channel names plus start/conversion/
> null states, cells shaded in a blue gradient from 0 to 1 with a colour-bar
> legend "P(next state)". White background, data-visualization style.

### 11. `docs/model-comparison.png` — Attribution model comparison chart
> A grouped bar chart titled "Attribution Model Comparison by Channel", x-axis of
> channels (Paid Search, Organic Search, Display, Paid Social, Email, Video,
> Referral, Direct), grouped bars for models: Shapley, Markov, Composite,
> Last-click, First-click, Linear; y-axis "Conversion credit (%)". Clean legend,
> white background, professional data viz.

### 12. `docs/shapley-vs-lastclick.png` — Shapley vs last-click chart
> A grouped bar chart titled "Shapley vs Last-Click Attribution by Channel". Two
> bars per channel: blue "Shapley" and grey "Last-click". Show Shapley higher for
> upper-funnel channels (Paid Search, Organic Search, Email) and last-click
> higher for Direct/Display/Video. Y-axis "Conversion credit (%)". White
> background, clean, professional.

### 13. `docs/optimization-loop.png` — Budget optimisation & agent loop
> A circular closed-loop diagram: "Composite Attribution" → "SciPy Budget
> Optimizer (maximise revenue under budget constraints)" → "LangChain Attribution
> Advisor Agent" → "Bid changes to Google Ads + Meta" → back to "GA4 events /
> attribution". Emphasise "autonomous, closes the loop without human
> intervention". White background, brand logos, clean flat design.

### 14. `docs/budget-reallocation.png` — Current vs optimised spend chart
> A grouped bar chart titled "Budget Reallocation: Current vs Shapley-Optimised",
> channels on the x-axis, two bars each (grey "Current", green "Optimised"),
> y-axis "Monthly spend ($K)". Show budget shifting toward Paid Search, Organic
> Search and Email. White background, professional data viz.

### 15. `docs/roas-uplift.png` — ROAS uplift chart
> A simple two-bar chart titled "Predicted Blended ROAS Improvement", bars
> "Current mix" (grey, ~2.8x) and "Optimised mix" (green, ~3.2x) with value
> labels on top and a "+15%" uplift callout. Y-axis "Blended ROAS". White
> background, clean, professional. Portrait or square is fine.

### 16. `docs/streamlit-simulator.png` — Streamlit budget simulator screenshot
> A screenshot of a Streamlit web dashboard titled "Budget Reallocation
> Simulator" on a white theme: a left sidebar with channel-mix percentage
> sliders and a total-budget input; the main area showing a "Composite
> attribution" bar chart, a "Predicted ROAS by scenario" bar chart, and a
> scenario-comparison data table. Clean, modern, professional web UI.

### 17. `docs/agent-audit-log.png` — Agent audit log
> A clean screenshot showing an AI agent's bid-change audit log: a small terminal
> table listing channels (Paid Search, Email, Paid Social, Display), platform
> (google_ads / meta_marketing), change_pct (+25% / −25%), and mode (dry_run),
> next to a snippet of a JSON-lines audit file. White/light background,
> monospaced, professional.

### 18. `docs/cicd-workflow.png` — CI/CD workflow
> A horizontal CI/CD pipeline diagram with the GitHub logo: "Push / Pull Request"
> → "GitHub Actions" → steps "Install deps → Run pytest → Smoke-run pipeline" →
> green "Passing" check. White background, clean flat icons, professional.

### 19. `docs/monitoring-architecture.png` — Monitoring & audit architecture
> An infographic of monitoring components for an attribution platform laid out as
> cards: "Attribution Validation (holdout A/B)", "Model Refresh (weekly dbt)",
> "Data Quality (dbt tests)", "Drift Detection (channel distribution)", "Agent
> Audit (all bid changes logged)". White background, clean icons, professional.

### 20. `docs/journey-sankey.png` — Customer journey Sankey diagram
> A Sankey flow diagram titled "Customer Journey Flow (converting paths)" showing
> flows between marketing channels (Paid Search, Organic Search, Email, Display,
> Paid Social, Direct) with proportional ribbon widths, ending in a "Conversion"
> node. Soft multi-colour ribbons, white background, clean data-visualization
> style.

### 21. `docs/looker-studio-dashboard.png` — Looker Studio dashboard screenshot
> A screenshot of a Looker Studio marketing dashboard on a white theme titled
> "Channel ROAS & Journey", with KPI scorecards (Blended ROAS, Total Attributed
> Revenue), a bar chart of attribution credit by channel, and a small journey
> Sankey panel. Clean, modern BI dashboard, professional.
