import requests
import json
import sys

def test_simulation():
    url = "http://127.0.0.1:5000/api/simulate"
    # Mock payload simulating the frontend
    payload = {
        "circuit": {
            "qubits": 1,
            "gates": [
                {"type": "H", "target": 0, "step": 0}
            ]
        },
        "shots": 0
    }
    
    # We can't easily test the running server from here without it running.
    # Instead, let's import the app and test the function directly.
    sys.path.append(".")
    from app.simulate import simulate
    
    print("Testing simulate function...")
    try:
        res = simulate(payload["circuit"], 0)
        print("Result keys:", res.keys())
        if "statevector" in res:
            print("Statevector found:", res["statevector"])
            print("SUCCESS: Statevector returned.")
        else:
            print("FAILURE: Statevector missing.")
            sys.exit(1)
            
        if "probabilities" in res:
             print("Probabilities found:", res["probabilities"])
        else:
             print("FAILURE: Probabilities missing.")
             sys.exit(1)
             
    except Exception as e:
        print(f"FAILURE: Exception occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_simulation()
