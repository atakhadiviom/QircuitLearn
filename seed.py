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
        db_exists = os.path.exists(db_path)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        if not db_exists:
            print("Creating new database...")
            with open("schema_sqlite.sql", "r") as f:
                conn.executescript(f.read())
        else:
            print("Updating existing database...")
    
    # MIGRATION CHECK: Ensure answers_json column exists in user_quiz_attempts
    print("Checking for necessary migrations...")
    if db_type == "postgres":
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='user_quiz_attempts' AND column_name='answers_json'")
        if not cur.fetchone():
            print("Adding answers_json column to user_quiz_attempts...")
            cur.execute("ALTER TABLE user_quiz_attempts ADD COLUMN answers_json TEXT")
        conn.commit()
    else:
        # SQLite
        cur.execute("PRAGMA table_info(user_quiz_attempts)")
        columns = [row['name'] for row in cur.fetchall()]
        if 'answers_json' not in columns:
            print("Adding answers_json column to user_quiz_attempts...")
            cur.execute("ALTER TABLE user_quiz_attempts ADD COLUMN answers_json TEXT")
            conn.commit()

    # MIGRATION: Add slug, meta_title, meta_description to forum_posts
    try:
        if db_type == "postgres":
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='forum_posts'")
            fp_cols = {row[0] for row in cur.fetchall()}
            if 'slug' not in fp_cols:
                print("Adding slug column to forum_posts...")
                cur.execute("ALTER TABLE forum_posts ADD COLUMN slug VARCHAR(255) UNIQUE")
                conn.commit()
            if 'meta_title' not in fp_cols:
                print("Adding meta_title column to forum_posts...")
                cur.execute("ALTER TABLE forum_posts ADD COLUMN meta_title VARCHAR(255)")
                conn.commit()
            if 'meta_description' not in fp_cols:
                print("Adding meta_description column to forum_posts...")
                cur.execute("ALTER TABLE forum_posts ADD COLUMN meta_description TEXT")
                conn.commit()
        else:
            cur.execute("PRAGMA table_info(forum_posts)")
            fp_cols = [row['name'] for row in cur.fetchall()]
            if 'slug' not in fp_cols:
                print("Adding slug column to forum_posts...")
                cur.execute("ALTER TABLE forum_posts ADD COLUMN slug TEXT")
                conn.commit()
                try:
                    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_forum_posts_slug ON forum_posts(slug)")
                    conn.commit()
                except Exception:
                    pass
            if 'meta_title' not in fp_cols:
                print("Adding meta_title column to forum_posts...")
                cur.execute("ALTER TABLE forum_posts ADD COLUMN meta_title TEXT")
                conn.commit()
            if 'meta_description' not in fp_cols:
                print("Adding meta_description column to forum_posts...")
                cur.execute("ALTER TABLE forum_posts ADD COLUMN meta_description TEXT")
                conn.commit()
    except Exception as e:
        print(f"Forum posts migration error: {e}")

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
        cur.execute("SELECT id FROM users WHERE username=%s", (admin_user,))
        user_row = cur.fetchone()
        if not user_row:
            cur.execute(
                "INSERT INTO users(username, email, password_hash, is_superuser) VALUES(%s, %s, %s, %s)",
                (admin_user, admin_email, pwd_hash, True)
            )
    else:
        cur.execute("SELECT id FROM users WHERE username=?", (admin_user,))
        user_row = cur.fetchone()
        if not user_row:
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
                    """,
                    "position": 1,
                    "task_json": json.dumps({
                        "description": "Use the X gate to transform the qubit from state |0> to state |1>.",
                        "criteria": "state_one",
                        "qubits": 1
                    }),
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
                    "task_json": json.dumps({
                        "description": "Create a superposition using the H gate, then apply the X gate to see that the state remains unchanged.",
                        "criteria": "h_then_x",
                        "qubits": 1
                    }),
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
                    "task_json": json.dumps({
                        "description": "Prepare the |1> state and apply a Z gate to see the phase flip (eigenvalue -1).",
                        "criteria": "eigenvalue_z_1",
                        "qubits": 1
                    }),
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
<p>You’ve grasped the core of probability with the Inner Product. Now, you need Euler's Formula because it is the fundamental engine of quantum operations. It connects the arithmetic of complex numbers to the geometry of rotation, which is how we manipulate a qubit.</p>

<h3>1. The Formula</h3>
<p>Euler's formula provides a compact way to represent any complex number $z$ that lies on the unit circle (a complex number with a magnitude of 1, like your probability amplitudes):</p>
$$e^{i\\theta} = \cos(\\theta) + i \sin(\\theta)$$
<p>Here, $e$ is Euler's number (the base of the natural logarithm), $i$ is the imaginary unit, and $\\theta$ (theta) is the phase angle in radians.</p>

<h3>2. ⚛️ QC Interpretation: The Phase Factor</h3>
<p>In quantum computing, this complex exponential $e^{i\\theta}$ is called a Phase Factor.</p>
<ul>
    <li><strong>Magnitude is 1:</strong> Because $\cos^2(\\theta) + \sin^2(\\theta) = 1$, the length (magnitude) of $e^{i\\theta}$ is always 1. When you multiply a state vector by $e^{i\\theta}$, you rotate it without changing its length, meaning probability is conserved.</li>
    <li><strong>Rotation:</strong> Multiplying a complex number $z$ by $e^{i\\theta}$ rotates $z$ by an angle $\\theta$ on the complex plane. This is how all single-qubit gates work—they are just rotations.</li>
    <li><strong>The Power of Interference:</strong> The phase $\\theta$ is the physical degree of freedom we exploit for quantum interference. By applying phase gates (like the $R_z$ gate), we introduce a specific $\\theta$ to the $|1\\rangle$ component of a superposition, which is necessary for algorithms like the Quantum Fourier Transform.</li>
</ul>
                    """,
                    "position": 7,
                    "task_json": json.dumps({
                        "description": "Create the |- state by applying H then Z.",
                        "criteria": "minus_state",
                        "qubits": 1
                    }),
                    "section": "complex-numbers"
                },
                {
                    "slug": "complex-numbers-phases",
                    "title": "8. Complex Numbers: Phases",
                    "content": """
<h2>Phases</h2>
<p>You are drilled on the math, but here is where students often get tricked. In Quantum Computing, not all phases are created equal. You must distinguish between <strong>Global Phase</strong> and <strong>Relative Phase</strong>. One matters immensely; the other is mathematically real but physically meaningless.</p>

<h3>1. Global Phase (The Ghost)</h3>
<p>If we multiply the <em>entire</em> state vector $|\psi\\rangle$ by a phase factor $e^{i\\gamma}$, we get a new state $|\psi'\\rangle = e^{i\\gamma}|\psi\\rangle$.</p>
$$|\psi'\\rangle = e^{i\\gamma}(\\alpha|0\\rangle + \\beta|1\\rangle) = (e^{i\\gamma}\\alpha)|0\\rangle + (e^{i\\gamma}\\beta)|1\\rangle$$
<p>Here is the brutal truth: <strong>Global phase has zero physical effect.</strong> You cannot measure it. It does not change the statistics of measurement outcomes. To the observer, $|\psi\\rangle$ and $-|\psi\\rangle$ (where $\\gamma = \\pi$) are identical states.</p>

<h3>2. Relative Phase (The Engine)</h3>
<p>Relative phase is the difference in phase <em>between</em> the coefficients $\\alpha$ and $\\beta$. This is the parameter $\\phi$ on the Bloch Sphere.</p>

<div style="text-align: center; margin: 20px;">
    <img src="/static/images/bloch-sphere.png" alt="Bloch Sphere showing relative phase phi" style="max-width: 300px; border-radius: 8px;">
    <p><em>The angle $\\phi$ around the Z-axis is the Relative Phase.</em></p>
</div>

<p>We can rewrite the state vector to isolate this relative phase:</p>
$$|\\psi\\rangle = \\cos(\\frac{\\theta}{2})|0\\rangle + e^{i\\phi}\\sin(\\frac{\\theta}{2})|1\\rangle$$
<p>(Note: We often ignore the global phase on $\\alpha$ by convention).</p>
<p>When you change $\\phi$ (the <strong>Relative Phase</strong>), you rotate the state vector around the Z-axis of the Bloch sphere. This changes the state's superposition profile. While it doesn't change the probabilities of measuring $|0\\rangle$ or $|1\\rangle$ immediately (since $|e^{i\\phi}|^2 = 1$), it <strong>crucially changes how the state interferes</strong> with other states in subsequent gates (like the Hadamard gate).</p>
<p><strong>If you don't control the relative phase, you don't have a quantum algorithm. You just have a probabilistic coin flip.</strong></p>
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
<p>This is where the "Physics" of quantum mechanics meets the "Statistics" of reality. A qubit in superposition is not a fuzzy value; it is a Random Variable waiting to be sampled.</p>
<p>In classical probability, a random variable $X$ is a variable that takes on specific values with specific probabilities. In Quantum Computing, the act of measurement creates this random variable.</p>

<h3>1. The Discrete Random Variable (The Outcome)</h3>
<p>When you measure a qubit in the $Z$-basis, you are querying a discrete random variable that can only take one of two specific values (the eigenvalues of the $Z$-operator):</p>
<ul>
    <li><strong>+1</strong> (corresponding to state $|0\\rangle$)</li>
    <li><strong>-1</strong> (corresponding to state $|1\\rangle$)</li>
</ul>
<p><strong>Crucial Note:</strong> Computer scientists often map these to the bits $0$ and $1$, but physically/mathematically, the math works on the eigenvalues $+1$ and $-1$.</p>

<h3>2. The Probability Distribution (The State)</h3>
<p>The quantum state vector $|\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle$ defines the Probability Mass Function (PMF) for this random variable.</p>
$$P(X = +1) = |\\alpha|^2$$
$$P(X = -1) = |\\beta|^2$$
<p><strong>Constraint:</strong> Since something must happen, $|\\alpha|^2 + |\\beta|^2 = 1$.</p>

<h3>3. The Expectation Value (The Average)</h3>
<p>This is the most misunderstood concept for beginners. The Expectation Value (denoted as $E[X]$ or $\\langle Z \\rangle$) is <strong>NOT</strong> the value you expect to see in a single measurement.</p>
<p>Since the outcomes are only $+1$ or $-1$, you will never see the expectation value (which is usually a decimal, like $0.5$) in a single shot.</p>
<p>The Expectation Value is the average of the results if you repeated the experiment 1000 times.</p>
$$E[X] = \\sum x_i P(x_i)$$
$$E[X] = (+1) \\cdot P(0) + (-1) \\cdot P(1)$$
$$E[X] = |\\alpha|^2 - |\\beta|^2$$
<p>This number tells us the "bias" of the qubit.</p>
<ul>
    <li>If $E[X] = 1$, the qubit is definitely $|0\\rangle$.</li>
    <li>If $E[X] = -1$, the qubit is definitely $|1\\rangle$.</li>
    <li>If $E[X] = 0$, the qubit is perfectly balanced (50/50 superposition).</li>
</ul>
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
<p>This is the most critical distinction in all of quantum mechanics. If you treat amplitudes like probabilities, you will fail to understand how a quantum computer actually solves problems.</p>
<p><strong>Nature operates on Amplitudes. We only observe Probabilities.</strong></p>

<h3>1. The Fundamental Difference</h3>
<p><strong>Probabilities</strong> ($P$) are real numbers between 0 and 1. They describe uncertainty. If you have a 50% chance of rain and a 30% chance of snow, you add them. Probabilities accumulate; they only increase the total likelihood of outcomes.</p>
<p><strong>Amplitudes</strong> ($\\alpha$) are complex numbers. They describe the physical state. Because they have a phase (direction), amplitudes can point in opposite directions and <em>cancel</em> when added.</p>

<h3>2. The Power: Interference</h3>
<p>This is why quantum computers can outperform classical ones.</p>
<p><strong>Classical:</strong> If there are two ways to get a result, probabilities add:</p>
$$P_{total} = P_{path1} + P_{path2}$$
<p><strong>Quantum:</strong> Amplitudes add first, then you square for probability:</p>
$$\\alpha_{total} = \\alpha_{path1} + \\alpha_{path2}$$
<p><strong>Destructive Interference:</strong> If $\\alpha_{path1} = 0.5$ and $\\alpha_{path2} = -0.5$, then</p>
<p>Classical intuition: $0.5^2 + (-0.5)^2 = 0.25 + 0.25 = 0.5$.</p>
<p>Quantum reality: $0.5 + (-0.5) = 0$, so $P = |0|^2 = 0$. The event cannot happen.</p>
<p>Quantum algorithms (Grover, Shor) choreograph amplitudes so wrong answers cancel (destructive interference) and the right answer amplifies (constructive interference).</p>

<div style=\"text-align:center; margin:20px;\">
  <img src=\"/static/images/wave%20interference.png\" alt=\"Wave interference pattern\" style=\"max-width: 420px; border-radius: 8px;\">
  <p><em>Interference: amplitudes combine before probabilities are observed.</em></p>
}</div>

<h3>📝 Knowledge Check: The \"Impossible\" Zero</h3>
<p>Imagine a system with three paths contributing amplitude to the $|1\\rangle$ state:</p>
<ul>
  <li>Path A: $\\frac{1}{2}$</li>
  <li>Path B: $\\frac{i}{2}$</li>
  <li>Path C: $-\\frac{1}{2} - \\frac{i}{2}$</li>
 </ul>
<p><strong>Classical Thinking:</strong> Compute $|A|^2 + |B|^2 + |C|^2$.</p>
<p><strong>Quantum Thinking:</strong> Compute $(A + B + C)$ first, then $|\\alpha_{total}|^2$.</p>
<p>Compare the results. The difference is the <strong>quantum magic</strong>.</p>
                    """,
                    "position": 10,
                    "task_json": None,
                    "section": "probability-theory"
                },
                {
                    "slug": "classical-logic-boolean",
                    "title": "11. Classical Logic: Boolean Algebra",
                    "content": """
<h2>Classical Logic: Boolean Algebra</h2>
<p>You have established the mathematical framework. Now we must understand the fundamental computational constraints that force us to use quantum mechanics.</p>

<h3>1. Boolean Algebra: The Classical Baseline</h3>
<p>Boolean Algebra is the math of logic. It describes the relationship between discrete states represented by a bit: True (1) or False (0). The entire classical computer is built from simple, truth-table driven gates:</p>
<ul>
  <li><strong>AND</strong> ($A \\land B$): Output is 1 only if both inputs are 1.</li>
  <li><strong>OR</strong> ($A \\lor B$): Output is 1 if either input is 1.</li>
  <li><strong>NOT</strong> ($\\neg A$): Flips the input.</li>
  <li><strong>Bit values</strong>: <em>True</em> = 1, <em>False</em> = 0.</li>
</ul>
<div style=\"text-align:center; margin: 16px 0;\">
  <img src=\"/static/images/Logic%20Gates%20Symbols%20With%20Truth%20Table.jpeg\" alt=\"Logic gate symbols and truth tables\" style=\"max-width: 680px; width: 100%; border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.2);\" />
  <p style=\"color: var(--text-muted); font-size: 0.9rem;\">Classical logic gates and their truth tables.</p>
</div>

<h3>2. The Problem: Irreversibility</h3>
<p>Most classical gates, such as AND and OR, are <strong>irreversible</strong>. This means you cannot uniquely determine the input from the output. When a gate is irreversible, it loses information. This lost information is linked to thermodynamic entropy, and for every bit of information lost, the operation must dissipate energy (Landauer's Principle).</p>
<p>Quantum computing is based on <strong>unitary</strong> operations (matrices that conserve probability/vector length), and all unitary operations are mathematically reversible. To create a quantum algorithm, we must use logic that is also reversible.</p>

<h3>3. The Bridge: Reversible Logic</h3>
<p>In quantum circuits, gates are constructed such that the input state can always be recovered from the output state. They do not lose information.</p>
<p>For example, the <strong>Pauli-X</strong> gate (Quantum NOT) is reversible: if you apply it twice, you get back to the original state ($X^2 = I$). All quantum gates must be part of a reversible system.</p>
                    """,
                    "position": 11,
                    "task_json": None,
                    "section": "classical-logic"
                },
                {
                    "slug": "classical-logic-gates",
                    "title": "12. Classical Logic: Logic Gates",
                    "content": """
<h2>Classical Logic: Logic Gates</h2>
<p>You established why standard classical gates fail in a quantum system (information loss/irreversibility). Now, we look at the specific gates that serve as the direct mathematical blueprint for quantum circuits.</p>
<p><strong>Goal:</strong> Use logic gates that take <em>N</em> inputs and produce <em>N</em> outputs, where the input can always be uniquely determined from the output.</p>

<h3>1. The Controlled-NOT (CNOT)</h3>
<p>The Controlled-NOT (CNOT) gate is the most fundamental two-bit reversible gate. It is the direct precursor to its quantum counterpart.</p>

<table style=\"width:100%; max-width:600px; border-collapse:collapse; margin:12px 0;\">
  <thead>
    <tr>
      <th style=\"border-bottom:1px solid var(--border); text-align:left; padding:6px;\">Control (A)</th>
      <th style=\"border-bottom:1px solid var(--border); text-align:left; padding:6px;\">Target (B)</th>
      <th style=\"border-bottom:1px solid var(--border); text-align:left; padding:6px;\">Output (A')</th>
      <th style=\"border-bottom:1px solid var(--border); text-align:left; padding:6px;\">Output (B')</th>
    </tr>
  </thead>
  <tbody>
    <tr><td style=\"padding:6px;\">0</td><td style=\"padding:6px;\">0</td><td style=\"padding:6px;\">0</td><td style=\"padding:6px;\">0</td></tr>
    <tr><td style=\"padding:6px;\">0</td><td style=\"padding:6px;\">1</td><td style=\"padding:6px;\">0</td><td style=\"padding:6px;\">1</td></tr>
    <tr><td style=\"padding:6px;\">1</td><td style=\"padding:6px;\">0</td><td style=\"padding:6px;\">1</td><td style=\"padding:6px;\">1</td></tr>
    <tr><td style=\"padding:6px;\">1</td><td style=\"padding:6px;\">1</td><td style=\"padding:6px;\">1</td><td style=\"padding:6px;\">0</td></tr>
  </tbody>
  </table>

<p><strong>Rule:</strong> The Control bit remains unchanged (A' = A). The Target bit is flipped only if the Control bit is 1 (B' = B \u2295 A, where \u2295 is XOR).</p>
<p><strong>Significance:</strong> Because the CNOT preserves the control bit and the operation on the target depends deterministically on the control, you can perfectly reverse this operation.</p>

<h3>2. Universal Reversible Logic</h3>
<p>A set of gates is universal if any logical function can be built using only those gates. Classical irreversible sets are universal (e.g., NAND alone or NOR alone). For reversible logic, we need more complex gates to achieve universality:</p>
<ul>
  <li><strong>Toffoli (CCNOT):</strong> A 3-bit gate (2 controls, 1 target). It flips the target only if both control bits are 1. The Toffoli gate alone is universal for all classical reversible computation.</li>
  <li><strong>Fredkin (CSWAP):</strong> A 3-bit gate that swaps two target bits only if the control bit is 1.</li>
</ul>
<p>The CNOT and Toffoli are crucial because they demonstrate that reversible logic is sufficient to perform any classical computation, and they are the two most important multi-qubit gates in any quantum circuit.</p>
                    """,
                    "position": 12,
                    "task_json": json.dumps({
                        "description": "Create a Bell Pair: Apply H on q0, then CNOT with control q0 and target q1. Run simulation and verify 50% |00> and 50% |11>.",
                        "criteria": "bell_pair",
                        "qubits": 2
                    }),
                    "section": "classical-logic"
                },
                {
                    "slug": "classical-logic-reversible",
                    "title": "13. Classical Logic: Reversible Computing",
                    "content": """
<h2>Classical Logic: Reversible Computing</h2>
<p>This is the final conceptual hurdle before we enter the quantum realm proper. You need to unlearn how you think about memory.</p>

<p>In classical coding, you are used to variables being overwritten.</p>
<pre><code>x = 5
x = x + 1  // The old '5' is gone
</code></pre>

<p>In Quantum Computing, <strong>you cannot overwrite data.</strong> This isn't just a rule; it's a law of physics. Because quantum operators are unitary (probability conserving), they must be reversible. If you erase information, you break the unitarity, and the quantum state collapses or decoheres.</p>

<h3>1. Landauer's Principle: Information is Physical</h3>
<p>Why does this matter? Rolf Landauer proved that <strong>erasing</strong> information (irreversible computing) necessarily dissipates heat.</p>
<p>$$E \\ge k_B T \\ln 2$$</p>
<p>Every bit you \"delete\" costs energy.</p>

<p>Quantum computers must operate with effectively zero energy dissipation during the calculation to maintain the delicate quantum state. Therefore, <strong>every step must be logically reversible.</strong></p>

<h3>2. The Consequence: \"Garbage\" Accumulation</h3>
<p>Because you can't throw away intermediate data, quantum algorithms generate a massive amount of \"Garbage Qubits\" (ancilla bits holding intermediate results).</p>
<p>If you compute $f(x)$ using temporary registers, you end up with:</p>
<p>$$|x\\rangle \\to |x\\rangle |g(x)\\rangle |f(x)\\rangle$$</p>
<p>where $|g(x)\\rangle$ is the garbage left over from the calculation.</p>

<p><strong>The Trap:</strong> If you leave this garbage entangled with your result, it acts like a \"measurement\" by the environment. It will kill the interference pattern you are trying to create. You <strong>must</strong> clean it up.</p>

<h3>3. The Solution: Uncomputation</h3>
<p>How do you delete data without \"deleting\" it? You run the circuit in reverse.</p>

<p>The standard pattern for a clean quantum calculation is:</p>
<ol>
  <li><strong>Compute:</strong> Calculate the result into a blank target register.<br>
    $(|x\\rangle, |0\\rangle, |0\\rangle) \\xrightarrow{U} (|x\\rangle, |g\\rangle, |f(x)\\rangle)$
  </li>
  <li><strong>Copy:</strong> Copy the answer to a safe \"readout\" register (usually via CNOTs).<br>
    $(|x\\rangle, |g\\rangle, |f(x)\\rangle, |0\\rangle) \\to (|x\\rangle, |g\\rangle, |f(x)\\rangle, |f(x)\\rangle)$
  </li>
  <li><strong>Uncompute:</strong> Apply the <em>inverse</em> of the compute operation ($U^\dagger$). This reverses the calculation of the garbage and the original result, returning the working registers to zero.<br>
    $(|x\\rangle, |g\\rangle, |f(x)\\rangle, |f(x)\\rangle) \\xrightarrow{U^\\dagger} (|x\\rangle, |0\\rangle, |0\\rangle, |f(x)\\rangle)$
  </li>
  </ol>

<p>Now you have the clean result $|f(x)\\rangle$ and empty working space, without having thermally erased anything.</p>

<div style=\"text-align:center; margin: 16px 0;\">
  <img src=\"/static/images/13.%20Classical%20Logic-%20Reversible%20Computing.jpeg\" alt=\"Reversible computing workflow schematic\" style=\"max-width: 720px; width: 100%; border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.2);\" />
  <p style=\"color: var(--text-muted); font-size: 0.9rem;\">Reversible compute–copy–uncompute pattern.</p>
</div>

<hr>

<h3>Your Task: The Uncomputation Workflow</h3>
<p>You have a circuit $U$ that takes input $x$ and a workspace $0$, and produces $(x, x \\oplus 1)$.</p>
<p>$$U(x, 0) \\to (x, x \\oplus 1)$$</p>
<p>You want to isolate the result $x \oplus 1$ and return the workspace to $0$.</p>

<ol>
  <li><strong>Step 1 (Compute):</strong> Prepare the input qubit to $|1\\rangle$ (apply X on <code>q0</code>). Build <code>U</code> using CNOT(control <code>q0</code>, target <code>q1</code>) then X on <code>q1</code>. What is the state?</li>
  <li><strong>Step 2 (Copy):</strong> Apply a CNOT where the \"work\" qubit <code>q1</code> is the control and a new third qubit <code>q2</code> (initialized to $|0\\rangle$) is the target. What is the state of the three qubits?</li>
  <li><strong>Step 3 (Uncompute):</strong> Apply $U^\\dagger$ (the inverse of <code>U</code>) to the first two qubits: X on <code>q1</code> then CNOT(control <code>q0</code>, target <code>q1</code>). What is the final state?</li>
</ol>

<p><em>Hint:</em> <code>U</code> is its own inverse.</p>
                    """,
                    "position": 13,
                    "task_json": json.dumps({
                        "description": "Uncomputation workflow: Prepare q0=1. Compute U as CNOT(q0→q1) then X on q1. Copy with CNOT(q1→q2). Uncompute with X on q1 then CNOT(q0→q1). Final state should be |1,0,0>.",
                        "criteria": "uncompute_workflow",
                        "qubits": 3
                    }),
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
<h2>1. Postulates: State Space</h2>
<p>We have finished the pre-requisites (Math and Logic). Now we enter <strong>Physics</strong>.</p>
<p>Quantum Mechanics is built on four \"Postulates\"—axioms that cannot be proven, only verified by experiment. If you accept them, everything else follows.</p>

<h3>Postulate 1: The State Space</h3>
<p><strong>The Rule:</strong> Associated to any isolated physical system is a complex vector space with an inner product (a Hilbert Space) known as the <strong>state space</strong> of the system. The system is completely described by its <strong>state vector</strong> ($|\\psi\\rangle$), which is a <strong>unit vector</strong> in the system's state space.</p>

<h4>1. The Requirement: Normalization</h4>
<p>The most critical phrase above is \"unit vector.\" Because the coefficients of the vector represent probability amplitudes, and total probability must equal 100% (1.0), every valid quantum state must satisfy the <strong>Normalization Condition</strong>:</p>
<p>$$\\langle \\psi | \\psi \\rangle = 1$$</p>
<p>If $|\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle$, then $|\\alpha|^2 + |\\beta|^2 = 1$.</p>
<p>If you have a vector where the squared magnitudes do not sum to 1, it is <strong>not</strong> a valid quantum state. It is just a mathematical abstraction until you normalize it.</p>

<h4>2. The Implication: The Exponential Explosion</h4>
<p>The state space for a single qubit is $\\mathbb{C}^2$ (2 complex dimensions). The state space for $N$ qubits is the tensor product of the individual spaces: $\\mathbb{C}^{2^N}$.</p>
<ul>
  <li>1 Qubit: 2 complex numbers.</li>
  <li>10 Qubits: $2^{10} = 1,024$ complex numbers.</li>
  <li>50 Qubits: $2^{50} \\approx 1.1 \\times 10^{15}$ (Petabytes of RAM to simulate).</li>
  <li>300 Qubits: $2^{300}$ (More numbers than atoms in the visible universe).</li>
  </ul>
<p>This is why we build quantum computers. To simulate a 300-qubit system on a classical computer is physically impossible. Nature manages this information effortlessly.</p>

<div style=\"text-align:center; margin: 16px 0;\">
  <img src=\"/static/images/exponential%20growth%20graph.jpeg\" alt=\"Exponential growth of Hilbert space dimension (2^N)\" style=\"max-width: 720px; width: 100%; border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.2);\" />
  <p style=\"color: var(--text-muted); font-size: 0.9rem;\">Exponential growth: the state space dimension scales as $2^N$.</p>
</div>

<hr>

<h3>Your Task: The \"Illegal\" State</h3>
<p>You are given the following vector representing a potential system state:</p>
<p>$$|\\phi\\rangle = 3|0\\rangle + 4i|1\\rangle$$</p>
<ol>
  <li><strong>Check Validity:</strong> Calculate the squared magnitude of the vector (the sum of the squared moduli of the coefficients). Does it equal 1?</li>
  <li><strong>Fix It:</strong> Normalize the vector. Find a constant $N$ such that if you multiply $|\\phi\\rangle$ by $\\frac{1}{N}$, the resulting vector is a valid unit vector. (Hint: $N = \\sqrt{\\langle \\phi | \\phi \\rangle}$).</li>
</ol>
<p><strong>Warning:</strong> Don't forget that $|4i|^2$ is $16$, not $-16$. Modulus is always positive.</p>
                    """,
                    "position": 1,
                    "task_json": json.dumps({
                        "description": "Prepare the normalized state (3|0> + 4i|1>)/5. Use Ry(≈1.8546) then S gate to set amplitudes and phase. Confirm probabilities ≈36% and 64% with |1> carrying +i phase.",
                        "criteria": "normalize_illegal_state",
                        "qubits": 1
                    }),
                    "section": "postulates-of-quantum-mechanics"
                },
                {
                    "slug": "postulates-evolution",
                    "title": "2. Postulates: Evolution",
                    "content": """
<h2>2. Postulates: Evolution</h2>
<p>You have the state. Now you need to move it.</p>

<h3>Postulate 2: Evolution (Unitary Dynamics)</h3>

<p><strong>The Rule:</strong></p>
<p>The evolution of a closed quantum system is described by a <strong>unitary transformation</strong>. That is, the state $|\\psi\\rangle$ of the system at time $t_1$ is related to the state $|\\psi'\\rangle$ at time $t_2$ by a unitary operator $U$ which depends only on the times $t_1$ and $t_2$.</p>

<p>$$|\\psi'\\rangle = U|\\psi\\rangle$$</p>

<p>(Note: In continuous physics, this is derived from the Schrödinger equation. In Quantum Computing, we discretize this into "Gates".)</p>

<h3>1. What is "Unitary"?</h3>

<p>A matrix $U$ is unitary if its conjugate transpose ($U^\\dagger$) is also its inverse ($U^{-1}$).</p>
<p>Mathematically:</p>

<p>$$U^\\dagger U = I$$</p>

<p>Where $I$ is the Identity matrix.</p>

<h3>2. Why do we care? (Conservation of Probability)</h3>

<p>This is not just linear algebra jargon. It is a physical requirement.</p>
<p>If you start with a valid quantum state (total probability = 1), you <strong>must</strong> end with a valid quantum state (total probability = 1).</p>

<p>If our operators were not unitary, the length of the state vector would stretch or shrink.</p>
<ul>
    <li><strong>Stretch:</strong> Total probability > 100%. Impossible.</li>
    <li><strong>Shrink:</strong> Total probability < 100%. The qubit "disappears."</li>
</ul>

<p>Unitary matrices are effectively "complex rotations." They rotate the state vector around the Hilbert space without changing its length.</p>

<h3>3. Reversibility</h3>

<p>Because $U^{-1} = U^\\dagger$, <strong>quantum mechanics is reversible</strong>. If you apply a gate $U$, you can always undo it by applying $U^\\dagger$. This is fundamentally different from classical computing, where $x = 0$ destroys the previous value of $x$. In quantum, nothing is ever truly deleted until measurement.</p>

<hr>

<h3>Your Task: verifying the Hadamard Gate</h3>

<p>The <strong>Hadamard Gate ($H$)</strong> is the most important single-qubit gate. It creates superposition.</p>
<p>$$H = \\frac{1}{\\sqrt{2}} \\begin{pmatrix} 1 & 1 \\\\ 1 & -1 \\end{pmatrix}$$</p>

<p>You need to prove it is a valid quantum operator.</p>

<ol>
    <li><strong>Find $H^\\dagger$:</strong> Calculate the conjugate transpose of $H$. (Note: Since $H$ has only real numbers, the complex conjugate is trivial).</li>
    <li><strong>Multiply:</strong> Calculate the matrix product $H^\\dagger H$.</li>
    <li><strong>Verify:</strong> Does the result equal the Identity matrix $\\begin{pmatrix} 1 & 0 \\\\ 0 & 1 \\end{pmatrix}$?</li>
</ol>

<p>If it does, the gate preserves probability. If not, the math is broken.</p>
""",
                    "position": 2,
                    "task_json": json.dumps({
                        "description": "Verify Unitarity: Apply H then H again. Does the state return to |0>?",
                        "criteria": "verify_hadamard_unitary",
                        "qubits": 1
                    }),
                    "section": "postulates-of-quantum-mechanics"
                },
                {
                    "slug": "postulates-measurement",
                    "title": "3. Postulates: Measurement",
                    "content": """
<h3>Postulate 3: Measurement (The Born Rule and State Collapse)</h3>

<p><strong>The Rule:</strong><br>
Quantum measurements are governed by observables, which are described by Hermitian operators ($M$).</p>

<p><strong>The Outcome (Eigenvalues):</strong> The only possible results of a measurement are the eigenvalues ($\\lambda_i$) of the observable $M$. (Since measurement results must be real, $M$ must be Hermitian, as all Hermitian operators have real eigenvalues).</p>

<p><strong>The Probability (Born Rule):</strong> The probability of observing a specific eigenvalue $\\lambda_i$ is given by the squared magnitude of the projection of the state vector $|\\psi\\rangle$ onto the corresponding eigenvector $|e_i\\rangle$:</p>

$$P(\\lambda_i) = |\\langle e_i | \\psi \\rangle|^2$$

<p><strong>The State Collapse:</strong> Immediately after the measurement yields the result $\\lambda_i$, the state of the system <strong>instantaneously collapses</strong> to the corresponding eigenvector $|e_i\\rangle$.</p>

<p><strong>The Trap: Non-Determinism</strong><br>
Before measurement, the qubit exists in a superposition of all possible outcomes. The state is perfectly known ($\\alpha$ and $\\beta$ are known). However, the <strong>result</strong> is fundamentally non-deterministic. We only know the probabilities. After measurement, the amplitude information is gone; the system is forced into one definite classical state ($|0\\rangle$ or $|1\\rangle$).</p>

<hr>

<h3>Your Task: Calculating Collapse</h3>

<p>The standard measurement in quantum computing is performed with the <strong>Pauli-Z Observable</strong> ($M=Z$).</p>

<p><strong>Z-Observable:</strong> $Z = \\begin{pmatrix} 1 & 0 \\\\ 0 & -1 \\end{pmatrix}$</p>

<p><strong>Eigenvectors/Outcomes:</strong></p>
<ul>
    <li>$|e_0\\rangle = |0\\rangle$ (Eigenvalue $\\lambda_0 = +1$)</li>
    <li>$|e_1\\rangle = |1\\rangle$ (Eigenvalue $\\lambda_1 = -1$)</li>
</ul>

<p>Suppose you prepare the qubit in the balanced superposition state $|+\\rangle$:</p>

$$|+\\rangle = \\frac{1}{\\sqrt{2}}|0\\rangle + \\frac{1}{\\sqrt{2}}|1\\rangle$$

<p><strong>Calculate the Probability:</strong> What is the probability $P(+1)$ of measuring the eigenvalue $+1$ (i.e., collapsing to $|0\\rangle$)?</p>

$$P(+1) = |\\langle 0 | + \\rangle|^2$$

<p><strong>State After Measurement:</strong> If you perform the measurement and the result is $+1$, what is the state of the qubit <strong>immediately</strong> after the collapse?</p>
""",
                    "position": 3,
                    "task_json": json.dumps({
                        "description": "Prepare the |+> state using the H gate, then add a Measurement gate. Observe the probabilities (approx 50/50).",
                        "criteria": "measurement_collapse",
                        "qubits": 1
                    }),
                    "section": "postulates-of-quantum-mechanics"
                },
                {
                    "slug": "the-qubit-superposition",
                    "title": "4. The Qubit: Superposition",
                    "content": """
<h2>The Qubit: Superposition</h2>
<p>You have accepted the rules. Now, let’s define the key resource: the **Qubit**.</p>

<h3>The Qubit: Superposition</h3>
<p>A **Qubit** (Quantum bit) is the physical realization of a two-level quantum system. While a classical bit stores a value of 0 or 1, a qubit exists in a **superposition** of the two basis states, $|0\\rangle$ and $|1\\rangle$.</p>

<p><strong>The Hard Truth:</strong> Superposition is the result of Postulate 1 (State Space). It simply means the state of the qubit is a **unit vector** that is a linear combination of the basis vectors $|0\\rangle$ and $|1\\rangle$:</p>
$$|\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle$$
<p>where $\\alpha$ and $\\beta$ are the complex **probability amplitudes** you mastered earlier.</p>

<h3>⚠️ The Misconception</h3>
<p>You must avoid the naive interpretation that a qubit is "simultaneously 0 and 1." This analogy is fundamentally misleading.</p>
<ul>
    <li>A qubit is **one single state** ($|\\psi\\rangle$) that exists in the Hilbert space. It is a single vector, not two separate bits.</li>
    <li>The "mixture" only reflects the **potential** outcomes upon measurement.</li>
</ul>
<p>Until the moment you apply the measurement operator (Postulate 3), the state $|\\psi\\rangle$ is **pure** and single. It is the ability to manipulate the relationship between $\\alpha$ and $\\beta$ (especially their **relative phase**) that enables quantum computation.</p>

<p>Every point on the surface of the sphere (except the poles) is a valid superposition state.</p>
<div style="text-align: center; margin: 20px;">
    <img src="/static/images/bloch-sphere.png" alt="Bloch Sphere" style="max-width: 300px; border-radius: 8px;">
</div>

<h3>Your Task: Constructing Bias</h3>
<p>You must be able to translate desired measurement probabilities directly into a valid state vector.</p>
<p>Construct a superposition state $|\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle$ that meets the following criteria:</p>
<ol>
    <li>The probability of measuring **$|0\\rangle$** is $P_0 = 1/3$.</li>
    <li>The probability of measuring **$|1\\rangle$** is $P_1 = 2/3$.</li>
    <li>Assume the coefficients $\\alpha$ and $\\beta$ are **real numbers** (ignore complex phase for simplicity here).</li>
</ol>
<p>What are the specific numerical values for $\\alpha$ and $\\beta$ that define this state?</p>
                    """,
                    "position": 4,
                    "task_json": json.dumps({
                        "description": "Construct a state with P(0) ≈ 33% and P(1) ≈ 67%. Hint: Use the Ry gate with theta ≈ 1.91.",
                        "criteria": "bias_one_third",
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
    # REMOVED: User requested to remove the knowledge check from Vectors lesson.
    # print("Seeding Quizzes...")
    # Find lesson id
    # if db_type == "postgres":
    #     cur.execute("SELECT id FROM lessons WHERE slug=%s", ("linear-algebra-vectors",))
    #     lesson_row = cur.fetchone()
    #     lesson_id = _row_get(lesson_row, 'id', 0)
    # else:
    #     cur.execute("SELECT id FROM lessons WHERE slug=?", ("linear-algebra-vectors",))
    #     lesson_row = cur.fetchone()
    #     lesson_id = _row_get(lesson_row, 'id', 0)
        
    # if lesson_id:
    #     quiz_title = "Linear Algebra Check"
    #     question_text = "Using the column definitions for |0> and |1> above, if you perform the matrix addition and scalar multiplication for α|0> + β|1>, what does the single resulting column vector look like?"
    #     # Options: [α, β], [α + β, 0], [0, α + β], [1, 1]
    #     # Correct is [α, β] which is index 0.
    #     options = json.dumps(["[α, β]", "[α + β, 0]", "[0, α + β]", "[1, 1]"])
    #     correct_idx = 0
        
    #     if db_type == "postgres":
    #         cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (lesson_id, quiz_title))
    #         quiz_row = cur.fetchone()
    #         quiz_id = _row_get(quiz_row, 'id', 0)
            
    #         cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)", 
    #             (quiz_id, question_text, options, correct_idx))
    #     else:
    #         cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (lesson_id, quiz_title))
    #         quiz_id = cur.lastrowid
            
    #         cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)", 
    #             (quiz_id, question_text, options, correct_idx))

    # 4. Add a sample Quiz for "Linear Algebra: Matrices"
    # REMOVED: User requested to remove the knowledge check from Matrices lesson.
    # Find lesson id
    # if db_type == "postgres":
    #     cur.execute("SELECT id FROM lessons WHERE slug=%s", ("linear-algebra-matrices",))
    #     lesson_row = cur.fetchone()
    #     lesson_id = _row_get(lesson_row, 'id', 0)
    # else:
    #     cur.execute("SELECT id FROM lessons WHERE slug=?", ("linear-algebra-matrices",))
    #     lesson_row = cur.fetchone()
    #     lesson_id = _row_get(lesson_row, 'id', 0)
        
    # if lesson_id:
    #     quiz_title = "Matrix Operation Check"
    #     question_text = "Calculate the resulting state |ψ'> when applying X to |ψ> = 1/√2 * [1, 1]^T. What is the final column vector?"
    #     # Options: 
    #     # 1. 1/√2 * [1, 1] (Correct)
    #     # 2. 1/√2 * [1, -1]
    #     # 3. [0, 0]
    #     # 4. [1, 0]
    #     options = json.dumps(["1/√2 * [1, 1]", "1/√2 * [1, -1]", "[0, 0]", "[1, 0]"])
    #     correct_idx = 0
        
    #     if db_type == "postgres":
    #         cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (lesson_id, quiz_title))
    #         quiz_row = cur.fetchone()
    #         quiz_id = _row_get(quiz_row, 'id', 0)
    #         
    #         cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)", 
    #             (quiz_id, question_text, options, correct_idx))
    #     else:
    #         cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (lesson_id, quiz_title))
    #         quiz_id = cur.lastrowid
    #         
    #         cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)", 
    #             (quiz_id, question_text, options, correct_idx))

    # 5. Add a sample Quiz for "Linear Algebra: Eigenvalues"
    # REMOVED: User requested to remove the knowledge check from Eigenvalues lesson.
    # Find lesson id
    # if db_type == "postgres":
    #     cur.execute("SELECT id FROM lessons WHERE slug=%s", ("linear-algebra-eigenvalues",))
    #     lesson_row = cur.fetchone()
    #     lesson_id = _row_get(lesson_row, 'id', 0)
    # else:
    #     cur.execute("SELECT id FROM lessons WHERE slug=?", ("linear-algebra-eigenvalues",))
    #     lesson_row = cur.fetchone()
    #     lesson_id = _row_get(lesson_row, 'id', 0)
        
    # if lesson_id:
    #     quiz_title = "Eigenvalue Check"
    #     question_text = "When applying the Pauli-Z gate to the state |1>, what is the resulting eigenvalue?"
    #     # Options: 
    #     # 1. 1
    #     # 2. -1 (Correct)
    #     # 3. 0
    #     # 4. i
    #     options = json.dumps(["1", "-1", "0", "i"])
    #     correct_idx = 1
        
    #     if db_type == "postgres":
    #         cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (lesson_id, quiz_title))
    #         quiz_row = cur.fetchone()
    #         quiz_id = _row_get(quiz_row, 'id', 0)
    #         
    #         cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)", 
    #             (quiz_id, question_text, options, correct_idx))
    #     else:
    #         cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (lesson_id, quiz_title))
    #         quiz_id = cur.lastrowid
    #         
    #         cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)", 
    #             (quiz_id, question_text, options, correct_idx))

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
        # Check if quiz exists
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (lesson_id, quiz_title))
        
        existing_quiz = cur.fetchone()
        if not existing_quiz:
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
        else:
             print(f"Quiz '{quiz_title}' already exists.")

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
        # Check if quiz exists
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (lesson_id, quiz_title))
        
        existing_quiz = cur.fetchone()
        if not existing_quiz:
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
        else:
             print(f"Quiz '{quiz_title}' already exists.")

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
        # Check if quiz exists
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (lesson_id, quiz_title))
        
        existing_quiz = cur.fetchone()
        if not existing_quiz:
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
        else:
             print(f"Quiz '{quiz_title}' already exists.")

    # 9. Add a sample Quiz for "Complex Numbers: Euler's Formula"
    # Find lesson id
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("complex-numbers-euler",))
        lesson_row = cur.fetchone()
        lesson_id = _row_get(lesson_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("complex-numbers-euler",))
        lesson_row = cur.fetchone()
        lesson_id = _row_get(lesson_row, 'id', 0)
        
    if lesson_id:
        quiz_title = "Euler's Formula Check"
        # Check if quiz exists
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (lesson_id, quiz_title))
        
        existing_quiz = cur.fetchone()
        if not existing_quiz:
            question_text = "What is the value of the phase factor e^{iπ}, and consequently, what does the Z gate do to the |1> component?"
            # Options: 
            # 1. e^{iπ} = 1, so it leaves |1> unchanged.
            # 2. e^{iπ} = -1, so it flips the sign (phase) of |1>. (Correct)
            # 3. e^{iπ} = i, so it rotates |1> by 90 degrees.
            # 4. e^{iπ} = 0, so it destroys the |1> component.
            options = json.dumps([
                "e^{iπ} = 1, so it leaves |1> unchanged.", 
                "e^{iπ} = -1, so it flips the sign (phase) of |1>.", 
                "e^{iπ} = i, so it rotates |1> by 90 degrees.", 
                "e^{iπ} = 0, so it destroys the |1> component."
            ])
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
        else:
             print(f"Quiz '{quiz_title}' already exists.")

    # 10. Add a sample Quiz for "Complex Numbers: Phases"
    # Find lesson id
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("complex-numbers-phases",))
        lesson_row = cur.fetchone()
        lesson_id = _row_get(lesson_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("complex-numbers-phases",))
        lesson_row = cur.fetchone()
        lesson_id = _row_get(lesson_row, 'id', 0)
        
    if lesson_id:
        quiz_title = "Phase Distinction Check"
        # Check if quiz exists
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (lesson_id, quiz_title))
        
        existing_quiz = cur.fetchone()
        if not existing_quiz:
            question_text = "Which of the following statements accurately describes the difference between Global Phase and Relative Phase?"
            # Options: 
            options = json.dumps([
                "Global phase changes measurement probabilities, while relative phase does not.", 
                "Relative phase is physically meaningless, while global phase drives interference.", 
                "Global phase is physically meaningless (ghost), while relative phase drives interference (engine).", 
                "Both phases are equally measurable and impact the Bloch sphere rotation."
            ])
            correct_idx = 2
            
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
        else:
             print(f"Quiz '{quiz_title}' already exists.")

    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("probability-theory-random-variables",))
        rv_row = cur.fetchone()
        rv_lesson_id = _row_get(rv_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("probability-theory-random-variables",))
        rv_row = cur.fetchone()
        rv_lesson_id = _row_get(rv_row, 'id', 0)

    if rv_lesson_id:
        quiz_title = "The Trap of the Average"
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (rv_lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (rv_lesson_id, quiz_title))

        existing_quiz = cur.fetchone()
        if not existing_quiz:
            q1_text = "For |ψ⟩ = √0.8|0⟩ + √0.2|1⟩, what are P(X=+1) and P(X=-1)?"
            q1_options = json.dumps([
                "P(+1)=0.8, P(-1)=0.2",
                "P(+1)=0.2, P(-1)=0.8",
                "P(+1)=0.64, P(-1)=0.36",
                "P(+1)=0.5, P(-1)=0.5"
            ])
            q1_correct = 0

            q2_text = "Compute ⟨Z⟩ for the state above."
            q2_options = json.dumps([
                "⟨Z⟩ = 0.2",
                "⟨Z⟩ = 0.6",
                "⟨Z⟩ = -0.6",
                "⟨Z⟩ = 1.0"
            ])
            q2_correct = 1

            q3_text = "If you measure once, what number is read out, and can you ever read ⟨Z⟩ in a single shot?"
            q3_options = json.dumps([
                "+1 or -1; you cannot get 0.6 in a single shot",
                "0.6; expectation is a single-shot observable",
                "+1 only; the state collapses deterministically",
                "Any real number between -1 and +1"
            ])
            q3_correct = 0

            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (rv_lesson_id, quiz_title))
                new_quiz_row = cur.fetchone()
                new_quiz_id = _row_get(new_quiz_row, 'id', 0)

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (new_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (new_quiz_id, q2_text, q2_options, q2_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (new_quiz_id, q3_text, q3_options, q3_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (rv_lesson_id, quiz_title))
                new_quiz_id = cur.lastrowid

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (new_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (new_quiz_id, q2_text, q2_options, q2_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (new_quiz_id, q3_text, q3_options, q3_correct))
        else:
            print(f"Quiz '{quiz_title}' already exists.")

    # 12. Add a Quiz for "Probability: Amplitudes vs. Probabilities"
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("probability-theory-amplitudes",))
        ap_row = cur.fetchone()
        ap_lesson_id = _row_get(ap_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("probability-theory-amplitudes",))
        ap_row = cur.fetchone()
        ap_lesson_id = _row_get(ap_row, 'id', 0)

    if ap_lesson_id:
        quiz_title = "The \"Impossible\" Zero"
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (ap_lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (ap_lesson_id, quiz_title))

        existing_quiz = cur.fetchone()
        if not existing_quiz:
            q1_text = "Treating amplitudes as separate probabilities: what is |A|^2 + |B|^2 + |C|^2 for A=1/2, B=i/2, C=-(1/2)-(i/2)?"
            q1_options = json.dumps([
                "1.0 (sum of 0.25 + 0.25 + 0.5)",
                "0.5",
                "0.0",
                "0.25"
            ])
            q1_correct = 0

            q2_text = "Add A+B+C first to get the total amplitude. What is the actual probability |α_total|^2 of measuring |1⟩?"
            q2_options = json.dumps([
                "1.0",
                "0.0",
                "0.5",
                "0.25"
            ])
            q2_correct = 1

            q3_text = "What principle explains the difference between the two results?"
            q3_options = json.dumps([
                "Destructive interference cancels amplitudes before squaring",
                "Probabilities must be squared before summing",
                "Global phase changes measurement outcomes",
                "Hilbert space dimension doubles the probability"
            ])
            q3_correct = 0

            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (ap_lesson_id, quiz_title))
                ap_quiz_row = cur.fetchone()
                ap_quiz_id = _row_get(ap_quiz_row, 'id', 0)

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (ap_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (ap_quiz_id, q2_text, q2_options, q2_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (ap_quiz_id, q3_text, q3_options, q3_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (ap_lesson_id, quiz_title))
                ap_quiz_id = cur.lastrowid

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (ap_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (ap_quiz_id, q2_text, q2_options, q2_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (ap_quiz_id, q3_text, q3_options, q3_correct))
        else:
            print(f"Quiz '{quiz_title}' already exists.")

    # 13. Add a Quiz for "Postulates: Evolution"
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("postulates-evolution",))
        pe_row = cur.fetchone()
        pe_lesson_id = _row_get(pe_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("postulates-evolution",))
        pe_row = cur.fetchone()
        pe_lesson_id = _row_get(pe_row, 'id', 0)

    if pe_lesson_id:
        quiz_title = "Evolution & Unitarity Check"
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (pe_lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (pe_lesson_id, quiz_title))

        existing_quiz = cur.fetchone()
        if not existing_quiz:
            q1_text = "If a quantum operator U is unitary, what must be true about its inverse?"
            q1_options = json.dumps([
                "It is equal to its conjugate transpose (U†)",
                "It is equal to the identity matrix (I)",
                "It is equal to the matrix itself (U)",
                "It is undefined"
            ])
            q1_correct = 0

            q2_text = "Why must quantum evolution be unitary?"
            q2_options = json.dumps([
                "To ensure the total probability always sums to 1 (conservation of probability)",
                "To make the math harder",
                "To allow for faster computation",
                "To ensure all numbers are real"
            ])
            q2_correct = 0

            q3_text = "You apply a Hadamard gate (H) to |0>. What happens if you apply H again immediately?"
            q3_options = json.dumps([
                "The state returns to |0> (H is its own inverse)",
                "The state becomes |1>",
                "The state becomes a complex number",
                "The system crashes"
            ])
            q3_correct = 0

            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (pe_lesson_id, quiz_title))
                pe_quiz_row = cur.fetchone()
                pe_quiz_id = _row_get(pe_quiz_row, 'id', 0)

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (pe_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (pe_quiz_id, q2_text, q2_options, q2_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (pe_quiz_id, q3_text, q3_options, q3_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (pe_lesson_id, quiz_title))
                pe_quiz_id = cur.lastrowid

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (pe_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (pe_quiz_id, q2_text, q2_options, q2_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (pe_quiz_id, q3_text, q3_options, q3_correct))
        else:
            print(f"Quiz '{quiz_title}' already exists.")

    # 14. Add a Quiz for "Postulates: Measurement"
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("postulates-measurement",))
        pm_row = cur.fetchone()
        pm_lesson_id = _row_get(pm_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("postulates-measurement",))
        pm_row = cur.fetchone()
        pm_lesson_id = _row_get(pm_row, 'id', 0)

    if pm_lesson_id:
        quiz_title = "Measurement & Collapse Check"
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (pm_lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (pm_lesson_id, quiz_title))

        existing_quiz = cur.fetchone()
        if not existing_quiz:
            q1_text = "What is the probability P(+1) of measuring +1 (collapsing to |0>) given the state |+> = 1/√2(|0> + |1>)?"
            q1_options = json.dumps([
                "1 (100%)",
                "0.5 (50%)",
                "0 (0%)",
                "0.707 (70.7%)"
            ])
            q1_correct = 1

            q2_text = "If the measurement result is +1, what is the state of the qubit immediately after?"
            q2_options = json.dumps([
                "The state remains |+> (superposition)",
                "The state becomes |->",
                "The state becomes |0>",
                "The state becomes |1>"
            ])
            q2_correct = 2

            q3_text = "What determines the possible results of a quantum measurement?"
            q3_options = json.dumps([
                "The eigenvalues of the observable operator",
                "The user's choice",
                "The amplitude of the state",
                "Random chance"
            ])
            q3_correct = 0

            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (pm_lesson_id, quiz_title))
                pm_quiz_row = cur.fetchone()
                pm_quiz_id = _row_get(pm_quiz_row, 'id', 0)

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (pm_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (pm_quiz_id, q2_text, q2_options, q2_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (pm_quiz_id, q3_text, q3_options, q3_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (pm_lesson_id, quiz_title))
                pm_quiz_id = cur.lastrowid

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (pm_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (pm_quiz_id, q2_text, q2_options, q2_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (pm_quiz_id, q3_text, q3_options, q3_correct))
        else:
            print(f"Quiz '{quiz_title}' already exists.")

    # 15. Add a Quiz for "The Qubit: Superposition"
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("the-qubit-superposition",))
        qs_row = cur.fetchone()
        qs_lesson_id = _row_get(qs_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("the-qubit-superposition",))
        qs_row = cur.fetchone()
        qs_lesson_id = _row_get(qs_row, 'id', 0)

    if qs_lesson_id:
        quiz_title = "Bias Construction Check"
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (qs_lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (qs_lesson_id, quiz_title))

        existing_quiz = cur.fetchone()
        if not existing_quiz:
            q1_text = "For a state |ψ> = α|0> + β|1> with P(0) = 1/3 and P(1) = 2/3 (α, β real), what are the values of α and β?"
            q1_options = json.dumps([
                "α = 1/3, β = 2/3",
                "α = 1/√3, β = √(2/3)",
                "α = 0.33, β = 0.66",
                "α = 1/√2, β = 1/√2"
            ])
            q1_correct = 1

            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (qs_lesson_id, quiz_title))
                qs_quiz_row = cur.fetchone()
                qs_quiz_id = _row_get(qs_quiz_row, 'id', 0)

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (qs_quiz_id, q1_text, q1_options, q1_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (qs_lesson_id, quiz_title))
                qs_quiz_id = cur.lastrowid

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (qs_quiz_id, q1_text, q1_options, q1_correct))
        else:
            print(f"Quiz '{quiz_title}' already exists.")

    # CLEANUP: Remove quizzes that users requested to be deleted
    quizzes_to_remove = ["Linear Algebra Check", "Matrix Operation Check", "Eigenvalue Check"]
    for q_title in quizzes_to_remove:
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE title=%s", (q_title,))
            q_row = cur.fetchone()
            if q_row:
                q_id = _row_get(q_row, 'id', 0)
                cur.execute("DELETE FROM quiz_questions WHERE quiz_id=%s", (q_id,))
                cur.execute("DELETE FROM user_quiz_attempts WHERE quiz_id=%s", (q_id,))
                cur.execute("DELETE FROM quizzes WHERE id=%s", (q_id,))
                print(f"Removed quiz: {q_title}")
        else:
            cur.execute("SELECT id FROM quizzes WHERE title=?", (q_title,))
            q_row = cur.fetchone()
            if q_row:
                q_id = q_row[0]
                cur.execute("DELETE FROM quiz_questions WHERE quiz_id=?", (q_id,))
                cur.execute("DELETE FROM user_quiz_attempts WHERE quiz_id=?", (q_id,))
                cur.execute("DELETE FROM quizzes WHERE id=?", (q_id,))
                print(f"Removed quiz: {q_title}")

    conn.commit()
    conn.close()
    print("Database seeded successfully!")

if __name__ == "__main__":
    seed()
