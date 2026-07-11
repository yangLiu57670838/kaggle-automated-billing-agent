def apply_discount(subtotal: float, discount_percent: float) -> float:
    return float(subtotal) * (1 - float(discount_percent) / 100)
