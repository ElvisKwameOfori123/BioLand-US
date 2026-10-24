import numpy as np
import pandas as pd

from bioland_us.economics import max_land_payment

ZERO_BUDGET = pd.Series({
    "year1_usd_per_ha": 0.0, "year2_usd_per_ha": 0.0, "later_usd_per_ha": 0.0,
    "year1_usd_per_t": 0.0, "year2_usd_per_t": 0.0, "later_usd_per_t": 0.0,
})


def test_no_costs_no_discount_spreads_revenue_over_the_stand():
    # 10-year stand, full yield from year 2 on: 9 harvests of 5 t at $70 over 10 years.
    out = max_land_payment(np.array([5.0]), 70.0, ZERO_BUDGET, stand_years=10,
                           discount_rate=0.0, year2_yield_share=1.0)
    assert np.isclose(out[0], 9 * 5 * 70 / 10)


def test_costs_lower_the_payable_rent_and_higher_yield_raises_it():
    budget = ZERO_BUDGET.copy()
    budget["year1_usd_per_ha"] = 500.0
    low, high = max_land_payment(np.array([3.0, 6.0]), 70.0, budget, stand_years=10,
                                 discount_rate=0.05, year2_yield_share=0.5)
    free = max_land_payment(np.array([3.0]), 70.0, ZERO_BUDGET, stand_years=10,
                            discount_rate=0.05, year2_yield_share=0.5)[0]
    assert low < free
    assert high > low
