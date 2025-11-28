# Zero to Hero: QircuitLearn Product Roadmap

This roadmap outlines the path from a basic quantum circuit simulator to a comprehensive educational platform for quantum computing.

## Phase 1: Foundations (Current Status: In Progress)
**Goal:** Solidify the core learning experience and ensure the "happy path" is bug-free and engaging.

- [x] **Core Simulator**: Qubit simulation, basic gates (H, X, Y, Z, CNOT), measurement.
- [x] **Visualization**: State vector probabilities, Bloch sphere representation.
- [x] **Interactive Lessons**: Lesson content with specific interactive tasks (e.g., "Create a Bell Pair").
- [x] **Goal Verification**: Real-time validation of user circuits against lesson criteria.
- [ ] **User Progress Persistence**: (Partial) Currently mocked; needs proper user authentication and database persistence for production.
- [ ] **UI Polish**: Improve drag-and-drop targets, mobile responsiveness, and error messages.

## Phase 2: The Quantum Technician (Intermediate)
**Goal:** Introduce intermediate concepts and standard quantum protocols.

- [ ] **Expanded Gate Set**:
    - Phase Gates: $S$, $S^\dagger$, $T$, $T^\dagger$.
    - Rotation Gates: $R_x(\theta)$, $R_y(\theta)$, $R_z(\theta)$ with interactive angle sliders.
    - Toffoli (CCNOT) gate for classical logic implementation.
- [ ] **Key Protocols**:
    - **Quantum Teleportation**: A guided level where users "move" a state from q0 to q2.
    - **Superdense Coding**: Transmitting two classical bits using one qubit.
- [ ] **Math Visualizer**:
    - "Show the Math" toggle: Display the matrix multiplication step-by-step as gates are applied.
    - Bra-ket notation display updates in real-time.

## Phase 3: The Algorithm Designer (Advanced)
**Goal:** Users implement famous quantum algorithms.

- [ ] **Grover's Algorithm**:
    - Implement "Oracle" blocks (black boxes) that the user must query.
    - Search for a marked state in an unstructured database.
- [ ] **Quantum Fourier Transform (QFT)**:
    - Step-by-step construction of the QFT circuit.
    - Visualizing the frequency domain transformation.
- [ ] **Deutsch-Jozsa Algorithm**:
    - Determining if a function is constant or balanced with a single query.
- [ ] **Custom Composites**: Allow users to group gates into a custom block (e.g., "MyQFT") to reuse in larger circuits.

## Phase 4: Real World & Community (Mastery)
**Goal:** Bridge the gap between simulation and real hardware constraints.

- [ ] **Noise Simulation**:
    - Introduce "decoherence" and "gate errors" to show why real quantum computers are difficult to build.
    - Challenge: "Error Correction" levels (Repetition codes).
- [ ] **QASM Export**:
    - Export circuits to OpenQASM format to run on real hardware (e.g., IBM Quantum).
- [ ] **Community Features**:
    - "Playground" mode: Build and share circuit URLs.
    - Leaderboards: "Fewest Gates Challenge" for specific algorithms.

## Technical Infrastructure Needs
- **Authentication**: Replace mock User ID with real OAuth/Email login.
- **Backend Optimization**: For >10 qubits, move from naive matrix multiplication to sparse matrix libraries or tensor network simulators (or limit to <10 qubits for education).
- **Frontend Testing**: E2E tests (Cypress/Playwright) for the drag-and-drop interface.
