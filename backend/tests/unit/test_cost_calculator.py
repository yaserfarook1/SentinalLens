"""
Unit tests for cost calculator

These tests verify REAL cost calculations based on actual Azure pricing.
"""

import pytest
from src.services.cost_calculator import cost_calculator
from src.models.schemas import TierType


class TestCostCalculator:
    """Test cost calculations with real Azure pricing"""

    def test_calculate_costs_for_single_table(self):
        """Test cost calculation for a single table"""
        # Real scenario: Table with 1 GB/day ingestion
        costs = cost_calculator.calculate_table_costs(
            ingestion_gb_per_day=1.0,
            current_tier="Hot",
            target_tier="Archive"
        )

        # Verify structure
        assert "daily_cost_hot" in costs
        assert "daily_cost_archive" in costs
        assert "monthly_savings" in costs
        assert "annual_savings" in costs

        # Verify calculations are reasonable
        assert costs["daily_cost_hot"] > costs["daily_cost_archive"]
        assert costs["monthly_savings"] > 0
        assert costs["annual_savings"] > costs["monthly_savings"]

    def test_calculate_costs_100_gb_per_day(self):
        """Test real-world scenario: 100 GB/day table"""
        costs = cost_calculator.calculate_table_costs(
            ingestion_gb_per_day=100.0,
            current_tier="Hot",
            target_tier="Archive"
        )

        # Approximate pricing:
        # Hot: ~$0.10/GB/day = $3000/month for 100 GB/day
        # Archive: ~$0.002/GB/day = $60/month for 100 GB/day
        # Savings: ~$2940/month

        assert costs["monthly_savings"] > 2000  # More than $2000/month
        assert costs["monthly_savings"] < 4000  # Less than $4000/month
        assert costs["annual_savings"] > 20000  # More than $20k/year

    def test_calculate_costs_zero_ingestion(self):
        """Test edge case: table with zero ingestion"""
        costs = cost_calculator.calculate_table_costs(
            ingestion_gb_per_day=0.0,
            current_tier="Hot",
            target_tier="Archive"
        )

        assert costs["monthly_savings"] == 0.0
        assert costs["annual_savings"] == 0.0

    def test_aggregate_workspace_savings(self):
        """Test aggregating savings across multiple tables"""
        tables_data = {
            "SecurityEvent": {
                "monthly_cost_hot": 300.0,
                "monthly_cost_archive": 10.0,
                "monthly_savings": 290.0
            },
            "SigninLogs": {
                "monthly_cost_hot": 150.0,
                "monthly_cost_archive": 5.0,
                "monthly_savings": 145.0
            },
            "AuditLogs": {
                "monthly_cost_hot": 100.0,
                "monthly_cost_archive": 3.0,
                "monthly_savings": 97.0
            }
        }

        summary = cost_calculator.aggregate_workspace_savings(tables_data)

        # Verify totals
        assert summary["total_monthly_cost_hot"] == 550.0
        assert summary["total_monthly_cost_archive"] == 18.0
        assert summary["total_monthly_savings"] == 532.0
        assert summary["total_annual_savings"] == 6384.0

        # Verify savings percentage
        assert summary["savings_percentage"] > 90  # >90% savings

    def test_savings_impact_summary_large_savings(self):
        """Test impact summary for substantial savings"""
        summary = cost_calculator.get_savings_impact_summary(10000.0)

        assert "120000" in summary or "$120,000" in summary
        assert "year" in summary.lower()

    def test_savings_impact_summary_small_savings(self):
        """Test impact summary for small savings"""
        summary = cost_calculator.get_savings_impact_summary(50.0)

        assert "year" in summary.lower()
        assert "$600" in summary

    def test_pricing_fetch_fallback(self):
        """Test that pricing falls back to approximate values"""
        # This tests the fallback mechanism
        price = cost_calculator._get_pricing("Hot")

        # Should return a reasonable price
        assert price > 0
        assert price < 1.0  # Per GB/day should be < $1

    def test_hot_vs_archive_cost_delta(self):
        """Test that Archive is significantly cheaper than Hot"""
        hot_price = cost_calculator._get_pricing("Hot")
        archive_price = cost_calculator._get_pricing("Archive")

        # Archive should be at least 40x cheaper than Hot
        assert hot_price / archive_price >= 40

    def test_real_world_multi_table_scenario(self):
        """Test real-world scenario with multiple tables of different sizes"""
        tables_data = {}

        # Large table (50 GB/day)
        tables_data["LargeTable"] = cost_calculator.calculate_table_costs(50.0, "Hot", "Archive")

        # Medium table (10 GB/day)
        tables_data["MediumTable"] = cost_calculator.calculate_table_costs(10.0, "Hot", "Archive")

        # Small table (1 GB/day)
        tables_data["SmallTable"] = cost_calculator.calculate_table_costs(1.0, "Hot", "Archive")

        # Unused table (0.01 GB/day)
        tables_data["UnusedTable"] = cost_calculator.calculate_table_costs(0.01, "Hot", "Archive")

        summary = cost_calculator.aggregate_workspace_savings(tables_data)

        # Verify reasonable totals
        assert summary["total_annual_savings"] > 1000  # At least $1000/year
        assert summary["savings_percentage"] > 0

    def test_monthly_to_annual_conversion(self):
        """Test that annual savings is 12x monthly savings"""
        costs = cost_calculator.calculate_table_costs(
            ingestion_gb_per_day=10.0,
            current_tier="Hot",
            target_tier="Archive"
        )

        # Annual should be exactly 12 * monthly
        assert abs(costs["annual_savings"] - (costs["monthly_savings"] * 12)) < 0.01
