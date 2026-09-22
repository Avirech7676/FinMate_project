# FinMate 2.0 — Financial Health Scoring Methodology

## 1. Overview & Purpose
The FinMate 2.0 Financial Health Score is an explainable, deterministic composite metric (ranging from 0 to 100) designed to provide users with transparent insight into their financial stability and discipline. 

> **LEGAL & REGULATORY DISCLAIMER**:
> This financial health score is an algorithmic educational assessment based on tracked transactions, budgets, and goals. It does not constitute professional financial, legal, or tax advice, nor is it a credit score, solvency guarantee, or formal certification.

---

## 2. Pillar Architecture & Weights

The overall score is computed as a weighted linear combination of five distinct behavioral pillars:

| Pillar | Weight | Focus Area | Underlying Data Sources |
| :--- | :--- | :--- | :--- |
| **1. Savings & Surplus** | **25%** ($w_1 = 0.25$) | Net savings rate and monthly surplus ratio | Monthly income vs total monthly spending |
| **2. Budget Adherence** | **25%** ($w_2 = 0.25$) | Budget limit discipline and ceiling utilization | Categorical and total budget ceilings vs actual spend |
| **3. Cash Flow Health** | **20%** ($w_3 = 0.20$) | Liquidity buffer and net cashflow margin | Net monthly cashflow relative to total inflows |
| **4. Goal Progress & Pacing** | **15%** ($w_4 = 0.15$) | Target achievement velocity and pacing | Active goals, completion percentage, pacing status |
| **5. Spending Consistency** | **15%** ($w_5 = 0.15$) | Volatility of daily outlays & anomaly avoidance | Daily expense coefficient of variation ($CV$), anomaly count |

$$\text{Overall Score} = \text{round}\left( \sum_{i=1}^{5} w_i \times S_i \right)$$

Where each component score $S_i \in [0, 100]$.

---

## 3. Pillar Formulations & Normalization

### Pillar 1: Savings & Surplus (25%)
- When monthly income ($I > 0$) is recorded:
  $$\text{Savings Rate } (SR) = \frac{I - E}{I}$$
  - $SR \ge 30\%$: **100 pts** (Strong savings)
  - $20\% \le SR < 30\%$: **85 pts** (Healthy savings)
  - $10\% \le SR < 20\%$: **70 pts** (Moderate savings)
  - $0\% \le SR < 10\%$: **50 pts** (Thin surplus)
  - $SR < 0\%$: $\max(10.0, 50.0 - |SR| \times 80.0)$ (Deficit penalty)
- Edge Case (No income configured): Baseline is estimated from absolute spending volume ($E < \$1,500 \implies 75$, $E < \$3,500 \implies 60$, else $40$).

### Pillar 2: Budget Adherence (25%)
- When an active monthly budget ceiling ($B > 0$) is configured:
  $$\text{Utilization } (U) = \frac{E}{B}$$
  - $U \le 80\%$: **100 pts**
  - $80\% < U \le 100\%$: **85 pts**
  - $100\% < U \le 115\%$: **55 pts** (Mild overrun)
  - $U > 115\%$: $\max(15.0, 100.0 - U \times 60.0)$ (Severe overrun)
- Edge Case (No budget configured): Defaults to neutral baseline **65 pts** with recommendation to configure a budget.

### Pillar 3: Cash Flow Health (20%)
- Compares net cash flow $NCF = I - E$ to total income $I$:
  - If $NCF > 0$: $S_3 = \min(100.0, 60.0 + \frac{NCF}{I} \times 100.0)$
  - If $NCF \le 0$: $S_3 = \max(15.0, 50.0 - \frac{|NCF|}{I} \times 80.0)$
- When $I = 0$: Defaults to 60 if $E < \$2,000$ else 40.

### Pillar 4: Goal Progress & Pacing (15%)
- Evaluates active financial goals:
  $$S_4 = \frac{N_{\text{on\_track}} \times 100 + N_{\text{at\_risk}} \times 50}{N_{\text{total\_goals}}}$$
- Edge Case (No goals configured): Defaults to neutral baseline **60 pts**.

### Pillar 5: Spending Consistency (15%)
- Evaluates volatility across daily spending history (minimum 5 days):
  $$CV = \frac{\sigma_{\text{daily}}}{\mu_{\text{daily}}}$$
  - $CV < 0.6$: **95 pts** (Very stable)
  - $0.6 \le CV < 1.0$: **80 pts** (Stable)
  - $1.0 \le CV < 1.5$: **65 pts** (Moderate fluctuations)
  - $CV \ge 1.5$: **45 pts** (High volatility)
- **Anomaly Penalty**: Recent detected anomalies reduce consistency by 10 points per anomaly:
  $$S_5 = \max(10.0, S_5 - \min(30.0, N_{\text{anomalies}} \times 10.0))$$

---

## 4. Score Interpretation & Bands

| Score Range | Tier Label | Color Code | Interpretation |
| :--- | :--- | :--- | :--- |
| **80 – 100** | **Excellent** | `#10b981` (Green) | High savings rate, disciplined budget adherence, zero critical anomalies. |
| **65 – 79** | **Good** | `#3b82f6` (Blue) | Positive cash flow, manageable spending variation, goals mostly on track. |
| **50 – 64** | **Fair** | `#f59e0b` (Amber) | Spending near income limits, mild budget overruns, or missing targets. |
| **35 – 49** | **Needs Work**| `#f97316` (Orange)| Net negative cashflow, consistent budget overruns, multiple spending spikes. |
| **0 – 34** | **Critical** | `#ef4444` (Red) | Severe deficit, extreme volatility, depleted surplus margin. |

---

## 5. Sensitivity Analysis

To quantify how changes in individual components affect the overall score, a partial derivative sensitivity analysis was performed:

| Pillar | Partial Derivative $\frac{\partial S}{\partial S_i}$ | Impact of $\pm 10$ Pt Pillar Change | Max Swing on Overall Score |
| :--- | :--- | :--- | :--- |
| Savings & Surplus | $0.25$ | $\pm 2.50$ points | $25.0$ points ($0 \to 100$) |
| Budget Adherence | $0.25$ | $\pm 2.50$ points | $25.0$ points ($0 \to 100$) |
| Cash Flow Health | $0.20$ | $\pm 2.00$ points | $20.0$ points ($0 \to 100$) |
| Goal Progress | $0.15$ | $\pm 1.50$ points | $15.0$ points ($0 \to 100$) |
| Spending Consistency | $0.15$ | $\pm 1.50$ points | $15.0$ points ($0 \to 100$) |

### Key Sensitivity Takeaways:
1. **Core Financial Health (Savings + Budget)** controls **50%** of the composite score. Users who balance spending and stay within budget can easily maintain a "Good" rating even if they haven't set up explicit goals.
2. **Resilience to Single Anomaly**: A single detected spending anomaly incurs a 10-point penalty on Pillar 5 ($10 \times 0.15 = -1.5$ points overall), preventing a single irregular transaction from drastically altering the user's tier.
3. **Severe Deficit Dampening**: Net negative spending penalizes both Savings (25%) and Cash Flow (20%), delivering an appropriate $-4.5$ point drop per $10\%$ deficit expansion.

---

## 6. Edge Cases & Handling
1. **Zero / New Account**: Neutral priors are assigned ($60-70$ range) so new users are not penalized before entering data.
2. **One-Time Income Spikes**: Large windfalls increase savings rate, capped at 100 points without mathematical overflow.
3. **No Goals Configured**: Rather than scoring 0 (which would drag score down by 15 points), an informative neutral baseline of 60 points is provided alongside a recommendation prompt.
