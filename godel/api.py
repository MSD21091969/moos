"""Gödel API - Meta-analysis for definitions and containers.

Named after Kurt Gödel: Can assess what the system cannot assess about itself.
"""
from __future__ import annotations
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from models import Definition, Container, UserObject


class Assessment(BaseModel):
    """Result of a Gödel assessment."""
    score: float  # 0-100
    confidence: float  # 0-1
    rationale: str
    recommendations: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TestResult(BaseModel):
    """Result of a generation test."""
    version: int
    passed: bool
    expected: str
    actual: str
    error: Optional[str] = None


class GodelAPI:
    """
    Gödel API - The outside observer.
    
    Key insight: A system cannot assess whether its current definition
    could perform equally to a proposed change. But Gödel (outside) can.
    
    Capabilities:
    - Assess deltas between definitions
    - Harvest emerged definitions from containers
    - Test across generations and versions
    - Analyze patterns the system itself cannot see
    """
    
    def __init__(self, knowledge_base: Optional[list] = None):
        self.knowledge_base = knowledge_base or []
        self.assessments: list[Assessment] = []
        self.harvested: list[Definition] = []
    
    def assess_delta(
        self,
        current: Definition,
        proposed: Definition,
    ) -> Assessment:
        """
        Assess a proposed change from OUTSIDE the system.
        
        This is THE Gödel operation - answering what the system cannot.
        """
        # Compare I/O schemas
        current_io = current.compute_composite_io()
        proposed_io = proposed.compute_composite_io()
        
        # Scoring dimensions
        scores = {
            "io_compatibility": self._score_io_compatibility(current_io, proposed_io),
            "complexity_delta": self._score_complexity(current, proposed),
            "children_changed": self._score_children_changes(current, proposed),
        }
        
        avg_score = sum(scores.values()) / len(scores)
        
        # Generate rationale
        rationale = self._generate_rationale(current, proposed, scores)
        
        # Recommendations
        recommendations = []
        if scores["io_compatibility"] < 50:
            recommendations.append("I/O schemas diverge significantly - ensure compatibility")
        if scores["complexity_delta"] < 50:
            recommendations.append("Complexity increase is substantial - consider splitting")
        
        assessment = Assessment(
            score=avg_score,
            confidence=0.8,  # TODO: Compute from model certainty
            rationale=rationale,
            recommendations=recommendations,
        )
        
        self.assessments.append(assessment)
        return assessment
    
    def harvest_emerged(
        self,
        containers: list[Container],
    ) -> list[Definition]:
        """
        Extract emerged definitions from container compositions.
        
        This is where composite definitions are collected after simulation.
        """
        emerged = []
        
        for container in containers:
            composite = container.compute_composite_definition()
            if composite and not composite.is_atomic:
                emerged.append(composite)
        
        self.harvested.extend(emerged)
        return emerged
    
    def harvest_from_user(self, user: UserObject) -> Definition:
        """Harvest the user's composite definition."""
        composite = user.compute_composite()
        self.harvested.append(composite)
        return composite
    
    def test_generations(
        self,
        definition: Definition,
        versions: list[int],
        test_cases: list[dict],
    ) -> dict[int, list[TestResult]]:
        """
        Test expected fail/succeed across versions.
        
        This enables pattern analysis across generations.
        """
        results: dict[int, list[TestResult]] = {}
        
        for version in versions:
            version_results = []
            for test in test_cases:
                # TODO: Actually run the definition with test inputs
                result = TestResult(
                    version=version,
                    passed=True,  # Placeholder
                    expected=test.get("expected", ""),
                    actual="",  # Would be filled by actual execution
                )
                version_results.append(result)
            results[version] = version_results
        
        return results
    
    def analyze_patterns(self) -> dict:
        """
        Analyze patterns from harvested definitions.
        
        This is the meta-analysis that discovers good patterns.
        """
        patterns = {
            "total_harvested": len(self.harvested),
            "atomic_count": sum(1 for d in self.harvested if d.is_atomic),
            "composite_count": sum(1 for d in self.harvested if not d.is_atomic),
            "avg_children": sum(len(d.children) for d in self.harvested) / max(1, len(self.harvested)),
            "validated_count": sum(1 for d in self.harvested if d.is_validated),
        }
        
        return patterns
    
    def _score_io_compatibility(self, current_io, proposed_io) -> float:
        """Score I/O schema compatibility."""
        # Simple comparison - count matching inputs/outputs
        curr_in, curr_out = current_io
        prop_in, prop_out = proposed_io
        
        if not prop_in and not prop_out:
            return 100.0
        
        matching = 0
        total = len(prop_in) + len(prop_out)
        
        for pi in prop_in:
            if any(ci.name == pi.name for ci in curr_in):
                matching += 1
        for po in prop_out:
            if any(co.name == po.name for co in curr_out):
                matching += 1
        
        return (matching / max(1, total)) * 100
    
    def _score_complexity(self, current: Definition, proposed: Definition) -> float:
        """Score complexity change."""
        curr_count = len(current.get_all_descendants())
        prop_count = len(proposed.get_all_descendants())
        
        if prop_count <= curr_count:
            return 100.0
        
        delta = prop_count - curr_count
        return max(0, 100 - delta * 10)
    
    def _score_children_changes(self, current: Definition, proposed: Definition) -> float:
        """Score changes in children."""
        curr_children = {str(c.id) for c in current.children}
        prop_children = {str(c.id) for c in proposed.children}
        
        if not prop_children:
            return 100.0
        
        unchanged = len(curr_children & prop_children)
        return (unchanged / len(prop_children)) * 100
    
    def _generate_rationale(self, current, proposed, scores) -> str:
        """Generate human-readable rationale."""
        lines = [
            f"Comparing '{current.name}' → '{proposed.name}':",
            f"- I/O Compatibility: {scores['io_compatibility']:.0f}%",
            f"- Complexity Delta: {scores['complexity_delta']:.0f}%",
            f"- Children Changes: {scores['children_changed']:.0f}%",
        ]
        return "\n".join(lines)


# Singleton for easy access
_godel_instance: Optional[GodelAPI] = None


def get_godel_api() -> GodelAPI:
    """Get the Gödel API singleton."""
    global _godel_instance
    if _godel_instance is None:
        _godel_instance = GodelAPI()
    return _godel_instance
