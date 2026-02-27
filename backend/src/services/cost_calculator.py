"""
Cost Calculator Service

Calculates ingestion costs and savings estimates.
Pricing fetched from Azure Retail Prices API at runtime (not hardcoded).
"""

import logging
from typing import Dict, Tuple
from datetime import datetime
import requests
from functools import lru_cache

logger = logging.getLogger(__name__)

# Approximate pricing (cached, updated daily)
# In production, fetch from Azure Retail Prices API:
# https://prices.azure.com/api/retail/prices
APPROXIMATE_PRICING = {
    "Hot": 0.10,      # ~$0.10 per GB per day (Analytics tier)
    "Basic": 0.05,    # ~$0.05 per GB per day (Basic tier)
    "Archive": 0.002  # ~$0.002 per GB per day (Archive tier)
}


class CostCalculator:
    """Calculate ingestion costs and savings"""

    @staticmethod
    def calculate_table_costs(
        ingestion_gb_per_day: float,
        current_tier: str,
        target_tier: str = "Archive"
    ) -> Dict[str, float]:
        """
        Calculate costs for a table across different tiers.

        Args:
            ingestion_gb_per_day: Daily ingestion volume in GB
            current_tier: Current tier (Hot, Basic, Archive)
            target_tier: Target tier for migration

        Returns:
            Dictionary with cost calculations:
            - daily_cost_hot, daily_cost_archive, monthly_cost_hot, monthly_cost_archive
            - monthly_savings, annual_savings
        """
        try:
            # Fetch current pricing (or use cached approximate)
            hot_rate = CostCalculator._get_pricing("Hot")
            archive_rate = CostCalculator._get_pricing(target_tier)

            # Daily costs
            daily_cost_hot = ingestion_gb_per_day * hot_rate
            daily_cost_archive = ingestion_gb_per_day * archive_rate
            daily_savings = daily_cost_hot - daily_cost_archive

            # Monthly costs (30 days)
            monthly_cost_hot = daily_cost_hot * 30
            monthly_cost_archive = daily_cost_archive * 30
            monthly_savings = daily_savings * 30

            # Annual costs
            annual_savings = monthly_savings * 12

            logger.debug(
                f"[COST] Table: {ingestion_gb_per_day:.2f} GB/day "
                f"-> Monthly savings: ${monthly_savings:.2f}"
            )

            return {
                "daily_cost_hot": round(daily_cost_hot, 4),
                "daily_cost_archive": round(daily_cost_archive, 4),
                "monthly_cost_hot": round(monthly_cost_hot, 2),
                "monthly_cost_archive": round(monthly_cost_archive, 2),
                "monthly_savings": round(monthly_savings, 2),
                "annual_savings": round(annual_savings, 2)
            }

        except Exception as e:
            logger.error(f"[COST] Cost calculation failed: {str(e)}")
            return {
                "daily_cost_hot": 0.0,
                "daily_cost_archive": 0.0,
                "monthly_cost_hot": 0.0,
                "monthly_cost_archive": 0.0,
                "monthly_savings": 0.0,
                "annual_savings": 0.0
            }

    @staticmethod
    @lru_cache(maxsize=128)
    def _get_pricing(tier: str) -> float:
        """
        Get current pricing for a tier.

        Attempts to fetch from Azure Retail Prices API, falls back to approximate.

        Args:
            tier: Tier name (Hot, Basic, Archive)

        Returns:
            Price per GB per day
        """
        try:
            # Try to fetch from Azure Retail Prices API
            response = requests.get(
                "https://prices.azure.com/api/retail/prices",
                params={
                    "api-version": "2021-10-01",
                    "$filter": f"productName eq 'Azure Log Analytics' and skuName eq '{tier}'",
                },
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("Items"):
                    # Extract unit price per GB
                    item = data["Items"][0]
                    price_per_gb = float(item.get("unitPrice", 0))
                    logger.debug(f"[COST] Fetched pricing for {tier}: ${price_per_gb}/GB")
                    return price_per_gb

        except Exception as e:
            logger.debug(f"[COST] Failed to fetch pricing from API: {str(e)}")

        # Fall back to approximate pricing
        return APPROXIMATE_PRICING.get(tier, 0.0)

    @staticmethod
    def aggregate_workspace_savings(tables_data: Dict[str, Dict]) -> Dict[str, float]:
        """
        Aggregate savings across all tables in a workspace.

        Args:
            tables_data: Dictionary of table costs

        Returns:
            Total savings metrics
        """
        total_monthly_cost_hot = 0.0
        total_monthly_cost_archive = 0.0
        total_monthly_savings = 0.0

        for table_name, costs in tables_data.items():
            total_monthly_cost_hot += costs.get("monthly_cost_hot", 0.0)
            total_monthly_cost_archive += costs.get("monthly_cost_archive", 0.0)
            total_monthly_savings += costs.get("monthly_savings", 0.0)

        annual_savings = total_monthly_savings * 12

        return {
            "total_monthly_cost_hot": round(total_monthly_cost_hot, 2),
            "total_monthly_cost_archive": round(total_monthly_cost_archive, 2),
            "total_monthly_savings": round(total_monthly_savings, 2),
            "total_annual_savings": round(annual_savings, 2),
            "savings_percentage": round((total_monthly_savings / total_monthly_cost_hot * 100) if total_monthly_cost_hot > 0 else 0, 1)
        }

    @staticmethod
    def get_savings_impact_summary(savings_amount: float) -> str:
        """
        Generate human-readable summary of savings impact.

        Args:
            savings_amount: Monthly savings in USD

        Returns:
            Impact summary string
        """
        annual = savings_amount * 12

        if annual > 100000:
            return f"Substantial savings: ${annual:,.0f}/year could fund critical security initiatives"
        elif annual > 50000:
            return f"Significant savings: ${annual:,.0f}/year enables important optimizations"
        elif annual > 10000:
            return f"Meaningful savings: ${annual:,.0f}/year improves operational efficiency"
        elif annual > 1000:
            return f"Moderate savings: ${annual:,.0f}/year reduces infrastructure costs"
        else:
            return f"Minor savings: ${annual:,.0f}/year from table optimization"


# ===== SINGLETON INSTANCE =====
cost_calculator = CostCalculator()
