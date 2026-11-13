import numpy as np


def evaluate_liquidity(
    simulation_results,
    available_capital,
    acceptable_risk=5
):

    # Convert crore into rupees
    capacity = available_capital * 10_000_000

    # Retrieve simulated peak exposures
    peak_exposure = simulation_results["peak_exposure"]

    # Calculate shortfall probability
    shortfall_probability = np.mean(
        peak_exposure > capacity
    ) * 100

    # Calculate capital needed for selected risk tolerance
    required_capital = np.percentile(
        peak_exposure,
        100 - acceptable_risk
    )

    # Calculate funding gap
    funding_gap = np.maximum(
        peak_exposure - capacity,
        0
    )

    # Calculate average outstanding exposure
    average_exposure = np.mean(
        simulation_results["outstanding_funding"],
        axis=0
    )

    # Calculate peak funding statistics
    average_peak = np.mean(peak_exposure)
    p95 = np.percentile(peak_exposure, 95)
    p99 = np.percentile(peak_exposure, 99)

    # Capital adequacy assessment
    capital_adequate = (
        shortfall_probability <= acceptable_risk
    )

    return {

        "available_capital": capacity,

        "shortfall_probability": shortfall_probability,

        "acceptable_risk": acceptable_risk,

        "required_capital": required_capital,

        "additional_capital_required": max(
            required_capital - capacity,
            0
        ),

        "average_peak_exposure": average_peak,

        "p95_funding": p95,

        "p99_funding": p99,

        "maximum_funding": np.max(peak_exposure),

        "average_funding_gap": (
            np.mean(funding_gap[funding_gap > 0])
            if np.any(funding_gap > 0)
            else 0
        ),

        "average_daily_exposure": average_exposure,

        "capital_adequate": capital_adequate,

        "peak_exposure_distribution": peak_exposure

    }
