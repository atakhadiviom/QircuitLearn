import json
import cirq
import numpy as np

def circuit_from_json(data):
    n = data.get("qubits", 1)
    qs = [cirq.LineQubit(i) for i in range(n)]
    c = cirq.Circuit()
    for g in data.get("gates", []):
        t = g.get("type")
        q = g.get("target", 0)
        ctr = g.get("control")
        p = g.get("params", {})
        if t == "X":
            c.append(cirq.X(qs[q]))
        elif t == "Y":
            c.append(cirq.Y(qs[q]))
        elif t == "Z":
            c.append(cirq.Z(qs[q]))
        elif t == "H":
            c.append(cirq.H(qs[q]))
        elif t == "S":
            c.append(cirq.S(qs[q]))
        elif t == "T":
            c.append(cirq.T(qs[q]))
        elif t == "RX":
            c.append(cirq.rx(p.get("theta", 0))(qs[q]))
        elif t == "RY":
            c.append(cirq.ry(p.get("theta", 0))(qs[q]))
        elif t == "RZ":
            c.append(cirq.rz(p.get("theta", 0))(qs[q]))
        elif t == "CNOT" and ctr is not None:
            c.append(cirq.CNOT(qs[ctr], qs[q]))
        elif t == "SWAP":
            c.append(cirq.SWAP(qs[q], qs[p.get("other", q)]))
        elif t == "MEASURE":
            c.append(cirq.measure(qs[q], key=f"m{q}"))
    return c, qs

def simulate(data, shots=0):
    # Check for measurement gates
    has_measure = any(g.get("type") == "MEASURE" for g in data.get("gates", []))
    
    # If measurements exist and no specific shot count requested, 
    # we switch to sampling mode to show probabilities of outcomes
    if has_measure and shots == 0:
        shots = 1024
        run_sampling_for_probs = True
    else:
        run_sampling_for_probs = False

    c, qs = circuit_from_json(data)
    
    if shots and shots > 0:
        sim = cirq.Simulator()
        res = sim.run(c, repetitions=shots)
        
        if run_sampling_for_probs:
            # Convert raw measurement counts to probabilities histogram
            n_qubits = data.get("qubits", 1)
            probs = [0.0] * (2 ** n_qubits)
            
            # We need to iterate over shots to reconstruct the state index
            # res.measurements[key] is a numpy array of 0s and 1s
            # We can vectorize this for performance using numpy
            
            # Create a matrix of shape (shots, n_qubits)
            # Initialize with zeros (default for unmeasured qubits)
            shot_matrix = np.zeros((shots, n_qubits), dtype=int)
            
            for q in range(n_qubits):
                key = f"m{q}"
                if key in res.measurements:
                    shot_matrix[:, q] = res.measurements[key].flatten()
            
            # Convert bits to integer indices
            # weights: [2^(n-1), 2^(n-2), ..., 1]
            weights = 2 ** np.arange(n_qubits - 1, -1, -1)
            indices = shot_matrix.dot(weights)
            
            # Count occurrences
            unique, counts = np.unique(indices, return_counts=True)
            for idx, count in zip(unique, counts):
                probs[idx] = count / shots
                
            return {"probabilities": probs, "statevector": None}
        
        # Standard raw shots request
        return {k: list(v) for k, v in res.measurements.items()}

    sim = cirq.Simulator()
    # qubit_order=qs ensures all qubits are included in the state vector
    sv = sim.simulate(c, qubit_order=qs).final_state_vector
    probs = np.abs(sv) ** 2
    # Convert complex state vector to string representation for JSON serialization
    sv_serializable = [str(x) for x in sv.tolist()]
    return {"statevector": sv_serializable, "probabilities": probs.tolist()}
