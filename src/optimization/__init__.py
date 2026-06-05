"""Budget optimisation: SciPy constrained allocation + scenario analysis."""

from .budget_optimizer import optimize_budget, OptimizationResult
from .scenario import compare_scenarios

__all__ = ["optimize_budget", "OptimizationResult", "compare_scenarios"]
