# QircuitLearn: Quantum Computing Without the Math

**Stop drowning in linear algebra. Start understanding the concepts that actually matter.**

QircuitLearn is an interactive, web-based platform designed to teach quantum computing from a "concept-first" perspective. It avoids the typical physics/math-heavy introduction and focuses on intuition, interactive simulation, and real-world utility.

## 🚀 Features

*   **No-Nonsense Curriculum**: A 13-lesson "Zero to Hero" course that explains quantum concepts using analogies (spinning coins, mazes) rather than dense equations.
*   **Interactive Circuit Simulator**: A drag-and-drop quantum circuit builder running entirely in the browser (frontend) with a powerful Python backend (Cirq).
    *   Support for H, X, Y, Z, S, T, SWAP, and CNOT gates.
    *   Visual representation of quantum states.
    *   Probability histograms.
*   **Modern Web Design**: Clean, responsive UI built with modern CSS (variables, flexbox/grid) and vanilla JavaScript.
*   **Shared Hosting Ready**: Designed to be easily deployed on standard shared hosting environments (cPanel/Passenger) using Flask.

## 📚 Curriculum Overview

The course is divided into 7 Phases:

1.  **The Wall**: Why classical computers fail (Combinatorial Explosion).
2.  **The Quantum Weirdness**: Superposition and Entanglement (The "Spinning Coin" & "Magic Dice").
3.  **The Quantum Speedup**: Parallelism & Interference (The "Water in the Maze").
4.  **The Reality Check**: Noise & Decoherence.
5.  **The "Killer Apps"**: Simulation & Optimization.
6.  **The Logic**: Quantum Gates & Circuits (Rotations & Music Scores).
7.  **The Valley of Death**: The roadmap to becoming a practitioner (Linear Algebra & Coding).

## 🛠️ Tech Stack

*   **Backend**: Python (Flask)
*   **Quantum Simulation**: Google Cirq
*   **Frontend**: HTML5, CSS3, Vanilla JavaScript (Drag & Drop API)
*   **Visualization**: Chart.js
*   **Database**: SQLite (Simple, file-based)
*   **Deployment**: Passenger WSGI (for Shared Hosting)

## 💻 Installation & Local Development

1.  **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/QircuitLearn.git
    cd QircuitLearn
    ```

2.  **Create a Virtual Environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Initialize the Database**
    ```bash
    python seed.py
    ```
    This will create `qircuit.db` and populate it with the full curriculum.

5.  **Run the Application**
    ```bash
    python run.py
    ```
    Access the app at `http://localhost:5001`.

## 🌐 Deployment (Shared Hosting)

This project is configured for deployment on shared hosting platforms (like Namecheap, Bluehost, A2) that support **Python via CloudLinux/Passenger**.

1.  Upload files to your server.
2.  Ensure `passenger_wsgi.py` is present (it hooks into Flask).
3.  Install dependencies via the hosting control panel or SSH.
4.  The `public/` folder in your hosting should point to the application root.

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

[MIT](https://choosealicense.com/licenses/mit/)
