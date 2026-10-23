"""Cloud Cost Optimizer - Audits cloud resource inventory for waste, idle resources, and unused storage.

Author: henri983 (henrinyame2001@gmail.com)
Part of DevOps Toolbox Foundations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class CostLeak:
    resource_id: str
    resource_type: str
    region: str
    reason: str
    estimated_monthly_saving_usd: float
    recommended_action: str


@dataclass
class OptimizationSummary:
    total_resources_evaluated: int
    idle_resources_count: int
    total_potential_monthly_savings_usd: float
    leaks: List[CostLeak] = field(default_factory=list)


class CloudCostOptimizer:
    """Evaluates cloud resource metadata to identify waste and idle infrastructure costs."""

    # Indicative monthly unit costs for idle estimation
    HOURLY_RATES = {
        "t3.nano": 0.0052,
        "t3.micro": 0.0104,
        "t3.small": 0.0208,
        "t3.medium": 0.0416,
        "t3.large": 0.0832,
        "m5.large": 0.096,
        "c5.xlarge": 0.17,
    }
    GB_MONTH_EBS_RATE = 0.08  # gp3 storage $/GB-month

    def __init__(self, idle_cpu_threshold: float = 5.0, idle_days_threshold: int = 7) -> None:
        self.idle_cpu_threshold = idle_cpu_threshold
        self.idle_days_threshold = idle_days_threshold

    def evaluate_instances(self, instances: List[Dict[str, Any]]) -> List[CostLeak]:
        """Check compute instances for near-zero average CPU usage over evaluated window."""
        leaks: List[CostLeak] = []
        for inst in instances:
            avg_cpu = inst.get("avg_cpu_percent", 100.0)
            instance_type = inst.get("instance_type", "t3.medium")
            inst_id = inst.get("id", "unknown-inst")
            region = inst.get("region", "eu-west-3")
            state = inst.get("state", "running")

            if state == "running" and avg_cpu <= self.idle_cpu_threshold:
                hourly = self.HOURLY_RATES.get(instance_type, 0.0416)
                monthly = round(hourly * 730, 2)
                leaks.append(
                    CostLeak(
                        resource_id=inst_id,
                        resource_type=f"Compute ({instance_type})",
                        region=region,
                        reason=f"Average CPU {avg_cpu}% is below threshold {self.idle_cpu_threshold}%",
                        estimated_monthly_saving_usd=monthly,
                        recommended_action="Stop, terminate, or downscale instance",
                    )
                )
        return leaks

    def evaluate_volumes(self, volumes: List[Dict[str, Any]]) -> List[CostLeak]:
        """Check block storage volumes for unattached (available) state."""
        leaks: List[CostLeak] = []
        for vol in volumes:
            vol_id = vol.get("id", "unknown-vol")
            size_gb = vol.get("size_gb", 20)
            status = vol.get("status", "in-use")
            region = vol.get("region", "eu-west-3")

            if status in ("available", "unattached"):
                monthly = round(size_gb * self.GB_MONTH_EBS_RATE, 2)
                leaks.append(
                    CostLeak(
                        resource_id=vol_id,
                        resource_type=f"Block Storage ({size_gb} GB)",
                        region=region,
                        reason="Volume is unattached and accumulating storage charges",
                        estimated_monthly_saving_usd=monthly,
                        recommended_action="Take snapshot if required and delete unattached volume",
                    )
                )
        return leaks

    def run_optimization_audit(
        self,
        instances: List[Dict[str, Any]],
        volumes: List[Dict[str, Any]],
    ) -> OptimizationSummary:
        """Run full evaluation on instances and volumes."""
        inst_leaks = self.evaluate_instances(instances)
        vol_leaks = self.evaluate_volumes(volumes)
        all_leaks = inst_leaks + vol_leaks

        total_savings = round(sum(leak.estimated_monthly_saving_usd for leak in all_leaks), 2)
        total_count = len(instances) + len(volumes)

        return OptimizationSummary(
            total_resources_evaluated=total_count,
            idle_resources_count=len(all_leaks),
            total_potential_monthly_savings_usd=total_savings,
            leaks=all_leaks,
        )
