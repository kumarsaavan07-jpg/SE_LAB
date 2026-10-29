
import pytest

from water_utility_billing import (
    calculate_water_bill,
    check_meter_tampering,
)


def test_invalid_accounts_type():
    with pytest.raises(ValueError):
        calculate_water_bill("invalid", 10)


def test_negative_base_fee():
    with pytest.raises(ValueError):
        calculate_water_bill([], -1)


def test_empty_accounts():
    result = calculate_water_bill([], 10)
    assert result["total_billed"] == 0.0
    assert result["status"] == "NO_ACTIVITY"


def test_inactive_and_missing_active_flag():
    accounts = [
        {"is_active": False, "usage_blocks": [30]},
        {"usage_blocks": [20]},
    ]
    result = calculate_water_bill(accounts, 10)
    assert result["total_billed"] == 0.0
    assert result["status"] == "NO_ACTIVITY"


def test_usage_at_lower_tier():
    accounts = [
        {"is_active": True, "usage_blocks": [30]}
    ]
    result = calculate_water_bill(accounts, 10)
    assert result["total_billed"] == 55.0


def test_usage_at_middle_tier():
    accounts = [
        {"is_active": True, "usage_blocks": [75]}
    ]
    result = calculate_water_bill(accounts, 10)
    assert result["total_billed"] == 197.5


def test_usage_exactly_50():
    accounts = [
        {"is_active": True, "usage_blocks": [50]}
    ]
    result = calculate_water_bill(accounts, 10)
    assert result["total_billed"] == 85.0


def test_commercial_usage_above_100():
    accounts = [
        {
            "is_active": True,
            "is_commercial": True,
            "usage_blocks": [120],
        }
    ]
    result = calculate_water_bill(accounts, 10)
    assert result["total_billed"] == 430.0


def test_residential_usage_above_100_breaks_loop():
    accounts = [
        {
            "is_active": True,
            "is_commercial": False,
            "usage_blocks": [120, 30],
        }
    ]
    result = calculate_water_bill(accounts, 10)
    assert result["total_billed"] == 550.0


def test_nonpositive_usage():
    accounts = [
        {"is_active": True, "usage_blocks": [0, -5, 30]}
    ]
    result = calculate_water_bill(accounts, 10)
    assert result["total_billed"] == 55.0


def test_empty_usage_blocks():
    accounts = [
        {"is_active": True, "usage_blocks": []}
    ]
    result = calculate_water_bill(accounts, 10)
    assert result["total_billed"] == 10.0


def test_leak_waiver_over_200():
    accounts = [
        {
            "is_active": True,
            "usage_blocks": [100],
            "has_leak_waiver": True,
        }
    ]
    result = calculate_water_bill(accounts, 100)
    assert result["total_billed"] == 300.0


def test_leak_waiver_at_or_below_200():
    accounts = [
        {
            "is_active": True,
            "usage_blocks": [10],
            "has_leak_waiver": True,
        }
    ]
    result = calculate_water_bill(accounts, 10)
    assert result["total_billed"] == 25.0


def test_waiver_not_enabled():
    accounts = [
        {"is_active": True, "usage_blocks": [10]}
    ]
    result = calculate_water_bill(accounts, 10)
    assert result["total_billed"] == 25.0


def test_excessive_flags():
    accounts = [
        {
            "is_active": True,
            "usage_blocks": [0, 0, 0, 0, 0, 0],
        }
    ]
    result = calculate_water_bill(accounts, 10)
    assert result["status"] == "EXCESSIVE_FLAGS"


def test_normal_status():
    accounts = [
        {"is_active": True, "usage_blocks": [30]}
    ]
    result = calculate_water_bill(accounts, 10)
    assert result["status"] == "NORMAL"


def test_meter_no_data():
    assert check_meter_tampering([]) == "NO_DATA"


def test_meter_tampering_detected():
    assert (
        check_meter_tampering([[-1, -2]])
        == "TAMPER_SUSPECTED"
    )


def test_meter_clear_after_positive_reading():
    assert check_meter_tampering([[-1, 2, -1]]) == "CLEAR"


def test_meter_clear_with_no_negative_readings():
    assert check_meter_tampering([[5, 4, 3]]) == "CLEAR"


def test_multiple_meters():
    assert check_meter_tampering([[-1], [2, 3]]) == "CLEAR"
