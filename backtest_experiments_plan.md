# 0DTE Hybrid Trading System: Backtest Experiment Plan

To validate the trading edge of our proposed 0DTE trading system, we must conduct a series of controlled backtesting experiments. This plan defines **10 key experiments** designed to isolate the impact of each core component of the system.

---

## Experiment 1: Market-Maker Volatility Attenuation Filter

* **Objective**: To test if dynamically sizing or disabling the sub-systems based on the Market Maker's Net Gamma Proxy (NOVI) improves overall risk-adjusted returns.
* **Experimental Setup**:
  - **Control Group (A)**: Run the dual-system with a fixed 50/50 capital split on all days without any Net Gamma filtering.
  - **Treatment Group (B)**: Scale position sizes dynamically based on the Net Gamma Proxy (reduce Sub-System A size and enable Sub-System B when MM Net Gamma is positive/high; enable Sub-System A and disable Sub-System B when MM Net Gamma is negative).
* **Independent Variable (ตัวแปรต้น)**: Activation of the Market-Maker Net Gamma filter logic.
* **Dependent Variable (ตัวแปรตาม)**: Portfolio Sharpe Ratio, Win Rate of Sub-System A, and Drawdown.
* **Hypothesis**: Integrating the Market Maker's Net Gamma proxy reduces false breakouts in Sub-System A (ORB) and protects Sub-System B (Ratio Spreads) from tail-risk spikes on short-gamma days, resulting in a higher overall Sharpe ratio and lower drawdowns.
* **Metrics for Success (If Hypothesis is True)**:
  - The portfolio Sharpe Ratio increases by $\ge 0.15$ compared to the control group.
  - Maximum Drawdown (MDD) decreases by $\ge 20\%$.
  - The Win Rate of Sub-System A (ORB) increases on active days.

---

## Experiment 2: LLM Hybrid Sentiment Filtering Layer (Gatekeeper)

* **Objective**: To test if qualitative news analysis by an LLM adds value over simple quantitative filters (like VIX and the macro calendar).
* **Experimental Setup**:
  - **Control Group (A)**: Run the system using only quantitative filters (VIX 15–25 and macro calendar exclusions).
  - **Treatment Group (B)**: Run the system with both quantitative filters AND the LLM News Gatekeeper (blocking all trades on days with an LLM Risk Score $\ge 7$).
* **Independent Variable (ตัวแปรต้น)**: Activation of the LLM News Gatekeeper filter.
* **Dependent Variable (ตัวแปรตาม)**: Portfolio Expected Shortfall (ES 99%) and Worst-Day Loss.
* **Hypothesis**: The LLM Sentiment Filter successfully identifies qualitative geopolitical and systemic panic risks from unstructured news text that quantitative indicators miss, preventing the system from entering trades on highly adverse days and reducing the frequency of extreme tail losses.
* **Metrics for Success (If Hypothesis is True)**:
  - Expected Shortfall (ES 99%) is reduced (moves closer to zero) by $\ge 15\%$.
  - The portfolio's Worst-Day Loss magnitude is reduced.
  - The portfolio Sharpe ratio increases because we avoid catastrophic loss days without sacrificing too many profitable days.

---

## Experiment 3: Portfolio Construction (Risk Parity vs. Equal Weight)

* **Objective**: To test if allocating capital based on Risk Parity (Expected Shortfall) outperforms a simple Equal-Weight capital split.
* **Experimental Setup**:
  - **Control Group (A)**: Allocate capital evenly: 50% to Sub-System A and 50% to Sub-System B.
  - **Treatment Group (B)**: Allocate capital using Risk Parity based on historical Expected Shortfall (e.g. 70% Sub-System A / 30% Sub-System B).
* **Independent Variable (ตัวแปรต้น)**: Portfolio capital allocation method (Equal-Weight vs. Risk Parity).
* **Dependent Variable (ตัวแปรตาม)**: Portfolio Maximum Drawdown, Sortino Ratio (downside risk-adjusted return).
* **Hypothesis**: Because Sub-System B (Capped-Risk Put Ratio Spread) has a higher risk profile than Sub-System A (Debit Spreads), an equal-weight split will cause portfolio drawdowns to be entirely dominated by Sub-System B. Risk Parity balances the risk contributions, leading to a smoother equity curve.
* **Metrics for Success (If Hypothesis is True)**:
  - Portfolio Maximum Drawdown is lower than the S&P 500 Buy & Hold benchmark.
  - The portfolio's Sortino Ratio increases by $\ge 0.20$ compared to the control group.
  - The risk contribution of both sub-systems is equalized in the historical log.

---

## Experiment 4: Moneyness-Based Strike Selection vs. Delta-Based Selection

* **Objective**: To test if selecting option strikes using fixed moneyness (distance as a % of index price) outperforms selecting strikes using fixed Delta targets.
* **Experimental Setup**:
  - **Control Group (A)**: Select strikes using fixed Delta targets at the 10:00 AM ET entry time (e.g., Buy 30-Delta, Sell 15-Delta puts).
  - **Treatment Group (B)**: Select strikes using the paper's fixed Moneyness Grid (0.98 to 1.02 with 0.001 increments).
* **Independent Variable (ตัวแปรต้น)**: Strike selection methodology (Delta-Based vs. Moneyness-Based).
* **Dependent Variable (ตัวแปรตาม)**: Average Trade Expected Value (EV) of Sub-System B, and the frequency of short strikes being breached.
* **Hypothesis**: Moneyness-based strike selection maintains a constant physical barrier relative to the underlying index price, protecting the strategy from the "Delta-drift trap" where strikes are pulled closer to the market during low-volatility regimes or late in the session, reducing the frequency of short strikes being breached.
* **Metrics for Success (If Hypothesis is True)**:
  - The frequency of the short strikes being breached in Sub-System B drops by $\ge 15\%$.
  - The average trade Expected Value (EV) of the Moneyness-based system is more stable across varying volatility sub-periods compared to the Delta-based system.

---

## Experiment 5: Tuesday/Thursday Expiration Expansion (Structural Break)

* **Objective**: To test if the trading edge of both strategies differs significantly before and after the introduction of daily (Tuesday/Thursday) expirations on May 11, 2022.
* **Experimental Setup**:
  - Run the backtest over the full sample (e.g. 2019-2026) and partition the performance results into two distinct sub-periods:
    - **Sub-period 1**: Pre-May 11, 2022 (Monday/Wednesday/Friday expirations only).
    - **Sub-period 2**: Post-May 11, 2022 (Daily expirations).
  - Compare Sharpe ratios, win rates, and average trade expected value between both sub-periods.
* **Independent Variable (ตัวแปรต้น)**: Expiration regime (Pre-2022 vs. Post-2022 daily listings).
* **Dependent Variable (ตัวแปรตาม)**: Average Trade Expected Value, Skewness of returns, and Portfolio Sharpe Ratio.
* **Hypothesis**: The introduction of daily 0DTE listings (post-May 11, 2022) increased market efficiency, compressed option skew, and reduced the average premium yield (VRP), resulting in a statistically significant drop in Sharpe ratio for both systems compared to the pre-2022 period.
* **Metrics for Success (If Hypothesis is True)**:
  - Confirm if the Sharpe ratio in Sub-period 2 is lower than in Sub-period 1.
  - Determine if the strategies still maintain a positive Sharpe ratio above the S&P 500 Buy & Hold benchmark after May 11, 2022.

---

## Experiment 6: VIX Regime Range Sensitivity Analysis

* **Objective**: To test if the original VIX filter range (15–25) is indeed the optimal range for the portfolio compared to alternative volatility boundaries.
* **Experimental Setup**:
  - Run the backtest under four different VIX regime filters:
    - **Group 1**: VIX 15–25 (Original baseline from papers).
    - **Group 2**: Low Volatility (VIX < 15).
    - **Group 3**: High Volatility (VIX > 25).
    - **Group 4**: Unfiltered (No VIX constraints).
* **Independent Variable (ตัวแปรต้น)**: VIX range constraint boundaries.
* **Dependent Variable (ตัวแปรตาม)**: Portfolio Sharpe Ratio, Max Drawdown, and Transaction Cost Drag.
* **Hypothesis**: The VIX 15–25 range provides the optimal balance. Strategies with VIX < 15 suffer from low premium capture (VRP is too small to cover bid-ask spreads), while VIX > 25 suffers from excessive bid-ask spreads and severe tail drawdowns, making VIX 15–25 the only range that outperforms the benchmark.
* **Metrics for Success (If Hypothesis is True)**:
  - Group 1 (VIX 15-25) yields the highest Sharpe ratio and Sortino ratio.
  - Group 3 (VIX > 25) shows the highest Maximum Drawdown and transaction cost drag.

---

## Experiment 7: Transaction Cost & Execution Latency Sensitivity

* **Objective**: To test prompt robustness for the LLM gate first, then test the system's vulnerability to transaction costs (bid-ask spread) and execution delays (latency).
* **Experimental Setup**:
  - **Prompt Pre-Experiment**: Before using the LLM gate in later experiments, compare multiple prompt variants for the OpenRouter DeepSeek V4 flash thinking target model:
    - **Prompt A**: conservative tail-risk blocker focused on avoiding catastrophic days.
    - **Prompt B**: balanced Go/No-Go scorer with explicit risk score and reasons.
    - **Prompt C**: structured volatility, directional bias, tail-risk, and strategy-suitability assessment.
  - Evaluate prompt variants on the same archived input set before any strategy performance comparison. Store prompt text, input hash, model id, output, decision, timestamp, and parser result for every run.
  - Run the backtest under different transaction costs and execution latencies:
    - **Group 1**: Standard assumption (Mid-price + 30-sec limit order protocol + 0.5 bp slippage/fee).
    - **Group 2**: Full Spread (Market orders, paying the full bid-ask spread on all legs).
    - **Group 3**: Execution Latency (Delaying entries and exits by 1, 2, and 5 minutes after signals trigger).
* **Independent Variable (ตัวแปรต้น)**: Prompt variant first; then execution slippage model and execution delay time.
* **Dependent Variable (ตัวแปรตาม)**: Prompt decision stability, parser validity, false block/false allow review rate, portfolio net PNL, Sharpe Ratio, and transaction cost drag.
* **Hypothesis**: The LLM gate needs a prompt that is stable, parseable, and not overly aggressive before it can be used in strategy experiments. Separately, 0DTE options decay and move so rapidly that execution delays $\ge 2$ minutes or paying the full bid-ask spread on multi-leg trades (Sub-System B) will completely erase the strategy's trading edge, leading to a negative Sharpe ratio.
* **Metrics for Success (If Hypothesis is True)**:
  - One prompt variant has valid structured outputs on all archived test inputs and materially fewer unexplained or contradictory decisions than the alternatives.
  - The selected prompt's block decisions are explainable by tail-risk, volatility, directional bias, or strategy-suitability evidence rather than vague sentiment.
  - Group 2 (Full Spread) and Group 3 (Latency $\ge 2$ min) exhibit negative Sharpe ratios and negative net PNL.
  - Quantify the exact threshold of transaction costs and latency beyond which the system becomes unprofitable.

---

## Experiment 8: Intraday Entry Timing Sensitivity

* **Objective**: To determine if the paper's default entry times (9:35 AM for ORB, 10:00 AM for Volatility) are optimal compared to alternative times of day.
* **Experimental Setup**:
  - Run the backtest, varying the entry times for both sub-systems:
    - **Sub-System A (ORB)**: Entry on breakout of 5-min range (9:35 AM), 15-min range (9:45 AM), or 30-min range (10:00 AM).
    - **Sub-System B (Volatility)**: Entry at 10:00 AM, 11:30 AM, 1:00 PM, and 2:30 PM ET.
* **Independent Variable (ตัวแปรต้น)**: Intraday entry timestamp.
* **Dependent Variable (ตัวแปรตาม)**: Win rate, average trade PNL, and premium yield capture.
* **Hypothesis**: Entering Sub-System B early in the day (10:00 AM) captures the peak of the intraday Variance Risk Premium (VRP), while entering later (e.g. 1:00 PM) suffers from severe time-decay premium compression that does not justify the trading costs. For Sub-System A, the 5-min ORB provides the best breakout alpha before mean reversion kicks in.
* **Metrics for Success (If Hypothesis is True)**:
  - 10:00 AM entries for Sub-System B yield the highest Net Sharpe and highest premium-to-underlying PNL compared to afternoon entries.
  - Sub-System A's 5-minute ORB yields a higher win rate and PNL compared to 15-minute or 30-minute ORB versions.

---

## Experiment 9: Exit Stop-Loss and Profit Target Optimization

* **Objective**: To optimize the exit parameters (profit target and stop-loss) for both sub-systems.
* **Experimental Setup**:
  - Run the backtest, varying the exit thresholds:
    - **Sub-System A (ORB)**: Test various combinations of Profit Target / Stop-Loss: 25%/50% (baseline), 20%/40%, 30%/60%, and no stop-loss (held to close).
    - **Sub-System B (Ratio)**: Test adding an intraday stop-loss (e.g., exiting if the spread loss exceeds 2x, 3x, or 5x the initial credit/debit) vs. the baseline (no stops, held to 3:45 PM ET).
* **Independent Variable (ตัวแปรต้น)**: Exit profit target and stop-loss percentages.
* **Dependent Variable (ตัวแปรตาม)**: Average Trade Expected Value (EV), Max Drawdown, and Win Rate.
* **Hypothesis**: The baseline 25%/50% exit for Sub-System A balances win rate and payout ratio optimally. For Sub-System B, adding a conservative intraday stop-loss reduces maximum drawdown and Expected Shortfall by preventing catastrophic losses during rare tail-risk days, even if it slightly reduces the overall win rate.
* **Metrics for Success (If Hypothesis is True)**:
  - The 25%/50% exit for Sub-System A yields the highest Net PNL compared to other combinations.
  - Adding an intraday stop-loss to Sub-System B reduces the Maximum Drawdown by $\ge 15\%$ and improves the Sortino ratio.

---

## Experiment 10: Granular Macro-Event Filter Sensitivity

* **Objective**: To test if blocking all macro-event days is necessary, or if we can optimize the calendar filter by isolating specific types of events.
* **Experimental Setup**:
  - Run the backtest under different event-blocking rules:
    - **Group 1**: Block all event days (FOMC, CPI, NFP, Fed speeches - baseline).
    - **Group 2**: Block only morning event days (CPI, NFP released at 8:30 AM ET).
    - **Group 3**: Block only afternoon event days (FOMC released at 2:00 PM ET).
    - **Group 4**: Do not block any event days (unfiltered).
* **Independent Variable (ตัวแปรต้น)**: The type of macro-events blocked.
* **Dependent Variable (ตัวแปรตาม)**: Portfolio Expected Shortfall, Sharpe Ratio, and total trade count.
* **Hypothesis**: Afternoon event days (FOMC) cause the most severe intraday jumps and volatility spikes during the trading session, making them critical to block. Morning event days (CPI, NFP) are released before the open and are mostly reflected in the opening price, meaning we can trade them safely after the 9:35 AM ORB breakout is established.
* **Metrics for Success (If Hypothesis is True)**:
  - Trading on morning event days (Group 3 active) increases the portfolio's total Net PNL by increasing trade frequency without increasing Max Drawdown.
  - Trading on FOMC days (Group 2 active) results in severe drawdowns and high Expected Shortfall (ES).
