from src.tools import apply_discount, calculate_final_total, calculate_subtotal


def test_calculate_subtotal():
    assert calculate_subtotal(50, 120) == 6000.0


def test_apply_discount():
    assert apply_discount(6000, 15) == 5100.0


def test_apply_discount_zero_percent():
    assert apply_discount(1000, 0) == 1000.0


def test_calculate_final_total():
    assert calculate_final_total(5100, 250) == 5350.0


def test_full_pipeline_competition_example():
    subtotal = calculate_subtotal(50, 120)
    discounted = apply_discount(subtotal, 15)
    total = calculate_final_total(discounted, 250)
    assert total == 5350.0
