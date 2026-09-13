from __future__ import annotations

import numpy as np

from bioland_us.behaviour import SmoothParticipationModel, predict_participation


MODEL = SmoothParticipationModel(
    intercept=-6.017543,
    ln_offer=0.943158,
    contract_10yr=-0.081661,
    pasture=0.0214773,
    switchgrass=0.746083,
)


def test_participation_is_monotonic_in_offer():
    offers = np.array([50.0, 100.0, 200.0, 300.0])
    p = predict_participation(
        offers,
        np.repeat(5, 4),
        np.repeat("Crop", 4),
        np.repeat("Poplar", 4),
        MODEL,
    )
    assert np.all(np.diff(p) > 0)


def test_ten_year_contract_has_lower_probability():
    p5 = predict_participation([100.0], [5], ["Crop"], ["Poplar"], MODEL)[0]
    p10 = predict_participation([100.0], [10], ["Crop"], ["Poplar"], MODEL)[0]
    assert p10 < p5


def test_switchgrass_probability_exceeds_poplar():
    poplar = predict_participation([100.0], [5], ["Crop"], ["Poplar"], MODEL)[0]
    switch = predict_participation([100.0], [5], ["Crop"], ["Switchgrass"], MODEL)[0]
    assert switch > poplar
