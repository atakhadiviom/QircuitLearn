import unittest
import json
import numpy as np
import sys
import os

# Add the project root to the path so we can import the app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.simulate import simulate

class TestSimulation(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'ok'})

    def test_landing_page(self):
        # Verify landing page loads
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'QircuitLearn', response.data)

    def test_basic_simulation_x_gate(self):
        # Test X gate (NOT)
        # q0: |0> -> X -> |1>
        payload = {
            "circuit": {
                "qubits": 1,
                "gates": [{"type": "X", "target": 0, "step": 0}]
            },
            "shots": 0
        }
        response = self.client.post('/api/simulate', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json
        
        # Probabilities: |0> should be 0, |1> should be 1
        probs = data['probabilities']
        self.assertAlmostEqual(probs[0], 0.0)
        self.assertAlmostEqual(probs[1], 1.0)

    def test_superposition_h_gate(self):
        # Test H gate (Hadamard)
        # q0: |0> -> H -> (|0> + |1>)/sqrt(2)
        payload = {
            "circuit": {
                "qubits": 1,
                "gates": [{"type": "H", "target": 0, "step": 0}]
            },
            "shots": 0
        }
        response = self.client.post('/api/simulate', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json
        
        # Probabilities: |0> ~ 0.5, |1> ~ 0.5
        probs = data['probabilities']
        self.assertAlmostEqual(probs[0], 0.5)
        self.assertAlmostEqual(probs[1], 0.5)

    def test_bell_pair(self):
        # Test Bell Pair: H(q0) -> CNOT(q0, q1)
        # Result: (|00> + |11>)/sqrt(2)
        payload = {
            "circuit": {
                "qubits": 2,
                "gates": [
                    {"type": "H", "target": 0, "step": 0},
                    {"type": "CNOT", "target": 1, "control": 0, "step": 1}
                ]
            },
            "shots": 0
        }
        response = self.client.post('/api/simulate', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json
        
        probs = data['probabilities']
        # |00> (idx 0) and |11> (idx 3) should be 0.5
        # |01> (idx 1) and |10> (idx 2) should be 0
        self.assertAlmostEqual(probs[0], 0.5)
        self.assertAlmostEqual(probs[1], 0.0)
        self.assertAlmostEqual(probs[2], 0.0)
        self.assertAlmostEqual(probs[3], 0.5)

    def test_rotation_gates(self):
        # Test RX gate
        # RX(pi) on |0> should be -i|1> (prob of 1 is 100%)
        # RX(pi/2) on |0> should be (|0> - i|1>)/sqrt(2) (prob 50/50)
        
        # Case 1: RX(pi) -> Flip to |1>
        payload_rx = {
            "circuit": {
                "qubits": 1,
                "gates": [
                    {"type": "RX", "target": 0, "step": 0, "params": {"theta": 3.14159265359}}
                ]
            }
        }
        res = self.client.post('/api/simulate', json=payload_rx)
        probs = res.json['probabilities']
        self.assertAlmostEqual(probs[1], 1.0, places=4)

        # Case 2: RY(pi/2) -> (|0> + |1>)/sqrt(2) -> Same probs as H
        payload_ry = {
            "circuit": {
                "qubits": 1,
                "gates": [
                    {"type": "RY", "target": 0, "step": 0, "params": {"theta": 1.57079632679}}
                ]
            }
        }
        res = self.client.post('/api/simulate', json=payload_ry)
        probs = res.json['probabilities']
        self.assertAlmostEqual(probs[0], 0.5, places=4)
        self.assertAlmostEqual(probs[1], 0.5, places=4)

if __name__ == '__main__':
    unittest.main()
