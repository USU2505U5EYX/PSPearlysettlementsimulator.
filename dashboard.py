import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from simulation import run_simulation
from risk import evaluate_liquidity


# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="PSP Treasury Intelligence",
    page_icon="🏦",
    layout="wide"
)

st.title("PSP Treasury & Settlement Intelligence")

st.caption(
    "Payment settlement liquidity simulation and capital adequacy"
)

st.divider()


# =====================================================
# SIDEBAR: SIMULATION CONTROLS
# =====================================================

st.sidebar.header("Simulation Parameters")

capital = st.sidebar.slider(
    "Available PSP Capital (₹ Crore)",
    min_value=1.0,
    max_value=10.0,
    value=3.0,
    step=0.25
)

acceptable_risk = st.sidebar.slider(
    "Acceptable Shortfall Risk (%)",
    min_value=0.1,
    max_value=20.0,
    value=5.0,
    step=0.5
)

scenarios = st.sidebar.select_slider(
    "Number of Scenarios",
    options=[1000, 2500, 5000, 10000, 20000],
    value=10000
)

days = st.sidebar.slider(
    "Simulation Period (Days)",
    min_value=7,
    max_value=90,
    value=30
)

daily_tpv = st.sidebar.number_input(
    "Average Daily TPV (₹ Crore)",
    min_value=0.1,
    max_value=100.0,
    value=4.5,
    step=0.5
)

discount = st.sidebar.number_input(
    "Early Settlement Discount (%)",
    min_value=0.01,
    max_value=5.0,
    value=0.20,
    step=0.05
)

annual_funding_cost = st.sidebar.number_input(
    "Annual Funding Cost (%)",
    min_value=0.1,
    max_value=50.0,
    value=12.0,
    step=0.5
)


# =====================================================
# RUN SIMULATION
# =====================================================

run_button = st.sidebar.button(
    "Run Treasury Simulation",
    type="primary",
    use_container_width=True
)


if run_button:

    with st.spinner("Running financial simulation..."):

        results = run_simulation(
            number_of_scenarios=scenarios,
            number_of_days=days,
            daily_tpv_mean=daily_tpv * 10_000_000,
            merchant_discount=discount / 100,
            annual_funding_cost=annual_funding_cost / 100
        )

        risk = evaluate_liquidity(
            simulation_results=results,
            available_capital=capital,
            acceptable_risk=acceptable_risk
        )

        st.session_state["results"] = results
        st.session_state["risk"] = risk


# =====================================================
# DISPLAY RESULTS
# =====================================================

if "results" in st.session_state:

    results = st.session_state["results"]
    risk = st.session_state["risk"]

    # ---------------------------------------------
    # KPI CARDS
    # ---------------------------------------------

    st.subheader("Treasury Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Available Capital",
        f"₹{capital:.2f} Cr"
    )

    col2.metric(
        "Shortfall Probability",
        f"{risk['shortfall_probability']:.2f}%"
    )

    col3.metric(
        "P95 Funding Requirement",
        f"₹{risk['p95_funding']/10_000_000:.2f} Cr"
    )

    col4.metric(
        "Required Capital",
        f"₹{risk['required_capital']/10_000_000:.2f} Cr"
    )

    # ---------------------------------------------
    # CAPITAL ADEQUACY
    # ---------------------------------------------

    st.divider()

    st.subheader("Capital Adequacy Assessment")

    if risk["capital_adequate"]:

        st.success(
            "Available capital meets the selected simulated risk threshold."
        )

    else:

        st.error(
            "Available capital does not meet the selected simulated risk threshold."
        )

    st.write(
        f"Additional capital required: "
        f"₹{risk['additional_capital_required']/10_000_000:.2f} crore"
    )

    # ---------------------------------------------
    # FUNDING EXPOSURE
    # ---------------------------------------------

    st.divider()

    st.subheader("Outstanding Funding Exposure")

    exposure = risk["average_daily_exposure"] / 10_000_000

    fig1 = go.Figure()

    fig1.add_trace(go.Scatter(
        x=list(range(1, days + 1)),
        y=exposure,
        mode="lines+markers",
        name="Average Exposure"
    ))

    fig1.add_hline(
        y=capital,
        line_dash="dash",
        annotation_text="Available Capital"
    )

    fig1.update_layout(
        xaxis_title="Simulation Day",
        yaxis_title="Funding (₹ Crore)",
        template="plotly_white"
    )

    st.plotly_chart(fig1, use_container_width=True)

    # ---------------------------------------------
    # PEAK FUNDING DISTRIBUTION
    # ---------------------------------------------

    st.divider()

    st.subheader("Peak Funding Distribution")

    peak = risk["peak_exposure_distribution"] / 10_000_000

    fig2 = go.Figure()

    fig2.add_trace(go.Histogram(
        x=peak,
        nbinsx=50,
        name="Peak Funding"
    ))

    fig2.add_vline(
        x=capital,
        line_dash="dot",
        annotation_text="Available Capital"
    )

    fig2.add_vline(
        x=risk["p95_funding"]/10_000_000,
        line_dash="dash",
        annotation_text="P95"
    )

    fig2.update_layout(
        xaxis_title="Peak Funding (₹ Crore)",
        yaxis_title="Number of Scenarios",
        template="plotly_white"
    )

    st.plotly_chart(fig2, use_container_width=True)

    # ---------------------------------------------
    # CAPITAL ADEQUACY CURVE
    # ---------------------------------------------

    st.divider()

    st.subheader("Capital Adequacy Curve")

    capacities = np.arange(1, 10.1, 0.1)

    shortfall_rates = [
        np.mean(
            risk["peak_exposure_distribution"] >
            c * 10_000_000
        ) * 100
        for c in capacities
    ]

    fig3 = go.Figure()

    fig3.add_trace(go.Scatter(
        x=capacities,
        y=shortfall_rates,
        mode="lines",
        name="Shortfall Probability"
    ))

    fig3.add_hline(
        y=acceptable_risk,
        line_dash="dash",
        annotation_text="Selected Risk Limit"
    )

    fig3.add_vline(
        x=capital,
        line_dash="dot",
        annotation_text="Available Capital"
    )

    fig3.update_layout(
        xaxis_title="PSP Capital (₹ Crore)",
        yaxis_title="Shortfall Probability (%)",
        template="plotly_white"
    )

    st.plotly_chart(fig3, use_container_width=True)

    # ---------------------------------------------
    # FINANCIAL SUMMARY
    # ---------------------------------------------

    st.divider()

    st.subheader("Financial Risk Summary")

    summary = pd.DataFrame({
        "Metric": [
            "Average Peak Exposure",
            "P95 Funding Requirement",
            "P99 Funding Requirement",
            "Maximum Funding Requirement",
            "Average Funding Gap When Breached"
        ],

        "Value (₹ Crore)": [
            risk["average_peak_exposure"],
            risk["p95_funding"],
            risk["p99_funding"],
            risk["maximum_funding"],
            risk["average_funding_gap"]
        ]
    })

    summary["Value (₹ Crore)"] /= 10_000_000

    st.dataframe(
        summary.round(3),
        use_container_width=True,
        hide_index=True
    )

    # ---------------------------------------------
    # EXPORT REPORT
    # ---------------------------------------------

    csv = summary.to_csv(index=False)

    st.download_button(
        label="Download Treasury Risk Report",
        data=csv,
        file_name="psp_treasury_risk_report.csv",
        mime="text/csv"
    )

else:

    st.info(
        "Adjust the simulation parameters in the sidebar "
        "and click Run Treasury Simulation."
    )
