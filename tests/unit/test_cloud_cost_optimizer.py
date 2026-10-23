"""Unit tests for cloud_cost_optimizer.py."""

from __future__ import annotations

from scripts.python.cloud_cost_optimizer import CloudCostOptimizer


def test_evaluate_idle_instances(cost_optimizer: CloudCostOptimizer) -> None:
    instances = [
        {"id": "i-idle01", "instance_type": "t3.large", "avg_cpu_percent": 1.5, "state": "running"},
        {"id": "i-active02", "instance_type": "t3.large", "avg_cpu_percent": 45.0, "state": "running"},
        {"id": "i-stopped03", "instance_type": "t3.large", "avg_cpu_percent": 0.0, "state": "stopped"},
    ]
    leaks = cost_optimizer.evaluate_instances(instances)
    assert len(leaks) == 1
    assert leaks[0].resource_id == "i-idle01"
    assert leaks[0].estimated_monthly_saving_usd > 0


def test_evaluate_unattached_volumes(cost_optimizer: CloudCostOptimizer) -> None:
    volumes = [
        {"id": "vol-unused01", "size_gb": 100, "status": "available"},
        {"id": "vol-active02", "size_gb": 50, "status": "in-use"},
    ]
    leaks = cost_optimizer.evaluate_volumes(volumes)
    assert len(leaks) == 1
    assert leaks[0].resource_id == "vol-unused01"
    assert leaks[0].estimated_monthly_saving_usd == 8.0  # 100 * 0.08


def test_run_full_optimization_audit(cost_optimizer: CloudCostOptimizer) -> None:
    instances = [
        {"id": "i-1", "instance_type": "t3.small", "avg_cpu_percent": 2.0, "state": "running"}
    ]
    volumes = [
        {"id": "v-1", "size_gb": 50, "status": "available"}
    ]
    summary = cost_optimizer.run_optimization_audit(instances, volumes)
    assert summary.total_resources_evaluated == 2
    assert summary.idle_resources_count == 2
    assert summary.total_potential_monthly_savings_usd > 0
