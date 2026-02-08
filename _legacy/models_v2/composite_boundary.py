"""Composite boundary derivation - tri-method validation.

Derives external I/O from internal topology using three methods
that must agree: Operad, Set Theory, and Data Flow.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any
from pydantic import BaseModel

from .port import Port
from .config import VALIDATE_BOUNDARY_TRI_METHOD

if TYPE_CHECKING:
    from .definition import Definition
    from .wire import Wire


class BoundaryDerivation(BaseModel):
    """
    Tri-method boundary derivation for composite I/O.
    
    Three methods that must agree:
    1. Operad: (All Inputs) - (Wired Inputs)
    2. Set Theory: Operad + promoted ports
    3. Data Flow: Reaching definitions analysis
    """
    internal_definitions: list[Any]  # list[Definition]
    internal_wires: list[Any]  # list[Wire]

    def derive_boundary(self) -> tuple[set[Port], set[Port]]:
        """
        Derive boundary I/O using tri-method validation.
        
        Returns: (boundary_inputs, boundary_outputs)
        """
        operad_result = self._derive_operad()
        
        if VALIDATE_BOUNDARY_TRI_METHOD:
            set_result = self._derive_set_theoretic()
            dataflow_result = self._derive_dataflow()
            
            # All three must agree
            assert operad_result == set_result, \
                f"Operad vs Set mismatch: {operad_result} != {set_result}"
            assert operad_result == dataflow_result, \
                f"Operad vs DataFlow mismatch: {operad_result} != {dataflow_result}"
        
        return operad_result

    def _derive_operad(self) -> tuple[set[Port], set[Port]]:
        """
        Operad algebra: Boundary = (All) - (Internal Wires)
        
        Input boundary: all inputs not satisfied by wires
        Output boundary: all outputs not consumed by wires
        """
        all_inputs: set[Port] = set()
        all_outputs: set[Port] = set()
        
        for defn in self.internal_definitions:
            all_inputs.update(defn.input_ports)
            all_outputs.update(defn.output_ports)
        
        wired_inputs = {w.target_port_id for w in self.internal_wires}
        consumed_outputs = {w.source_port_id for w in self.internal_wires}
        
        boundary_inputs = {p for p in all_inputs if p.id not in wired_inputs}
        boundary_outputs = {p for p in all_outputs if p.id not in consumed_outputs}
        
        return boundary_inputs, boundary_outputs

    def _derive_set_theoretic(self) -> tuple[set[Port], set[Port]]:
        """
        Set theory: Operad result + promoted ports.
        
        Accounts for ports that were promoted from inner scope.
        """
        base_inputs, base_outputs = self._derive_operad()
        
        # Check for promoted ports (name starts with "promoted_")
        for defn in self.internal_definitions:
            for port in defn.input_ports:
                if port.name.startswith("promoted_") and port.id not in {p.id for p in base_inputs}:
                    base_inputs.add(port)
            for port in defn.output_ports:
                if port.name.startswith("promoted_") and port.id not in {p.id for p in base_outputs}:
                    base_outputs.add(port)
        
        return base_inputs, base_outputs

    def _derive_dataflow(self) -> tuple[set[Port], set[Port]]:
        """
        Data flow analysis: Reaching definitions.
        
        Inputs: ports with no incoming data flow
        Outputs: ports with no outgoing data flow
        """
        all_inputs: set[Port] = set()
        all_outputs: set[Port] = set()
        
        for defn in self.internal_definitions:
            all_inputs.update(defn.input_ports)
            all_outputs.update(defn.output_ports)
        
        # Build reaching sets
        reached_inputs = {w.target_port_id for w in self.internal_wires}
        reaching_outputs = {w.source_port_id for w in self.internal_wires}
        
        boundary_inputs = {p for p in all_inputs if p.id not in reached_inputs}
        boundary_outputs = {p for p in all_outputs if p.id not in reaching_outputs}
        
        return boundary_inputs, boundary_outputs


def derive_composite_boundary(
    internal_definitions: list,
    internal_wires: list
) -> tuple[set[Port], set[Port]]:
    """
    Convenience function for boundary derivation.
    """
    derivation = BoundaryDerivation(
        internal_definitions=internal_definitions,
        internal_wires=internal_wires
    )
    return derivation.derive_boundary()
