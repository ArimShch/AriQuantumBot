def validate_gate_on_measured_qubits(
    gate_name: str,
    controls: list[int],
    targets: list[int],
    measured_qubits: list[int]
) -> None:
    """
    Validate if gate can be applied to qubits based on their measurement status.
    
    This function checks whether a quantum gate can be safely applied to the
    specified qubits, considering which qubits have already been measured.
    
    The validation logic follows specific rules for different gate types,
    matching the behavior of the original __check_measured method.
    
    Args:
        gate_name: String identifying the gate type (e.g., 'X', 'H', 'Rx').
        controls: List of control qubit indices or empty list.
        targets: Target qubit index as a single-element list [target].
        measured_qubits: Set of qubit indices that have been measured.
        
    Raises:
        ValueError: If gate cannot be applied due to measurement constraints.
    """
    # Extract target qubit (original method expects single target)
    targ = targets[0]
    
    # Convert controls and target to boolean flags based on measurement status
    ctrls_bool = []
    for c in controls:
        ctrls_bool.append(c in measured_qubits)
    
    targ_bool = targ in measured_qubits
    
    # Define gate type categories (matching original op_str1 and op_str2)
    op_str1 = {'I', 'X', 'Y', 'Z', 'S', 'T', 'Rz', 'P'}
    op_str2 = {'I', 'Z', 'S', 'T', 'Rz', 'P'}
    
    # Apply the same validation logic as in the original method
    if (
        (all(ctrls_bool) and targ_bool and gate_name in op_str1) or
        (any(ctrls_bool) and not targ_bool) or
        (not all(ctrls_bool) and targ_bool and gate_name in op_str2) or
        (not any(ctrls_bool) and not targ_bool)
    ):
        return
    else:
        raise ValueError(
            f"Quantum gate {gate_name} cannot be applied to measured qubits."
        )