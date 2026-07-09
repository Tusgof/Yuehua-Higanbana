from __future__ import annotations

import math
from statistics import mean, pstdev


ONE_SIDED_95_Z = 1.6448536269514722


def normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def normal_pdf(value: float) -> float:
    return math.exp(-0.5 * value * value) / math.sqrt(2.0 * math.pi)


def sharpe_ratio(returns: list[float]) -> float | None:
    if len(returns) < 2:
        return None
    sigma = pstdev(returns)
    if sigma == 0:
        return None
    return mean(returns) / sigma


def skewness_population(returns: list[float]) -> float | None:
    if len(returns) < 2:
        return None
    mu = mean(returns)
    sigma = pstdev(returns)
    if sigma == 0:
        return None
    return sum(((value - mu) / sigma) ** 3 for value in returns) / len(returns)


def raw_kurtosis_population(returns: list[float]) -> float | None:
    if len(returns) < 2:
        return None
    mu = mean(returns)
    sigma = pstdev(returns)
    if sigma == 0:
        return None
    return sum(((value - mu) / sigma) ** 4 for value in returns) / len(returns)


def first_order_autocorrelation(returns: list[float]) -> float | None:
    if len(returns) < 3:
        return None
    head = returns[:-1]
    tail = returns[1:]
    mu_head = mean(head)
    mu_tail = mean(tail)
    denominator = math.sqrt(
        sum((value - mu_head) ** 2 for value in head)
        * sum((value - mu_tail) ** 2 for value in tail)
    )
    if denominator == 0:
        return None
    return sum((left - mu_head) * (right - mu_tail) for left, right in zip(head, tail)) / denominator


def generalized_sharpe_variance_term(
    observed_sharpe: float,
    skewness: float,
    raw_kurtosis: float,
) -> float:
    return 1.0 - skewness * observed_sharpe + ((raw_kurtosis - 1.0) / 4.0) * observed_sharpe * observed_sharpe


def autocorr_inflation(autocorrelation: float | None) -> float:
    if autocorrelation is None:
        return 1.0
    clipped = max(min(autocorrelation, 0.95), -0.95)
    return (1.0 + clipped) / (1.0 - clipped)


def effective_sample_length(sample_length: int, autocorrelation: float | None) -> float:
    return sample_length / autocorr_inflation(autocorrelation)


def probabilistic_sharpe_ratio(
    *,
    observed_sharpe: float,
    sample_length: int,
    skewness: float,
    raw_kurtosis: float,
    null_sharpe: float,
    autocorrelation: float | None = None,
) -> float:
    variance_term = max(generalized_sharpe_variance_term(observed_sharpe, skewness, raw_kurtosis), 1e-12)
    effective_n = effective_sample_length(sample_length, autocorrelation)
    statistic = (observed_sharpe - null_sharpe) * math.sqrt(max(effective_n - 1.0, 1.0)) / math.sqrt(variance_term)
    return normal_cdf(statistic)


def minimum_track_record_length(
    *,
    observed_sharpe: float,
    skewness: float,
    raw_kurtosis: float,
    null_sharpe: float,
    autocorrelation: float | None = None,
    z_score: float = ONE_SIDED_95_Z,
) -> int | None:
    if observed_sharpe <= null_sharpe:
        return None
    variance_term = max(generalized_sharpe_variance_term(observed_sharpe, skewness, raw_kurtosis), 1e-12)
    raw_length = 1.0 + variance_term * (z_score / (observed_sharpe - null_sharpe)) ** 2
    return math.ceil(raw_length * autocorr_inflation(autocorrelation))


def expected_shortfall(values: list[float], confidence: float) -> float | None:
    if not values:
        return None
    if confidence <= 0 or confidence >= 1:
        raise ValueError("confidence must be between 0 and 1")
    tail_count = max(1, math.ceil(len(values) * (1.0 - confidence)))
    return mean(sorted(values)[:tail_count])


def black_scholes_price_delta_gamma(
    *,
    spot: float,
    strike: float,
    years_to_expiry: float,
    rate: float,
    dividend_yield: float,
    volatility: float,
    right: str,
) -> dict[str, float]:
    if spot <= 0 or strike <= 0 or years_to_expiry <= 0 or volatility <= 0:
        raise ValueError("spot, strike, years_to_expiry, and volatility must be positive")
    sqrt_t = math.sqrt(years_to_expiry)
    d1 = (math.log(spot / strike) + (rate - dividend_yield + 0.5 * volatility * volatility) * years_to_expiry) / (
        volatility * sqrt_t
    )
    d2 = d1 - volatility * sqrt_t
    df_r = math.exp(-rate * years_to_expiry)
    df_q = math.exp(-dividend_yield * years_to_expiry)
    if right == "call":
        price = spot * df_q * normal_cdf(d1) - strike * df_r * normal_cdf(d2)
        delta = df_q * normal_cdf(d1)
    elif right == "put":
        price = strike * df_r * normal_cdf(-d2) - spot * df_q * normal_cdf(-d1)
        delta = -df_q * normal_cdf(-d1)
    else:
        raise ValueError(f"unsupported right: {right}")
    gamma = df_q * normal_pdf(d1) / (spot * volatility * sqrt_t)
    return {"price": price, "delta": delta, "gamma": gamma}
