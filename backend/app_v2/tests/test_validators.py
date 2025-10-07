"""
Tests for validation utilities.

Tests data validators and validation rules.
"""

import pytest
from bson import ObjectId

from app_v2.utils.validators import (
    validate_object_id,
    validate_positive_number,
    validate_year,
    validate_currency_code,
    DataValidator
)


class TestBasicValidators:
    """Test basic validation functions."""
    
    def test_validate_object_id_valid(self):
        """Test valid ObjectId validation."""
        valid_id = ObjectId()
        is_valid, error = validate_object_id(valid_id)
        assert is_valid
        assert error is None
    
    def test_validate_object_id_string(self):
        """Test ObjectId string validation."""
        valid_id_str = str(ObjectId())
        is_valid, error = validate_object_id(valid_id_str)
        assert is_valid
        assert error is None
    
    def test_validate_object_id_invalid(self):
        """Test invalid ObjectId."""
        is_valid, error = validate_object_id("invalid")
        assert not is_valid
        assert error is not None
    
    def test_validate_positive_number_valid(self):
        """Test valid positive number."""
        is_valid, error = validate_positive_number(100.5)
        assert is_valid
        assert error is None
    
    def test_validate_positive_number_zero(self):
        """Test zero with allow_zero."""
        is_valid, error = validate_positive_number(0, allow_zero=True)
        assert is_valid
        
        is_valid, error = validate_positive_number(0, allow_zero=False)
        assert not is_valid
    
    def test_validate_positive_number_negative(self):
        """Test negative number."""
        is_valid, error = validate_positive_number(-10)
        assert not is_valid
        assert error is not None
    
    def test_validate_year_valid(self):
        """Test valid year."""
        is_valid, error = validate_year(2024)
        assert is_valid
        assert error is None
    
    def test_validate_year_invalid_range(self):
        """Test year outside valid range."""
        is_valid, error = validate_year(1800)
        assert not is_valid
        
        is_valid, error = validate_year(3000)
        assert not is_valid
    
    def test_validate_currency_code_valid(self):
        """Test valid currency codes."""
        for code in ["USD", "CAD", "EUR", "GBP"]:
            is_valid, error = validate_currency_code(code)
            assert is_valid, f"{code} should be valid"
    
    def test_validate_currency_code_invalid(self):
        """Test invalid currency code."""
        is_valid, error = validate_currency_code("XXX")
        assert not is_valid


class TestDataValidator:
    """Test DataValidator class."""
    
    def test_validate_equipment_specifications_valid(self):
        """Test valid equipment specifications."""
        specs = {
            "capacity_tph": 5000,
            "capacity_unit": "tph",
            "power_kw": 1120,
            "length_m": 5.0,
            "width_m": 3.0
        }
        
        is_valid, errors = DataValidator.validate_equipment_specifications(
            specs, "crusher"
        )
        
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_equipment_specifications_negative(self):
        """Test invalid equipment specifications (negative values)."""
        specs = {
            "capacity_tph": -1000,
            "power_kw": 1120
        }
        
        is_valid, errors = DataValidator.validate_equipment_specifications(
            specs, "crusher"
        )
        
        assert not is_valid
        assert len(errors) > 0
    
    def test_validate_crusher_specs(self):
        """Test crusher-specific validation."""
        specs = {
            "feed_opening_in": 60.0,
            "closed_side_setting_in": 8.0,
            "reduction_ratio": 7.5
        }
        
        is_valid, errors = DataValidator.validate_equipment_specifications(
            specs, "gyratory_crusher"
        )
        
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_cost_data_valid(self):
        """Test valid cost data."""
        cost_data = {
            "purchase_cost": 2500000,
            "purchase_cost_year": 2020,
            "purchase_cost_currency": "USD",
            "total_installed_cost": 8750000
        }
        
        is_valid, errors = DataValidator.validate_cost_data(cost_data)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_cost_data_invalid_multiplier(self):
        """Test cost data with unrealistic multiplier."""
        cost_data = {
            "purchase_cost": 2500000,
            "total_installed_cost": 30000000  # 12x multiplier - too high
        }
        
        is_valid, errors = DataValidator.validate_cost_data(cost_data)
        
        assert not is_valid
        assert any("multiplier" in err.lower() for err in errors)
    
    def test_validate_parameter_change_valid(self):
        """Test valid parameter change."""
        change = {
            "parameter_name": "capacity_tph",
            "original_value": 5000,
            "new_value": 4500,
            "unit": "tph"
        }
        
        is_valid, errors = DataValidator.validate_parameter_change(change)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_parameter_change_same_values(self):
        """Test parameter change with same values."""
        change = {
            "parameter_name": "capacity_tph",
            "original_value": 5000,
            "new_value": 5000
        }
        
        is_valid, errors = DataValidator.validate_parameter_change(change)
        
        assert not is_valid
        assert any("different" in err.lower() for err in errors)