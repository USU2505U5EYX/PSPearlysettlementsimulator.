import numpy as np


def run_simulation(
    number_of_scenarios=10000,
    number_of_days=30,
    daily_tpv_mean=45_000_000,
    daily_tpv_std=6_750_000,
    merchant_discount=0.002,
    annual_funding_cost=0.12,
    adoption_alpha=2,
    adoption_beta=8,
    random_seed=42
):

    rng = np.random.default_rng(random_seed)

    # 1. Generate transaction volumes
    daily_tpv = rng.normal(
        daily_tpv_mean,
        daily_tpv_std,
        size=(number_of_scenarios, number_of_days)
    )

    daily_tpv = np.maximum(daily_tpv, 0)

    # 2. Generate merchant adoption
    adoption_rates = rng.beta(
        adoption_alpha,
        adoption_beta,
        size=(number_of_scenarios, number_of_days)
    )

    early_settlement_volume = daily_tpv * adoption_rates

    # 3. Calculate payouts
    merchant_payouts = (
        early_settlement_volume * (1 - merchant_discount)
    )

    discount_revenue = (
        early_settlement_volume * merchant_discount
    )

    # 4. Generate settlement delays
    settlement_delays = rng.choice(
        [1, 2, 3],
        size=(number_of_scenarios, number_of_days),
        p=[0.80, 0.15, 0.05]
    )

    # 5. Calculate outstanding funding
    outstanding_funding = np.zeros(
        (number_of_scenarios, number_of_days)
    )

    origin_days = np.arange(number_of_days)

    for day in range(number_of_days):

        active_cohorts = (
            (origin_days <= day) &
            (day < origin_days + settlement_delays)
        )

        outstanding_funding[:, day] = np.sum(
            np.where(
                active_cohorts,
                merchant_payouts,
                0
            ),
            axis=1
        )

    # 6. Peak funding requirement
    peak_exposure = np.max(
        outstanding_funding,
        axis=1
    )

    # 7. Funding costs
    funding_cost = np.sum(
        merchant_payouts
        * annual_funding_cost
        * settlement_delays / 365,
        axis=1
    )

    # 8. Commercial economics
    total_discount_revenue = np.sum(
        discount_revenue,
        axis=1
    )

    return {
        "daily_tpv": daily_tpv,
        "adoption_rates": adoption_rates,
        "early_settlement_volume": early_settlement_volume,
        "merchant_payouts": merchant_payouts,
        "settlement_delays": settlement_delays,
        "outstanding_funding": outstanding_funding,
        "peak_exposure": peak_exposure,
        "funding_cost": funding_cost,
        "discount_revenue": total_discount_revenue
    }
