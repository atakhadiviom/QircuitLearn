import sqlite3
import os
import json
from werkzeug.security import generate_password_hash

def seed():
    db_type = os.getenv("DB_TYPE", "sqlite")
    print("Initializing database (Zero to Hero Curriculum)...")
    conn = None
    cur = None
    if db_type == "postgres":
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASS", ""),
            dbname=os.getenv("DB_NAME", "qircuitlearn"),
            port=int(os.getenv("DB_PORT", "5432"))
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        with open("schema_postgres.sql", "r") as f:
            statements = f.read().split(";")
            for s in statements:
                s = s.strip()
                if s:
                    cur.execute(s)
        conn.commit()
    else:
        db_path = "qircuit.db"
        if os.path.exists(db_path):
            os.remove(db_path)
            print("Removed existing database for fresh seed.")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        with open("schema_sqlite.sql", "r") as f:
            conn.executescript(f.read())
    
    def _row_get(row, key, index=0):
        try:
            return row[key]
        except Exception:
            try:
                return row[index]
            except Exception:
                return None

    # 0. Create Superuser
    print("Creating superuser...")
    admin_user = "admin"
    admin_email = "admin@example.com"
    admin_pass = "admin123"
    pwd_hash = generate_password_hash(admin_pass, method='pbkdf2:sha256')
    
    if db_type == "postgres":
        cur.execute(
            "INSERT INTO users(username, email, password_hash, is_superuser) VALUES(%s, %s, %s, %s)",
            (admin_user, admin_email, pwd_hash, True)
        )
    else:
        cur.execute(
            "INSERT INTO users(username, email, password_hash, is_superuser) VALUES(?, ?, ?, ?)",
            (admin_user, admin_email, pwd_hash, 1) # SQLite uses 1 for True
        )

    # 1. Define Courses & Lessons
    courses_data = [
        {
            "slug": "stage-1-foundations",
            "title": "Stage 1: The Non-Negotiable Foundations",
            "description": "You cannot understand quantum mechanics without this toolkit.",
            "lessons": [
                {
                    "slug": "linear-algebra-vectors",
                    "title": "1. Linear Algebra: Vectors",
                    "content": """
<h2>Linear Algebra: Vectors</h2>
<p>Let's get to work. In classical mechanics, we might use a vector to describe the position or velocity of a ball. In Quantum Computing, we use a vector to describe the <strong>state</strong> of the system—literally everything we know about it.</p>
<p>These aren't just arrows in space; they are specific mathematical objects called <strong>State Vectors</strong>, and they live in a complex vector space called a <strong>Hilbert Space</strong>.</p>

<h3>1. The Standard Basis (The "Axes")</h3>
<p>In a classical computer, a bit is either 0 or 1. In a quantum computer, we treat these as column vectors. We call this the "Computational Basis."</p>
<ul>
    <li>The state "Zero" is denoted as $|0\\rangle$: $$|0\\rangle = \\begin{pmatrix} 1 \\\\ 0 \\end{pmatrix}$$</li>
    <li>The state "One" is denoted as $|1\\rangle$: $$|1\\rangle = \\begin{pmatrix} 0 \\\\ 1 \\end{pmatrix}$$</li>
</ul>
<p><em>(Note: The symbol $|\\psi\\rangle$ is called a "ket". This is Dirac Notation, and it's the standard language of quantum mechanics.)</em></p>

<h3>2. Superposition (Linear Combination)</h3>
<p>The power of quantum computing comes from <strong>Linearity</strong>. We can add these vectors together. A qubit can be in a state that is a linear combination (superposition) of $|0\\rangle$ and $|1\\rangle$:</p>
$$|\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle$$
<p>Here, $\\alpha$ (alpha) and $\\beta$ (beta) are numbers that describe "how much" of 0 and 1 are in the state.</p>
<p><strong>Here is your first task:</strong></p>
<p>Using the column definitions for $|0\\rangle$ and $|1\\rangle$ above, if you perform the matrix addition and scalar multiplication for $\\alpha|0\\rangle + \\beta|1\\rangle$, what does the single resulting column vector look like?</p>
                    """,
                    "position": 1,
                    "task_json": None,
                    "section": "linear-algebra"
                },
                {
                    "slug": "linear-algebra-matrices",
                    "title": "2. Linear Algebra: Matrices",
                    "content": """
<h2>Matrices</h2>
<p>That's the correct progression. If <strong>vectors</strong> are the <strong>states</strong> of a quantum system, then <strong>matrices</strong> are the <strong>operations</strong> we perform on those states.</p>
<p>In Quantum Computing, a single-qubit <strong>quantum gate</strong> is represented by a $2 \\times 2$ matrix. When you apply a gate to a qubit, you perform standard <strong>matrix-vector multiplication</strong>.</p>
$$|\\psi'\\rangle = U |\\psi\\rangle$$
<p>Where $U$ is the matrix (the gate) and $|\\psi\\rangle$ is the state vector.</p>

<h3>⚛️ Key Gate: The Pauli-X (Quantum NOT)</h3>
<p>The most fundamental operation is the <strong>Pauli-X</strong> gate, often simply called $X$. This is the quantum equivalent of the classical NOT gate, which flips the bit: $0 \\leftrightarrow 1$.</p>
<p>The matrix for the $X$ gate is:</p>
$$X = \\begin{pmatrix} 0 & 1 \\\\ 1 & 0 \\end{pmatrix}$$

<p>You can verify that:</p>
<ul>
    <li>$X|0\\rangle = \\begin{pmatrix} 0 & 1 \\\\ 1 & 0 \\end{pmatrix} \\begin{pmatrix} 1 \\\\ 0 \\end{pmatrix} = \\begin{pmatrix} 0 \\\\ 1 \\end{pmatrix} = |1\\rangle$</li>
    <li>$X|1\\rangle = \\begin{pmatrix} 0 & 1 \\\\ 1 & 0 \\end{pmatrix} \\begin{pmatrix} 0 \\\\ 1 \\end{pmatrix} = \\begin{pmatrix} 1 \\\\ 0 \\end{pmatrix} = |0\\rangle$</li>
</ul>

<h3>Your Task: Applying $X$ to Superposition</h3>
<p>Let's test the linearity. Consider a superposition state $|\\psi\\rangle$ where the chance of being $|0\\rangle$ or $|1\\rangle$ is equal. Its normalized vector is:</p>
$$|\\psi\\rangle = \\frac{1}{\\sqrt{2}}\\begin{pmatrix} 1 \\\\ 1 \\end{pmatrix}$$
<p>Calculate the resulting state, $|\\psi'\\rangle$, when you apply the $X$ gate to $|\\psi\\rangle$. What is the final column vector?</p>
                    """,
                    "position": 2,
                    "task_json": None,
                    "section": "linear-algebra"
                },
                {
                    "slug": "linear-algebra-eigenvalues",
                    "title": "3. Linear Algebra: Eigenvalues",
                    "content": """
<h2>Eigenvalues and Eigenvectors</h2>
<p>In Quantum Computing, Eigenvalues and Eigenvectors are the language that translates a quantum operation into a physical, observable result.</p>

<h3>1. 🔑 The Core Equation</h3>
<p>An Eigenvector is a special vector $|\\psi\\rangle$ that, when acted upon by a matrix $U$, only gets scaled, not rotated.</p>
<p>The amount it is scaled by is the Eigenvalue $\\lambda$:</p>
$$U|\\psi\\rangle = \\lambda|\\psi\\rangle$$

<h3>🧠 QC Interpretation: Observables and Outcomes</h3>
<ul>
    <li><strong>The Matrix $U$ is the Observable:</strong> A matrix that represents a physical property we can measure, like energy or spin. In our case, this is the measurement operator (usually the Pauli-Z gate).</li>
    <li><strong>The Eigenvectors are the Measurable States:</strong> These special states ($\\{|\\psi\\rangle\\}$) are the only states the qubit can collapse into upon measurement. For a single qubit measured in the standard basis, the eigenvectors are simply $|0\\rangle$ and $|1\\rangle$.</li>
    <li><strong>The Eigenvalues are the Measurement Results:</strong> The values ($\\lambda$) tell us what the result of the measurement is. In quantum mechanics, these are real numbers. We map them to the outcomes 0 and 1.</li>
</ul>

<h3>🚪 Introducing the Pauli-Z Gate ($Z$)</h3>
<p>The Pauli-Z gate is the standard observable for measurement in the computational basis. Its matrix is:</p>
$$Z = \\begin{pmatrix} 1 & 0 \\\\ 0 & -1 \\end{pmatrix}$$

<h3>Your Task:</h3>
<p>Apply the Pauli-Z matrix ($Z$) to our basis states, $|0\\rangle$ and $|1\\rangle$.</p>
<ul>
    <li>Calculate $Z|0\\rangle$. What is the resulting vector and its corresponding eigenvalue ($\\lambda_0$)?</li>
    <li>Calculate $Z|1\\rangle$. What is the resulting vector and its corresponding eigenvalue ($\\lambda_1$)?</li>
</ul>
<p>This will reveal why $|0\\rangle$ and $|1\\rangle$ are the special states we measure.</p>
                    """,
                    "position": 3,
                    "task_json": None,
                    "section": "linear-algebra"
                },
                {
                    "slug": "linear-algebra-inner-products",
                    "title": "4. Linear Algebra: Inner Products",
                    "content": """
<h2>Inner Products</h2>
<p>The <strong>Inner Product</strong> is the final, essential piece of single-qubit linear algebra. It is the tool that turns abstract vectors into concrete, measurable probabilities.</p>

<h3>1. The Bra Vector and Dirac Notation</h3>
<p>To perform the Inner Product, we need the <strong>bra</strong> vector. The bra $\\langle \\phi |$ is the Hermitian conjugate (the complex conjugate transpose) of the ket $|\\phi\\rangle$.</p>
<p>If the ket for $|0\\rangle$ is:</p>
$$|0\\rangle = \\begin{pmatrix} 1 \\\\ 0 \\end{pmatrix}$$
<p>Then the corresponding bra $\\langle 0 |$ is a row vector:</p>
$$\\langle 0 | = \\begin{pmatrix} 1 & 0 \\end{pmatrix}$$

<h3>2. The Inner Product (Bra-Ket)</h3>
<p>The <strong>Inner Product</strong> of two state vectors, $|\\psi\\rangle$ and $|\\phi\\rangle$, is the matrix multiplication of the bra $\\langle \\phi |$ and the ket $|\\psi\\rangle$, resulting in a single complex number (a scalar):</p>
$$\\langle \\phi | \\psi \\rangle = \\begin{pmatrix} \\phi_0^* & \\phi_1^* \\end{pmatrix} \\begin{pmatrix} \\psi_0 \\\\ \\psi_1 \\end{pmatrix} = \\phi_0^* \\psi_0 + \\phi_1^* \\psi_1$$

<h3>3. Measurement Probability 🎯</h3>
<p>In quantum mechanics, the probability ($P$) of measuring a state $|\\psi\\rangle$ to be in a specific state $|\\phi\\rangle$ is given by the squared magnitude of their inner product:</p>
$$P(|\\psi\\rangle \\text{ collapses to } |\\phi\\rangle) = |\\langle \\phi | \\psi \\rangle|^2$$

<hr>

<h3>Your Task:</h3>
<p>Consider the common superposition state $|+\\rangle$:</p>
$$|+\\rangle = \\frac{1}{\\sqrt{2}}|0\\rangle + \\frac{1}{\\sqrt{2}}|1\\rangle = \\frac{1}{\\sqrt{2}}\\begin{pmatrix} 1 \\\\ 1 \\end{pmatrix}$$
<p>Calculate the probability $P$ that when we measure the state $|+\\rangle$, it collapses to the $|0\\rangle$ state.</p>
<ol>
    <li>First, calculate the inner product $\\langle 0 | + \\rangle$.</li>
    <li>Then, find the probability $P = |\\langle 0 | + \\rangle|^2$.</li>
</ol>
                    """,
                    "position": 4,
                    "task_json": None,
                    "section": "linear-algebra"
                },
                {
                    "slug": "linear-algebra-hilbert-spaces",
                    "title": "5. Linear Algebra: Hilbert Spaces",
                    "content": """
<h2>Hilbert Spaces</h2>
<p>Excellent. You've built all the necessary components: states, operators, measurement. Now we need the <strong>container</strong> for all of it.</p>

<p>A <strong>Hilbert Space ($\mathcal{H}$)</strong> is simply the formal, mathematical environment where all the rules of quantum computing live. It is a specific type of vector space with three core properties that make it suitable for quantum mechanics:</p>

<ol>
    <li><strong>It is a Vector Space:</strong> 🌌 This means it contains all possible linear combinations (superpositions) of the basis states. If $|0\\rangle$ and $|1\\rangle$ are in the space, then the vector $|\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle$ must also be in the space.</li>
    <li><strong>It has an Inner Product:</strong> $\\langle \\cdot | \\cdot \\rangle$ This allows us to calculate the <strong>length</strong> of vectors (normalization, ensuring $|\\alpha|^2 + |\\beta|^2 = 1$) and the <strong>angle</strong> between them (orthogonality, ensuring we can distinguish basis states).</li>
    <li><strong>It is Complete:</strong> This is a technical property that ensures every sequence of vectors that "should" converge, does converge to a valid vector within the space. Physically, this means every possible measurement outcome corresponds to a valid quantum state.</li>
</ol>

<h3>The Single-Qubit Space</h3>
<p>For a single qubit, the Hilbert space is 2-dimensional ($\mathcal{H} = \mathbb{C}^2$). The Bloch sphere is the visual representation of all the possible vectors in this 2-dimensional complex space.</p>

<h3>📈 Scaling Up</h3>
<p>The true power of the Hilbert space concept is in describing systems with multiple qubits. To describe $N$ independent qubits, we use a mathematical operation called the <strong>tensor product</strong> (which we'll cover next) to combine their individual spaces.</p>

<p>For an $N$-qubit system, the dimension of the Hilbert space is:</p>
$$\\text{Dimension}(\\mathcal{H}_N) = 2^N$$

<hr>

<h3>Your Task:</h3>
<p>Based on this scaling rule, what is the dimension of the Hilbert space needed to fully describe the state of a system composed of <strong>two qubits</strong>?</p>
                    """,
                    "position": 5,
                    "task_json": None,
                    "section": "linear-algebra"
                },
                {
                    "slug": "complex-numbers-arithmetic",
                    "title": "6. Complex Numbers: Arithmetic",
                    "content": """
<h2>Complex Arithmetic</h2>
<p>That is the essential next step. If linear algebra is the <strong>structure</strong> of quantum mechanics, <strong>complex numbers</strong> are the very <strong>substance</strong> that makes it quantum. They are non-negotiable.</p>

<p>In quantum computing, the numbers $\\alpha$ and $\\beta$ in your state vector are not just any scalars; they are <strong>complex numbers</strong>. They are called <strong>probability amplitudes</strong>.</p>

<h3>1. The Imaginary Unit and Complex Number Definition</h3>
<p>A complex number $z$ is composed of a real part ($a$) and an imaginary part ($b$):</p>
$$z = a + bi$$
<p>where $i$ is the imaginary unit, defined such that $i^2 = -1$.</p>

<p>The crucial concept for QC is the <strong>phase</strong>. The complex number $z$ can be visualized on the complex plane (the Argand diagram), where its position defines both its <strong>magnitude</strong> (length from the origin) and its <strong>phase</strong> (the angle $\\phi$ it makes with the real axis). It is this phase that quantum gates manipulate to create interference.</p>

<h3>2. The Complex Conjugate ($z^*$)</h3>
<p>The <strong>complex conjugate</strong> $z^*$ is found by flipping the sign of the imaginary part:</p>
$$z^* = a - bi$$

<p>We need this conjugate for the Inner Product because the probability of measuring a state is the <strong>squared magnitude</strong> ($|z|^2$) of the amplitude $z$.</p>

$$P = |z|^2 = z^* z$$

<hr>

<h3>Your Task: Calculating Probability</h3>
<p>Suppose we have an amplitude $\\alpha$ for the $|0\\rangle$ state, defined as:</p>
$$\\alpha = \\frac{1}{\\sqrt{2}} + \\frac{i}{\\sqrt{2}}$$

<p>Calculate the probability $P$ of measuring the state $|0\\rangle$. Remember, $P = \\alpha^* \\alpha$.</p>
                    """,
                    "position": 6,
                    "task_json": None,
                    "section": "complex-numbers"
                },
                {
                    "slug": "complex-numbers-euler",
                    "title": "7. Complex Numbers: Euler's Formula",
                    "content": """
<h2>Euler's Formula</h2>
<p>This is arguably the most important equation in quantum mechanics:</p>
$$e^{i\\theta} = \cos(\\theta) + i\sin(\\theta)$$
<p>It tells us that an exponential with an imaginary exponent is actually a point on a circle in the complex plane.</p>
<p><strong>The Takeaway:</strong> This connects "growth" (exponentials) with "rotation" (trig). In quantum, gates are just rotations.</p>
                    """,
                    "position": 7,
                    "task_json": None,
                    "section": "complex-numbers"
                },
                {
                    "slug": "complex-numbers-phases",
                    "title": "8. Complex Numbers: Phases",
                    "content": """
<h2>Phases</h2>
<p>The "angle" of the complex number is called its <strong>Phase</strong>.</p>
<ul>
    <li><strong>Global Phase:</strong> If we rotate the entire quantum state, physics doesn't change. $|\\psi\\rangle$ and $-|\\psi\\rangle$ represent the same physical state.</li>
    <li><strong>Relative Phase:</strong> The difference in angle between two parts of a superposition ($|0\\rangle + |1\\rangle$ vs $|0\\rangle - |1\\rangle$). This changes everything!</li>
</ul>
<p><strong>The Takeaway:</strong> Relative phase is what creates interference patterns.</p>
                    """,
                    "position": 8,
                    "task_json": None,
                    "section": "complex-numbers"
                },
                {
                    "slug": "probability-theory-random-variables",
                    "title": "9. Probability Theory: Random Variables",
                    "content": """
<h2>Random Variables</h2>
<p>A <strong>Random Variable</strong> is a variable whose value depends on the outcome of a random phenomenon.</p>
<p>Example: Let $X$ be the result of rolling a die. $X$ can be 1, 2, 3, 4, 5, or 6.</p>
<p>In quantum computing, the result of a measurement is a random variable. You don't know what you'll get until you look.</p>
                    """,
                    "position": 9,
                    "task_json": None,
                    "section": "probability-theory"
                },
                {
                    "slug": "probability-theory-amplitudes",
                    "title": "10. Probability: Amplitudes vs. Probabilities",
                    "content": """
<h2>Amplitudes vs. Probabilities</h2>
<p>This is the single biggest difference between classical and quantum physics.</p>
<ul>
    <li><strong>Classical:</strong> Probabilities are always positive real numbers. To find the total probability, you ADD them.</li>
    <li><strong>Quantum:</strong> We work with <strong>Amplitudes</strong> (complex numbers). To find the probability, you SQUARE the amplitude ($P = |\\alpha|^2$).</li>
</ul>
<p><strong>The Magic:</strong> Because amplitudes can be negative (or complex), they can CANCEL each other out when added. This is interference.</p>
                    """,
                    "position": 10,
                    "task_json": None,
                    "section": "probability-theory"
                },
                {
                    "slug": "classical-logic-boolean",
                    "title": "11. Classical Logic: Boolean Algebra",
                    "content": """
<h2>Boolean Algebra</h2>
<p>George Boole proved that logic could be reduced to math.</p>
<ul>
    <li><strong>True</strong> = 1</li>
    <li><strong>False</strong> = 0</li>
</ul>
<p>In classical computers, everything is built from these 0s and 1s. In quantum, we extend this to vectors.</p>
                    """,
                    "position": 11,
                    "task_json": None,
                    "section": "classical-logic"
                },
                {
                    "slug": "classical-logic-gates",
                    "title": "12. Classical Logic: Logic Gates",
                    "content": """
<h2>Logic Gates (AND, OR, NOT)</h2>
<p>Complex decisions are built from simple gates.</p>
<ul>
    <li><strong>NOT:</strong> Flips 0 to 1 (like the Quantum X-gate).</li>
    <li><strong>AND:</strong> Returns 1 only if BOTH inputs are 1.</li>
    <li><strong>OR:</strong> Returns 1 if EITHER input is 1.</li>
</ul>
                    """,
                    "position": 12,
                    "task_json": None,
                    "section": "classical-logic"
                },
                {
                    "slug": "classical-logic-reversible",
                    "title": "13. Classical Logic: Reversible Computing",
                    "content": """
<h2>Reversible Computing</h2>
<p>A process is <strong>reversible</strong> if you can reconstruct the input from the output.</p>
<ul>
    <li><strong>Irreversible:</strong> An AND gate. If output is 0, was the input (0,0), (0,1), or (1,0)? Information is lost (dissipated as heat).</li>
    <li><strong>Reversible:</strong> A NOT gate. If output is 0, input was 1.</li>
</ul>
<p><strong>The Rule:</strong> Quantum evolution MUST be reversible (unitary). Information is never lost.</p>
                    """,
                    "position": 13,
                    "task_json": None,
                    "section": "classical-logic"
                }
            ]
        },
        {
            "slug": "stage-2-fundamentals",
            "title": "Stage 2: Quantum Fundamentals",
            "description": "Core mechanics: Postulates, The Qubit, Multi-Qubit Systems, and Gates.",
            "lessons": [
                {
                    "slug": "postulates-state-space",
                    "title": "1. Postulates: State Space",
                    "content": """
<h2>Postulate 1: State Space</h2>
<p>The first postulate of quantum mechanics tells us where everything happens.</p>
<ul>
    <li><strong>The Rule:</strong> The state of an isolated quantum system is described by a unit vector $|\psi\\rangle$ in a complex vector space with an inner product (a Hilbert Space).</li>
    <li><strong>Why it matters:</strong> This gives us the language. We aren't just listing properties; we are defining a single mathematical object that contains <em>all</em> the information about the system.</li>
</ul>
<p>The simplest quantum system is the Qubit, which lives in a 2-dimensional Hilbert space.</p>
                    """,
                    "position": 1,
                    "task_json": None,
                    "section": "postulates-of-quantum-mechanics"
                },
                {
                    "slug": "postulates-evolution",
                    "title": "2. Postulates: Evolution",
                    "content": """
<h2>Postulate 2: Evolution</h2>
<p>How does the state change over time?</p>
<ul>
    <li><strong>The Rule:</strong> The evolution of a closed quantum system is described by a <strong>Unitary Transformation</strong>.</li>
    <li><strong>The Equation:</strong> $|\psi'\\rangle = U|\psi\\rangle$</li>
</ul>
<p><strong>Key Property:</strong> Unitary matrices preserve the length of the vector (probability must sum to 1) and are reversible ($U^{-1} = U^{\dagger}$). This means quantum information is never lost.</p>
                    """,
                    "position": 2,
                    "task_json": None,
                    "section": "postulates-of-quantum-mechanics"
                },
                {
                    "slug": "postulates-measurement",
                    "title": "3. Postulates: Measurement",
                    "content": """
<h2>Postulate 3: Measurement</h2>
<p>This is where things get weird. When we look at the system, we change it.</p>
<ul>
    <li><strong>The Rule:</strong> Quantum measurements are described by a collection of measurement operators $\{M_m\}$. The probability of outcome $m$ is $P(m) = \langle \psi | M_m^{\dagger} M_m | \psi \rangle$.</li>
    <li><strong>Collapse:</strong> Immediately after measurement, the state of the system collapses to the outcome state.</li>
</ul>
<p><strong>The Takeaway:</strong> Measurement is irreversible. Once you look, you destroy the superposition.</p>
                    """,
                    "position": 3,
                    "task_json": None,
                    "section": "postulates-of-quantum-mechanics"
                },
                {
                    "slug": "the-qubit-superposition",
                    "title": "4. The Qubit: Superposition",
                    "content": """
<h2>Superposition</h2>
<p>Let's upgrade our analogy.</p>
<ul>
    <li><strong>Classical Bit:</strong> A coin flat on the table. It is definitely <strong>Heads</strong> OR <strong>Tails</strong>.</li>
    <li><strong>Qubit:</strong> A coin <em>spinning</em> on the table. Is it Heads or Tails? It’s <strong>both and neither</strong> at the same time.</li>
</ul>
<p>This state is called <strong>Superposition</strong>. The coin keeps spinning until you slap your hand down on it—this is <strong>measurement</strong>. Only then does it force itself to be Heads or Tails.</p>
<p><strong>Interactive Task:</strong> Drag an <strong>H</strong> (Hadamard) gate to the circuit and run it. You'll see a 50/50 chance of measuring 0 or 1. Look at the <strong>Bloch Sphere</strong> below the results—the arrow points to the equator, representing the superposition state!</p>
                    """,
                    "position": 4,
                    "task_json": json.dumps({
                        "description": "Create a Superposition State (50% chance of 0 or 1)",
                        "criteria": "superposition",
                        "qubits": 1
                    }),
                    "section": "the-qubit"
                },
                {
                    "slug": "the-qubit-bloch-sphere",
                    "title": "5. The Qubit: The Bloch Sphere",
                    "content": """
<h2>The Bloch Sphere</h2>
<p>Since a qubit $|\psi\\rangle = \alpha|0\\rangle + \beta|1\\rangle$ has complex coefficients, we can't just draw it on a 2D graph.</p>
<p>However, ignoring the global phase, we can map the state of a single qubit to a point on the surface of a sphere called the <strong>Bloch Sphere</strong>.</p>
<ul>
    <li><strong>North Pole:</strong> $|0\\rangle$</li>
    <li><strong>South Pole:</strong> $|1\\rangle$</li>
    <li><strong>Equator:</strong> Superposition states (like $|+\\rangle = \\frac{|0\\rangle + |1\\rangle}{\sqrt{2}}$).</li>
</ul>
<p><strong>The Takeaway:</strong> Quantum Gates are just rotations of this sphere.</p>
                    """,
                    "position": 5,
                    "task_json": None,
                    "section": "the-qubit"
                },
                {
                    "slug": "multi-qubit-tensor-products",
                    "title": "6. Multi-Qubit: Tensor Products",
                    "content": """
<h2>Tensor Products</h2>
<p>How do we describe two qubits? We multiply their vector spaces using the <strong>Tensor Product</strong> ($\otimes$).</p>
<p>If qubit A is in state $|0\\rangle$ and qubit B is in state $|1\\rangle$, the combined state is:</p>
$$|0\\rangle \otimes |1\\rangle = |01\\rangle$$
<p>If we have two 2D vectors, their tensor product is a 4D vector. For $n$ qubits, the state space is $2^n$. This exponential growth is why quantum computers are hard to simulate.</p>
                    """,
                    "position": 6,
                    "task_json": None,
                    "section": "multi-qubit-systems"
                },
                {
                    "slug": "multi-qubit-entanglement",
                    "title": "7. Multi-Qubit: Entanglement",
                    "content": """
<h2>Entanglement</h2>
<p>Entanglement occurs when a multi-qubit state <strong>cannot</strong> be written as a tensor product of individual qubit states.</p>
<p>Imagine you have two dice. You throw one in New York and one in Tokyo. If they are <strong>entangled</strong>, every time the New York die lands on 6, the Tokyo die <em>instantly</em> lands on 6.</p>
<p><strong>Interactive Task:</strong> Create a Bell Pair. Use an <strong>H</strong> gate on q0, then a <strong>CNOT</strong> gate (control q0, target q1). Measure both. They will always match!</p>
                    """,
                    "position": 7,
                    "task_json": json.dumps({
                        "description": "Create a Bell Pair (|00> and |11> only)",
                        "criteria": "bell_pair",
                        "qubits": 2
                    }),
                    "section": "multi-qubit-systems"
                },
                {
                    "slug": "multi-qubit-bell-states",
                    "title": "8. Multi-Qubit: The Bell States",
                    "content": """
<h2>The Bell States</h2>
<p>The four maximally entangled states for two qubits are known as the Bell States:</p>
<ul>
    <li>$|\Phi^+\\rangle = \\frac{|00\\rangle + |11\\rangle}{\sqrt{2}}$ (The one you just made)</li>
    <li>$|\Phi^-\\rangle = \\frac{|00\\rangle - |11\\rangle}{\sqrt{2}}$</li>
    <li>$|\Psi^+\\rangle = \\frac{|01\\rangle + |10\\rangle}{\sqrt{2}}$</li>
    <li>$|\Psi^-\\rangle = \\frac{|01\\rangle - |10\\rangle}{\sqrt{2}}$</li>
</ul>
<p>These form a basis for the two-qubit Hilbert space, known as the <strong>Bell Basis</strong>.</p>
                    """,
                    "position": 8,
                    "task_json": None,
                    "section": "multi-qubit-systems"
                },
                {
                    "slug": "quantum-gates-pauli",
                    "title": "9. Gates: Pauli Matrices",
                    "content": """
<h2>Pauli Matrices (X, Y, Z)</h2>
<p>The single-qubit gates are rotations. The most fundamental ones are the Pauli matrices:</p>
<ul>
    <li><strong>X (Bit Flip):</strong> Swaps $|0\\rangle$ and $|1\\rangle$. (Rotation around X-axis)</li>
    <li><strong>Y (Bit & Phase Flip):</strong> Swaps $|0\\rangle$ and $|1\\rangle$ and adds a phase. (Rotation around Y-axis)</li>
    <li><strong>Z (Phase Flip):</strong> Leaves $|0\\rangle$ alone but flips the sign of $|1\\rangle$. (Rotation around Z-axis)</li>
</ul>
                    """,
                    "position": 9,
                    "task_json": None,
                    "section": "quantum-gates"
                },
                {
                    "slug": "quantum-gates-hadamard",
                    "title": "10. Gates: Hadamard",
                    "content": """
<h2>The Hadamard Gate (H)</h2>
<p>The Superposition Creator.</p>
<p>It maps the basis states to superpositions:</p>
<ul>
    <li>$H|0\\rangle = |+\\rangle = \\frac{|0\\rangle + |1\\rangle}{\sqrt{2}}$</li>
    <li>$H|1\\rangle = |-\\rangle = \\frac{|0\\rangle - |1\\rangle}{\sqrt{2}}$</li>
</ul>
<p>Applying H twice gets you back to where you started ($H^2 = I$).</p>
                    """,
                    "position": 10,
                    "task_json": None,
                    "section": "quantum-gates"
                },
                {
                    "slug": "quantum-gates-cnot",
                    "title": "11. Gates: CNOT",
                    "content": """
<h2>Controlled-NOT (CNOT)</h2>
<p>The Entanglement Creator.</p>
<p>This is a two-qubit gate. It flips the <strong>Target</strong> qubit if and only if the <strong>Control</strong> qubit is $|1\\rangle$.</p>
<p>If the control qubit is in superposition ($|0\\rangle + |1\\rangle$), the target becomes entangled with it, creating the state $|00\\rangle + |11\\rangle$.</p>
                    """,
                    "position": 11,
                    "task_json": None,
                    "section": "quantum-gates"
                },
                {
                    "slug": "quantum-gates-phase",
                    "title": "12. Gates: Phase Gates",
                    "content": """
<h2>Phase Gates (S, T)</h2>
<p>Sometimes we need finer control than a full Z-flip (180 degrees).</p>
<ul>
    <li><strong>S Gate:</strong> 90-degree rotation around Z axis ($\sqrt{Z}$).</li>
    <li><strong>T Gate:</strong> 45-degree rotation around Z axis ($\sqrt[4]{Z}$).</li>
</ul>
<p>The T gate is crucial because H, S, and CNOT are not enough to build <em>any</em> quantum circuit. Adding the T gate makes the set "Universal".</p>
                    """,
                    "position": 12,
                    "task_json": None,
                    "section": "quantum-gates"
                }
            ]
        },
        {
            "slug": "stage-3-circuits-algorithms",
            "title": "Stage 3: Quantum Circuits & Algorithms",
            "description": "How we actually manipulate information: The Circuit Model, Parallelism, and Algorithms.",
            "lessons": [
                {
                    "slug": "circuit-model-reading",
                    "title": "1. The Circuit Model: Reading Scores",
                    "content": """
<h2>The Circuit Model</h2>
<p>Quantum computing has a standard notation called the <strong>Circuit Model</strong>.</p>
<p>Look at the simulator below. It looks like a musical score, right?</p>
<ul>
    <li><strong>Time:</strong> Moves from left to right.</li>
    <li><strong>Qubits:</strong> Horizontal lines (like strings on a guitar).</li>
    <li><strong>Gates:</strong> Boxes or symbols placed on the lines. These are operations happening at specific times.</li>
</ul>
<p><strong>The Takeaway:</strong> We compose quantum algorithms like music, sequencing operations in time to manipulate the state of the qubits.</p>
                    """,
                    "position": 1,
                    "task_json": None,
                    "section": "circuit-model"
                },
                {
                    "slug": "quantum-parallelism-deutsch-jozsa",
                    "title": "2. Parallelism: Deutsch-Jozsa",
                    "content": """
<h2>The Deutsch-Jozsa Algorithm</h2>
<p>This was the first "proof of concept" that a quantum computer could do something faster than a classical one.</p>
<p><strong>The Problem:</strong> You have a black box function $f(x)$ that takes a bit string input and outputs 0 or 1. The function is guaranteed to be either:</p>
<ul>
    <li><strong>Constant:</strong> Always outputs 0 or always outputs 1.</li>
    <li><strong>Balanced:</strong> Outputs 0 for half the inputs and 1 for the other half.</li>
</ul>
<p><strong>The Solution:</strong>
<ul>
    <li><strong>Classical:</strong> You might need to check $2^{n-1} + 1$ inputs to be sure.</li>
    <li><strong>Quantum:</strong> You can determine the answer with exactly <strong>ONE</strong> query.</li>
</ul>
<p>It works by creating a superposition of all possible inputs, querying the function once, and using interference to separate the "constant" case from the "balanced" case.</p>
                    """,
                    "position": 2,
                    "task_json": None,
                    "section": "quantum-parallelism"
                },
                {
                    "slug": "amplitude-amplification-grover",
                    "title": "3. Amplification: Grover’s Algorithm",
                    "content": """
<h2>Grover’s Algorithm</h2>
<p>Imagine you have a phone book with $N$ names, but it's not alphabetized. You want to find a specific number.</p>
<ul>
    <li><strong>Classical Search:</strong> You have to look through them one by one. On average, you check $N/2$ entries.</li>
    <li><strong>Quantum Search:</strong> Grover's Algorithm can find it in roughly $\sqrt{N}$ steps.</li>
</ul>
<p>If $N = 1,000,000$, a classical computer checks 500,000 times. A quantum computer checks 1,000 times.</p>
<p><strong>How it works:</strong> It uses a process called <strong>Amplitude Amplification</strong>. It repeatedly rotates the state vector towards the correct answer, increasing its probability while decreasing the probability of wrong answers.</p>
                    """,
                    "position": 3,
                    "task_json": None,
                    "section": "amplitude-amplification"
                },
                {
                    "slug": "qft-phase-estimation",
                    "title": "4. QFT: Phase Estimation",
                    "content": """
<h2>Quantum Phase Estimation (QPE)</h2>
<p>Many quantum algorithms rely on finding the <strong>eigenvalue</strong> of a unitary operator. If $U|\psi\\rangle = e^{i\theta}|\psi\\rangle$, we want to estimate $\theta$.</p>
<p>The <strong>Quantum Fourier Transform (QFT)</strong> is the key. Just as a classical Fourier Transform extracts frequencies from a sound wave, the QFT extracts periodicity from quantum amplitudes.</p>
<p>QPE is the engine under the hood of most advanced quantum algorithms, including Shor's Algorithm and Quantum Chemistry simulations.</p>
                    """,
                    "position": 4,
                    "task_json": None,
                    "section": "quantum-fourier-transform"
                },
                {
                    "slug": "qft-shors",
                    "title": "5. QFT: Shor’s Algorithm",
                    "content": """
<h2>Shor’s Algorithm</h2>
<p>Why is there so much hype (and fear) around quantum computing?</p>
<p>Most internet security (like HTTPS/RSA) relies on the fact that factoring very large numbers is hard.</p>
<p><strong>The Threat:</strong> Peter Shor discovered that by using Phase Estimation (and thus the QFT), a quantum computer could turn this "hard" math problem into an easy one.</p>
<p><strong>The Impact:</strong> A powerful enough quantum computer could crack current encryption in hours, not millions of years. This is why the world is racing to build one.</p>
                    """,
                    "position": 5,
                    "task_json": None,
                    "section": "quantum-fourier-transform"
                }
            ]
        },
        {
            "slug": "stage-4-advanced",
            "title": "Stage 4: Advanced Theory & Hardware (Expert Level)",
            "description": "Where reality meets theory.",
            "lessons": [
                {
                    "slug": "qec-decoherence",
                    "title": "1. QEC: Decoherence",
                    "content": """
<h2>Decoherence: The Enemy</h2>
<p>Quantum states are fragile. Interaction with the environment (heat, radiation, magnetic fields) causes the quantum information to leak out.</p>
<p>This process is called <strong>Decoherence</strong>.</p>
<ul>
    <li><strong>T1 (Relaxation):</strong> The time it takes for $|1\\rangle$ to decay to $|0\\rangle$.</li>
    <li><strong>T2 (Dephasing):</strong> The time it takes for the relative phase ($\alpha|0\\rangle + \beta|1\\rangle$) to scramble.</li>
</ul>
<p>Without error correction, decoherence limits the depth of our circuits.</p>
                    """,
                    "position": 1,
                    "task_json": None,
                    "section": "quantum-error-correction"
                },
                {
                    "slug": "qec-surface-codes",
                    "title": "2. QEC: Surface Codes",
                    "content": """
<h2>Surface Codes & Fault Tolerance</h2>
<p>How do we build a reliable computer from unreliable parts?</p>
<p><strong>Quantum Error Correction (QEC):</strong> We spread the information of 1 <strong>Logical Qubit</strong> across many noisy <strong>Physical Qubits</strong>.</p>
<p><strong>The Surface Code:</strong> The leading candidate for QEC. It uses a checkerboard pattern of data and measurement qubits to detect and correct errors without collapsing the state.</p>
<p><strong>Threshold Theorem:</strong> If the physical error rate is below a certain threshold (~1%), we can make the logical error rate arbitrarily low by adding more physical qubits.</p>
                    """,
                    "position": 2,
                    "task_json": None,
                    "section": "quantum-error-correction"
                },
                {
                    "slug": "complexity-bqp",
                    "title": "3. Complexity: BQP vs P vs NP",
                    "content": """
<h2>Quantum Complexity Theory</h2>
<p>Where does quantum computing fit in the landscape of solvable problems?</p>
<ul>
    <li><strong>P (Polynomial):</strong> Problems solvable quickly by a classical computer (Multiplication).</li>
    <li><strong>NP (Nondeterministic Polynomial):</strong> Problems where a solution can be <em>verified</em> quickly (Sudoku, Traveling Salesman).</li>
    <li><strong>BQP (Bounded-error Quantum Polynomial):</strong> Problems solvable quickly by a quantum computer.</li>
</ul>
<p><strong>The Reality:</strong> $P \subseteq BQP$. Quantum computers can solve everything classical computers can. But can they solve NP-Complete problems? <strong>Probably not.</strong></p>
<p>They excel at specific "hidden structure" problems (like Factoring) that are likely in <strong>NP-Intermediate</strong>.</p>
                    """,
                    "position": 3,
                    "task_json": None,
                    "section": "quantum-complexity-theory"
                },
                {
                    "slug": "hardware-superconducting",
                    "title": "4. Hardware: Superconducting",
                    "content": """
<h2>Superconducting Qubits (Transmons)</h2>
<p><strong>The Players:</strong> IBM, Google, Rigetti.</p>
<p><strong>The Tech:</strong> Artificial atoms made from superconducting circuits (Josephson Junctions) cooled to near absolute zero.</p>
<ul>
    <li><strong>Pros:</strong> Very fast gate speeds (nanoseconds). Standard microchip fabrication.</li>
    <li><strong>Cons:</strong> Short coherence times (microseconds). Wiring complexity grows with size. Needs massive dilution refrigerators.</li>
</ul>
                    """,
                    "position": 4,
                    "task_json": None,
                    "section": "physical-implementations"
                },
                {
                    "slug": "hardware-ions-photonics",
                    "title": "5. Hardware: Ions & Photonics",
                    "content": """
<h2>Trapped Ions & Photonics</h2>
<p><strong>Trapped Ions (IonQ, Quantinuum):</strong>
<ul>
    <li><strong>Tech:</strong> Individual atoms levitated by electric fields.</li>
    <li><strong>Pros:</strong> Perfect qubits (nature makes them identical). Long coherence (seconds/minutes). High connectivity.</li>
    <li><strong>Cons:</strong> Slow gates. Hard to scale trap size.</li>
</ul></p>
<p><strong>Photonics (PsiQuantum, Xanadu):</strong>
<ul>
    <li><strong>Tech:</strong> Encoding information in particles of light.</li>
    <li><strong>Pros:</strong> Works at room temperature (mostly). Integration with fiber optics.</li>
    <li><strong>Cons:</strong> Photons don't like to interact (hard to do 2-qubit gates). Loss is a major issue.</li>
</ul></p>
                    """,
                    "position": 5,
                    "task_json": None,
                    "section": "physical-implementations"
                },
                {
                    "slug": "qml-vqe",
                    "title": "6. QML: VQE",
                    "content": """
<h2>Variational Quantum Eigensolvers (VQE)</h2>
<p>How do we use today's noisy quantum computers (NISQ) for useful work?</p>
<p><strong>VQE</strong> is a hybrid algorithm. It uses a classical computer to optimize the parameters of a quantum circuit to find the ground state energy of a molecule.</p>
<p><strong>Application:</strong> Drug discovery and Material science. Simulating molecular bonds is one of the "killer apps" for near-term quantum.</p>
                    """,
                    "position": 6,
                    "task_json": None,
                    "section": "quantum-machine-learning"
                },
                {
                    "slug": "qml-qaoa",
                    "title": "7. QML: QAOA",
                    "content": """
<h2>Quantum Approximate Optimization (QAOA)</h2>
<p><strong>QAOA</strong> is another hybrid algorithm designed for combinatorial optimization problems.</p>
<p><strong>Example:</strong> The MaxCut problem (partitioning a graph). QAOA tries to find a "good enough" solution faster than classical brute force.</p>
<p>It is a leading candidate for demonstrating "Quantum Advantage" in practical industry problems like logistics and finance.</p>
                    """,
                    "position": 7,
                    "task_json": None,
                    "section": "quantum-machine-learning"
                }
            ]
        }
    ]

    for course_data in courses_data:
        course_slug = course_data["slug"]
        course_title = course_data["title"]
        description = course_data["description"]
        
        if db_type == "postgres":
            cur.execute(
                "INSERT INTO courses(slug, title, description) VALUES(%s, %s, %s) "
                "ON CONFLICT (slug) DO UPDATE SET title=EXCLUDED.title, description=EXCLUDED.description "
                "RETURNING id",
                (course_slug, course_title, description)
            )
            course_row = cur.fetchone()
            course_id = _row_get(course_row, 'id', 0)
            if course_id is None:
                cur.execute("SELECT id FROM courses WHERE slug=%s", (course_slug,))
                course_row = cur.fetchone()
                course_id = _row_get(course_row, 'id', 0)
        else:
            # Check if course exists first to update or insert
            # Actually simple INSERT OR REPLACE logic or checking ID
            cur.execute("SELECT id FROM courses WHERE slug=?", (course_slug,))
            row = cur.fetchone()
            if row:
                course_id = row[0]
                cur.execute("UPDATE courses SET title=?, description=? WHERE id=?", (course_title, description, course_id))
            else:
                cur.execute("INSERT INTO courses(slug, title, description) VALUES(?, ?, ?)", (course_slug, course_title, description))
                course_id = cur.lastrowid
        
        print(f"Seeded Course: {course_title} (ID: {course_id})")

        for l in course_data["lessons"]:
            section = l.get("section")
            if db_type == "postgres":
                cur.execute(
                    "INSERT INTO lessons(course_id, slug, title, content, position, task_json, section) VALUES(%s, %s, %s, %s, %s, %s, %s) "
                    "ON CONFLICT (course_id, slug) DO UPDATE SET title=EXCLUDED.title, content=EXCLUDED.content, position=EXCLUDED.position, task_json=EXCLUDED.task_json, section=EXCLUDED.section",
                    (course_id, l["slug"], l["title"], l["content"], l["position"], l["task_json"], section))
            else:
                cur.execute("SELECT id FROM lessons WHERE course_id=? AND slug=?", (course_id, l["slug"]))
                l_row = cur.fetchone()
                if l_row:
                    cur.execute("UPDATE lessons SET title=?, content=?, position=?, task_json=?, section=? WHERE id=?", 
                                (l["title"], l["content"], l["position"], l["task_json"], section, l_row[0]))
                else:
                    cur.execute("INSERT INTO lessons(course_id, slug, title, content, position, task_json, section) VALUES(?, ?, ?, ?, ?, ?, ?)",
                                (course_id, l["slug"], l["title"], l["content"], l["position"], l["task_json"], section))
    
    # 3. Add a sample Quiz for "Linear Algebra"
    print("Seeding Quizzes...")
    # Find lesson id
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("linear-algebra-vectors",))
        lesson_row = cur.fetchone()
        lesson_id = _row_get(lesson_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("linear-algebra-vectors",))
        lesson_row = cur.fetchone()
        lesson_id = _row_get(lesson_row, 'id', 0)
        
    if lesson_id:
        quiz_title = "Linear Algebra Check"
        question_text = "Using the column definitions for |0> and |1> above, if you perform the matrix addition and scalar multiplication for α|0> + β|1>, what does the single resulting column vector look like?"
        # Options: [α, β], [α + β, 0], [0, α + β], [1, 1]
        # Correct is [α, β] which is index 0.
        options = json.dumps(["[α, β]", "[α + β, 0]", "[0, α + β]", "[1, 1]"])
        correct_idx = 0
        
        if db_type == "postgres":
            cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (lesson_id, quiz_title))
            quiz_row = cur.fetchone()
            quiz_id = _row_get(quiz_row, 'id', 0)
            
            cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)", 
                (quiz_id, question_text, options, correct_idx))
        else:
            cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (lesson_id, quiz_title))
            quiz_id = cur.lastrowid
            
            cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)", 
                (quiz_id, question_text, options, correct_idx))

    # 4. Add a sample Quiz for "Linear Algebra: Matrices"
    # Find lesson id
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("linear-algebra-matrices",))
        lesson_row = cur.fetchone()
        lesson_id = _row_get(lesson_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("linear-algebra-matrices",))
        lesson_row = cur.fetchone()
        lesson_id = _row_get(lesson_row, 'id', 0)
        
    if lesson_id:
        quiz_title = "Matrix Operation Check"
        question_text = "Calculate the resulting state |ψ'> when applying X to |ψ> = 1/√2 * [1, 1]^T. What is the final column vector?"
        # Options: 
        # 1. 1/√2 * [1, 1] (Correct)
        # 2. 1/√2 * [1, -1]
        # 3. [0, 0]
        # 4. [1, 0]
        options = json.dumps(["1/√2 * [1, 1]", "1/√2 * [1, -1]", "[0, 0]", "[1, 0]"])
        correct_idx = 0
        
        if db_type == "postgres":
            cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (lesson_id, quiz_title))
            quiz_row = cur.fetchone()
            quiz_id = _row_get(quiz_row, 'id', 0)
            
            cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)", 
                (quiz_id, question_text, options, correct_idx))
        else:
            cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (lesson_id, quiz_title))
            quiz_id = cur.lastrowid
            
            cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)", 
                (quiz_id, question_text, options, correct_idx))

    # 5. Add a sample Quiz for "Linear Algebra: Eigenvalues"
    # Find lesson id
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("linear-algebra-eigenvalues",))
        lesson_row = cur.fetchone()
        lesson_id = _row_get(lesson_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("linear-algebra-eigenvalues",))
        lesson_row = cur.fetchone()
        lesson_id = _row_get(lesson_row, 'id', 0)
        
    if lesson_id:
        quiz_title = "Eigenvalue Check"
        question_text = "When applying the Pauli-Z gate to the state |1>, what is the resulting eigenvalue?"
        # Options: 
        # 1. 1
        # 2. -1 (Correct)
        # 3. 0
        # 4. i
        options = json.dumps(["1", "-1", "0", "i"])
        correct_idx = 1
        
        if db_type == "postgres":
            cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (lesson_id, quiz_title))
            quiz_row = cur.fetchone()
            quiz_id = _row_get(quiz_row, 'id', 0)
            
            cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)", 
                (quiz_id, question_text, options, correct_idx))
        else:
            cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (lesson_id, quiz_title))
            quiz_id = cur.lastrowid
            
            cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)", 
                (quiz_id, question_text, options, correct_idx))

    # 6. Add a sample Quiz for "Linear Algebra: Inner Products"
    # Find lesson id
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("linear-algebra-inner-products",))
        lesson_row = cur.fetchone()
        lesson_id = _row_get(lesson_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("linear-algebra-inner-products",))
        lesson_row = cur.fetchone()
        lesson_id = _row_get(lesson_row, 'id', 0)
        
    if lesson_id:
        quiz_title = "Probability Check"
        question_text = "What is the probability P of measuring the state |+> = 1/√2(|0> + |1>) as |0>?"
        # Options: 
        # 1. 1 (100%)
        # 2. 0.5 (50%) (Correct)
        # 3. 0 (0%)
        # 4. 0.707 (70.7%)
        options = json.dumps(["1 (100%)", "0.5 (50%)", "0 (0%)", "0.707 (70.7%)"])
        correct_idx = 1
        
        if db_type == "postgres":
            cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (lesson_id, quiz_title))
            quiz_row = cur.fetchone()
            quiz_id = _row_get(quiz_row, 'id', 0)
            
            cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)", 
                (quiz_id, question_text, options, correct_idx))
        else:
            cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (lesson_id, quiz_title))
            quiz_id = cur.lastrowid
            
            cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)", 
                (quiz_id, question_text, options, correct_idx))

    # 7. Add a sample Quiz for "Linear Algebra: Hilbert Spaces"
    # Find lesson id
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("linear-algebra-hilbert-spaces",))
        lesson_row = cur.fetchone()
        lesson_id = _row_get(lesson_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("linear-algebra-hilbert-spaces",))
        lesson_row = cur.fetchone()
        lesson_id = _row_get(lesson_row, 'id', 0)
        
    if lesson_id:
        quiz_title = "Hilbert Space Dimension"
        question_text = "What is the dimension of the Hilbert space needed to fully describe the state of a system composed of 2 qubits?"
        # Options: 
        # 1. 2
        # 2. 4 (Correct)
        # 3. 8
        # 4. 16
        options = json.dumps(["2", "4", "8", "16"])
        correct_idx = 1
        
        if db_type == "postgres":
            cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (lesson_id, quiz_title))
            quiz_row = cur.fetchone()
            quiz_id = _row_get(quiz_row, 'id', 0)
            
            cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)", 
                (quiz_id, question_text, options, correct_idx))
        else:
            cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (lesson_id, quiz_title))
            quiz_id = cur.lastrowid
            
            cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)", 
                (quiz_id, question_text, options, correct_idx))

    # 8. Add a sample Quiz for "Complex Numbers: Arithmetic"
    # Find lesson id
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("complex-numbers-arithmetic",))
        lesson_row = cur.fetchone()
        lesson_id = _row_get(lesson_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("complex-numbers-arithmetic",))
        lesson_row = cur.fetchone()
        lesson_id = _row_get(lesson_row, 'id', 0)
        
    if lesson_id:
        quiz_title = "Probability from Amplitude"
        question_text = "Calculate the probability P of measuring |0> given the amplitude α = 1/√2 + i/√2."
        # Options: 
        # 1. 0.5 (50%)
        # 2. 1 (100%) (Correct)
        # 3. 0 (0%)
        # 4. i
        options = json.dumps(["0.5 (50%)", "1 (100%)", "0 (0%)", "i"])
        correct_idx = 1
        
        if db_type == "postgres":
            cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (lesson_id, quiz_title))
            quiz_row = cur.fetchone()
            quiz_id = _row_get(quiz_row, 'id', 0)
            
            cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)", 
                (quiz_id, question_text, options, correct_idx))
        else:
            cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (lesson_id, quiz_title))
            quiz_id = cur.lastrowid
            
            cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)", 
                (quiz_id, question_text, options, correct_idx))

    conn.commit()
    conn.close()
    print("Database seeded successfully!")

if __name__ == "__main__":
    seed()
