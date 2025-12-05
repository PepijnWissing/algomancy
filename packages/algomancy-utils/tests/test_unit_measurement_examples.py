from src.algomancy import (
    QUANTITIES,
    BaseMeasurement,
    Measurement,
    create_currency_quantity,
)


def test_length_scaling_outputs_reasonable_units():
    length = QUANTITIES["length"]
    length_m = BaseMeasurement(length["m"], min_digits=1, max_digits=3, decimals=2)

    # Very small should scale to micrometers or nanometers; very large to km
    small = Measurement(length_m, 0.000005)  # 5e-6 m -> likely μm
    large = Measurement(length_m, 2_500_000)  # -> likely km

    small_pretty = small.pretty()
    large_pretty = large.pretty()

    assert (
        isinstance(small_pretty, str) and small_pretty
    ), "pretty() should return non-empty string"
    assert (
        isinstance(large_pretty, str) and large_pretty
    ), "pretty() should return non-empty string"

    assert "μm" in small_pretty, "μm is the expected small-unit"
    assert "Mm" in large_pretty, "Mm is the expected large-unit"


def test_length_scaling_respects_max_min_unit():
    length = QUANTITIES["length"]
    length_m = BaseMeasurement(
        length["m"],
        min_digits=1,
        max_digits=3,
        decimals=2,
        smallest_unit="mm",
        largest_unit="km",
    )

    # Very small should scale to micrometers or nanometers; very large to km
    small = Measurement(length_m, 0.000005)  # 5e-6 m
    large = Measurement(length_m, 2_500_000)

    small_pretty = small.pretty()
    large_pretty = large.pretty()

    assert (
        isinstance(small_pretty, str) and small_pretty
    ), "pretty() should return non-empty string"
    assert (
        isinstance(large_pretty, str) and large_pretty
    ), "pretty() should return non-empty string"

    assert "mm" in small_pretty, "mm is the expected small-unit"
    assert "km" in large_pretty, "km is the expected large-unit"


def test_mass_time_data_examples_do_not_raise_and_return_strings():
    # Mass
    mass = QUANTITIES["mass"]
    mass_g = BaseMeasurement(mass["g"], min_digits=1, max_digits=3, decimals=2)
    for val in [0.5, 50, 5_000, 50_000_000]:
        assert Measurement(mass_g, val).pretty()

    # Time
    time = QUANTITIES["time"]
    time_s = BaseMeasurement(time["s"], min_digits=1, max_digits=2, decimals=1)
    for val in [0.000_001, 0.5, 45, 3_665, 86_400]:
        assert Measurement(time_s, val).pretty()

    # Data (binary)
    data = QUANTITIES["data"]
    data_b = BaseMeasurement(data["B"], min_digits=1, max_digits=3, decimals=2)
    outputs = [
        Measurement(data_b, v).pretty() for v in [512, 5_120, 5_242_880, 5_368_709_120]
    ]
    assert any("KiB" in o for o in outputs)
    assert any("MiB" in o for o in outputs)


def test_money_and_custom_currency_scaling_contains_expected_unit_symbols():
    money = QUANTITIES["money"]
    usd_base = BaseMeasurement(money["$"], min_digits=0, max_digits=3, decimals=2)

    vals = [0.50, 50, 1_234_567, 5_000_000_000]
    outs = [Measurement(usd_base, v).pretty() for v in vals]

    # Check that expected money unit symbols appear at some scales
    assert any("$" in o for o in outs)
    assert any("k$" in o or "M$" in o or "B$" in o or "T$" in o for o in outs)

    # Custom currency (EUR)
    eur = create_currency_quantity("€", "Euro")
    eur_base = BaseMeasurement(eur["€"], min_digits=1, max_digits=3, decimals=2)
    eur_outs = [
        Measurement(eur_base, v).pretty() for v in [50, 5_000, 500_000, 50_000_000]
    ]
    assert any("€" in o for o in eur_outs)


def test_scale_to_same_unit_behaviour():
    # Length: mm vs km; ensure units match after scaling
    length = QUANTITIES["length"]
    m1 = Measurement(BaseMeasurement(length["mm"], decimals=2), 1_500_000)
    m2 = Measurement(BaseMeasurement(length["km"], decimals=2), 2.5)

    m1_to_m2 = m1.scale_to_unit(m2)
    m2_to_m1 = m2.scale_to_unit(m1)

    assert isinstance(str(m1_to_m2), str) and str(m1_to_m2)
    assert isinstance(str(m2_to_m1), str) and str(m2_to_m1)

    # Units should now match the target's current unit
    assert m1_to_m2.unit.name == m2.unit.name
    assert m2_to_m1.unit.name == m1.unit.name

    # Money example: $ vs M$
    money = QUANTITIES["money"]
    revenue = Measurement(BaseMeasurement(money["$"], decimals=2), 1_234_567)
    budget = Measurement(BaseMeasurement(money["M$"], decimals=2), 5.5)

    rev_in_budget_units = revenue.scale_to_unit(budget)
    bud_in_revenue_units = budget.scale_to_unit(revenue)

    assert rev_in_budget_units.unit.name == budget.unit.name
    assert bud_in_revenue_units.unit.name == revenue.unit.name


def test_auto_scaled_and_matched_time_examples():
    time = QUANTITIES["time"]
    time_s = BaseMeasurement(time["s"], min_digits=1, max_digits=2, decimals=1)

    t1 = Measurement(time_s, 45)
    t2 = Measurement(time_s, 7_200)

    t1_scaled = t1.scale()
    t2_scaled = t2.scale()

    # basic sanity: scaling returns Measurement-like printable strings
    assert str(t1_scaled)
    assert str(t2_scaled)

    matched_1 = t1.scale_to_unit(t2_scaled)
    matched_2 = t2.scale_to_unit(t1_scaled)

    assert matched_1.unit.name == t2_scaled.unit.name
    assert matched_2.unit.name == t1_scaled.unit.name
