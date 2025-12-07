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

    # CLEANUP: Remove misplaced Circuit Model lesson from Stage 2
    print("Cleaning up misplaced Circuit Model lesson...")
    if db_type == "postgres":
        cur.execute("SELECT id FROM courses WHERE slug=%s", ("stage-2-fundamentals",))
        c2_row = cur.fetchone()
        if c2_row:
            c2_id = _row_get(c2_row, 'id', 0)
            cur.execute("DELETE FROM lessons WHERE slug=%s AND course_id=%s", ("circuit-model-reading", c2_id))
            conn.commit()
    else:
        cur.execute("SELECT id FROM courses WHERE slug=?", ("stage-2-fundamentals",))
        c2_row = cur.fetchone()
        if c2_row:
            c2_id = c2_row[0]
            cur.execute("DELETE FROM lessons WHERE slug=? AND course_id=?", ("circuit-model-reading", c2_id))
            conn.commit()

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
                    "content": r"""
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
                    "content": r"""
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
                    "content": r"""
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
                    "content": r"""
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
                    "content": r"""
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
                    "content": r"""
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
                    "content": r"""
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
                    "content": r"""
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
                    "content": r"""
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
                    "slug": "gates-hadamard",
                    "title": "10. Gates: Hadamard",
                    "content": r"""
<h2>10. Gates: Hadamard</h2>
<p>The <strong>Hadamard Gate ($H$)</strong> is the indispensable single-qubit tool. It is the gate that generates balanced <strong>superposition</strong> and enables the ability to measure the qubit in a new basis, which is necessary for algorithms like the Quantum Fourier Transform.</p>

<h3>1. The Matrix and the Operation</h3>
<p>The Hadamard gate is a $2\times 2$ unitary matrix:</p>
$$H = \frac{1}{\sqrt{2}} \begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}$$
<p>Its action is to map the computational basis states ($|0\rangle, |1\rangle$) to the new basis states, often called the <strong>Hadamard Basis</strong> or the <strong>X-Basis</strong> states ($|+\rangle, |-\rangle$):</p>
$$\begin{array}{l} H|0\rangle = |+\rangle = \frac{1}{\sqrt{2}}|0\rangle + \frac{1}{\sqrt{2}}|1\rangle \\ H|1\rangle = |-\rangle = \frac{1}{\sqrt{2}}|0\rangle - \frac{1}{\sqrt{2}}|1\rangle \end{array}$$

<h3>2. Physical Significance: Basis Change</h3>
<p>On the Bloch sphere, the Hadamard gate represents a specific sequence of rotations (a $90^\circ$ rotation about the Y-axis followed by a $180^\circ$ rotation about the X-axis) that effectively swaps the Z-axis with the X-axis.</p>

<div style="text-align:center; margin:20px;">
  <img src="/static/images/bloch-sphere.png" alt="Bloch Sphere" style="max-width: 400px; border-radius: 8px;">
</div>

<ul>
  <li>When you apply $H$ to $|0\rangle$, the state vector moves from the North Pole (Z-axis) to the positive X-axis ($|+\rangle$).</li>
  <li>If you measure the state $|+\rangle$ in the Z-basis, the result is random (50/50).</li>
  <li>However, if you apply $H$ again, the state returns to $|0\rangle$. Now, if you measure, the result is deterministic ($100\%$ probability of $|0\rangle$).</li>
</ul>
<p>This ability to switch bases is what allows quantum computation to function. Interference effects (which rely on the relative phase $\phi$) are only visible when the state is measured in the correct basis.</p>

<h3>Your Task: Proving Reversibility</h3>
<p>Since $H$ is a valid quantum gate, it must be <strong>unitary</strong> (Postulate 2). The simplest way to show this is to prove that the gate is its own inverse, meaning applying it twice returns the original state.</p>
<p>Prove that:</p>
$$H^2 = I$$
<p>where $I = \begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix}$ is the Identity matrix.</p>
<p>Show the matrix multiplication $H \cdot H$ step-by-step.</p>
""",
                    "position": 10,
                    "task_json": None,
                    "section": "probability-theory"
                },
                {
                    "slug": "classical-logic-boolean",
                    "title": "11. Classical Logic: Boolean Algebra",
                    "content": r"""
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
                    "content": r"""
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
                    "content": r"""
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
                    "content": r"""
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
                    "content": r"""
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
                    "content": r"""
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
                    "content": r"""
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
                    "content": r"""
<h2>The Bloch Sphere</h2>
<p>The Bloch Sphere is not a physical object; it is the essential geometric visualization tool for the state space of a single qubit ($\mathbb{C}^2$). It ties together everything you’ve learned about normalization, superposition, and phase.</p>

<h3>1. The Mapping</h3>
<p>A state vector is a 2-dimensional complex vector, but the Bloch Sphere allows us to map it uniquely onto the surface of a 3-dimensional real sphere (the unit sphere).</p>
<ul>
    <li><strong>Poles (The Classical Basis):</strong> The North Pole is the state $|0\\rangle$. The South Pole is the state $|1\\rangle$.</li>
    <li><strong>Surface (Superposition):</strong> Every single point on the surface represents a valid pure superposition state $|\\psi\\rangle$.</li>
    <li><strong>Vector Length (Normalization):</strong> The vector from the center to any point on the surface has a length of 1, satisfying the normalization condition $\\langle \\psi | \\psi \\rangle = 1$.</li>
</ul>
<img src="/static/images/Sphere.jpeg" alt="Bloch Sphere" style="max-width:100%; margin: 20px 0;">

<h3>2. The Spherical Coordinates</h3>
<p>The position of any pure state $|\\psi\\rangle$ on the sphere is defined by two real angles, $\\theta$ (polar) and $\\phi$ (azimuthal), which directly map to probability and phase:</p>
$$|\\psi\\rangle = \\cos(\\frac{\\theta}{2})|0\\rangle + e^{i\\phi}\\sin(\\frac{\\theta}{2})|1\\rangle$$

<ul>
    <li><strong>Angle $\\theta$ (Polar, $0 \\le \\theta \\le \\pi$):</strong> This angle, measured from the Z-axis (North Pole), controls the probability bias.
    $$P(|0\\rangle) = \\cos^2(\\theta/2)$$
    $$P(|1\\rangle) = \\sin^2(\\theta/2)$$
    </li>
    <li><strong>Angle $\\phi$ (Azimuthal, $0 \\le \\phi < 2\\pi$):</strong> This angle, measured from the X-axis, controls the crucial relative phase $e^{i\\phi}$ between the $|0\\rangle$ and $|1\\rangle$ components.</li>
</ul>

<h3>3. Gates as Rotations</h3>
<p>Unitary gates (Postulate 2) are represented as rotations of the state vector on the sphere.</p>
<ul>
    <li>The <strong>Pauli-X</strong> gate is a $180^\\circ$ rotation about the X-axis.</li>
    <li>The <strong>Pauli-Z</strong> gate is a rotation about the Z-axis (changing $\\phi$).</li>
    <li>The <strong>Hadamard</strong> gate is a rotation that maps the Z-axis states ($|0\\rangle, |1\\rangle$) to the X-axis states ($|+\\rangle, |-\\rangle$).</li>
</ul>

<h3>Your Task: Mapping the Superposition</h3>
<p>The balanced superposition state $|+\\rangle$ is created by applying the Hadamard gate to $|0\\rangle$. Its vector form is:</p>
$$|+\\rangle = \\frac{1}{\\sqrt{2}}|0\\rangle + \\frac{1}{\\sqrt{2}}|1\\rangle$$
<p>Find the corresponding spherical coordinates $(\\theta, \\phi)$ for this state.</p>
<ul>
    <li><strong>Determine $\\theta$:</strong> What value for $\\theta$ makes $\\cos(\\theta/2) = 1/\\sqrt{2}$?</li>
    <li><strong>Determine $\\phi$:</strong> Since the coefficient of $|1\\rangle$ is real, what must the phase factor $e^{i\\phi}$ equal?</li>
</ul>
                    """,
                    "position": 5,
                    "task_json": json.dumps({
                        "description": "Create the |+> state by applying the Hadamard (H) gate to |0>.",
                        "criteria": "state_plus",
                        "qubits": 1
                    }),
                    "section": "the-qubit"
                },
                {
                    "slug": "multi-qubit-tensor-products",
                    "title": "6. Multi-Qubit: Tensor Products",
                    "content": r"""
<h2>The Tensor Product</h2>
<p>This is the mathematical machine that allows us to scale from one qubit to a million. It is the reason quantum simulation is so hard for classical computers.</p>

<h3>1. The Physics: Merging Universes</h3>
<p>When you have two separate classical coins, you describe them separately: "Coin A is Heads, Coin B is Tails."</p>
<p>In Quantum Mechanics, when you bring two systems together, they cease to be separate mathematical entities. They merge into a <strong>single, larger state vector</strong> residing in a larger Hilbert Space.</p>

<p>The tool we use to glue these spaces together is the <strong>Tensor Product</strong> (denoted by the symbol $\\otimes$).</p>

<p>If system A is in state $|\\psi\\rangle$ and system B is in state $|\\phi\\rangle$, the combined system is:</p>
$$|\\Psi_{AB}\\rangle = |\\psi\\rangle \\otimes |\\phi\\rangle$$

<h3>2. The Math: The Kronecker Product</h3>
<p>How do we actually calculate this? We use the Kronecker Product rule. It takes a vector of size $M$ and a vector of size $N$ and creates a new vector of size $M \\times N$.</p>

$$\\begin{pmatrix} a \\\\ b \\end{pmatrix} \\otimes \\begin{pmatrix} c \\\\ d \\end{pmatrix} = \\begin{pmatrix} a \\cdot \\begin{pmatrix} c \\\\ d \\end{pmatrix} \\\\ b \\cdot \\begin{pmatrix} c \\\\ d \\end{pmatrix} \\end{pmatrix} = \\begin{pmatrix} ac \\\\ ad \\\\ bc \\\\ bd \\end{pmatrix}$$

<h3>3. The New Basis (The Computational Basis)</h3>
<p>For two qubits, we tensor their individual basis states ($|0\\rangle, |1\\rangle$) to form the new <strong>4-dimensional</strong> basis for the combined system.</p>

<ul>
    <li>$|00\\rangle = |0\\rangle \\otimes |0\\rangle = \\begin{pmatrix} 1 \\\\ 0 \\end{pmatrix} \\otimes \\begin{pmatrix} 1 \\\\ 0 \\end{pmatrix} = \\begin{pmatrix} 1 \\\\ 0 \\\\ 0 \\\\ 0 \\end{pmatrix}$</li>
    <li>$|01\\rangle = |0\\rangle \\otimes |1\\rangle = \\begin{pmatrix} 1 \\\\ 0 \\end{pmatrix} \\otimes \\begin{pmatrix} 0 \\\\ 1 \\end{pmatrix} = \\begin{pmatrix} 0 \\\\ 1 \\\\ 0 \\\\ 0 \\end{pmatrix}$</li>
    <li>$|10\\rangle = |1\\rangle \\otimes |0\\rangle = \\begin{pmatrix} 0 \\\\ 1 \\end{pmatrix} \\otimes \\begin{pmatrix} 1 \\\\ 0 \\end{pmatrix} = \\begin{pmatrix} 0 \\\\ 0 \\\\ 1 \\\\ 0 \\end{pmatrix}$</li>
    <li>$|11\\rangle = |1\\rangle \\otimes |1\\rangle = \\begin{pmatrix} 0 \\\\ 1 \\end{pmatrix} \\otimes \\begin{pmatrix} 0 \\\\ 1 \\end{pmatrix} = \\begin{pmatrix} 0 \\\\ 0 \\\\ 0 \\\\ 1 \\end{pmatrix}$</li>
</ul>

<p>Notice the pattern? The vector has a $1$ in the position corresponding to the binary value (00 is index 0, 11 is index 3).</p>

<h3>Your Task: The Product State</h3>
<p>You have two qubits.</p>
<ul>
    <li><strong>Qubit 1</strong> is in state $|1\\rangle$.</li>
    <li><strong>Qubit 2</strong> is in the superposition state $|+\\rangle = \\frac{1}{\\sqrt{2}}\\begin{pmatrix} 1 \\\\ 1 \\end{pmatrix}$.</li>
</ul>

<p>Calculate the state vector of the combined system $|\\Psi\\rangle = |1\\rangle \\otimes |+\\rangle$.</p>
<ol>
    <li>Set up the tensor product of the column vectors.</li>
    <li>Perform the multiplication to find the resulting 4-element column vector.</li>
    <li>Rewrite this vector in Dirac notation (e.g., $\\alpha|00\\rangle + \\beta|01\\rangle...$).</li>
</ol>
<p><em>(Hint: You will see that only the bottom half of the vector is populated.)</em></p>
""",
                    "position": 6,
                    "task_json": json.dumps({
                        "description": "Create the state |1> ⊗ |+> (Qubit 0 in |1>, Qubit 1 in |+>).",
                        "criteria": "tensor_product_1_plus",
                        "qubits": 2
                    }),
                    "section": "multi-qubit-systems"
                },
                {
                    "slug": "multi-qubit-entanglement",
                    "title": "7. Multi-Qubit: Entanglement",
                    "content": r"""
<h2>Entanglement</h2>
<p>This is the point where your intuition will try to fail you. Do not let it.</p>

<p>You just learned about Tensor Products, which allow us to combine independent qubits into a larger system (e.g., $|\Psi\\rangle = |a\\rangle \\otimes |b\\rangle$).</p>

<p><strong>Entanglement</strong> is simply the realization that <strong>not all states in the larger system can be created this way.</strong></p>

<h3>1. The Definition: Product vs. Entangled</h3>
<p>In the 4-dimensional space of two qubits ($\mathbb{C}^4$), most vectors <strong>cannot</strong> be factored back into two smaller vectors.</p>

<ul>
    <li><strong>Product State:</strong> A state that can be written as $|\\psi\\rangle_1 \\otimes |\\phi\\rangle_2$. The qubits are independent. Measuring one tells you nothing about the other.</li>
    <li><strong>Entangled State:</strong> A state where <strong>no such factorization exists</strong>. The qubits have lost their individual identity. They are no longer "Qubit A" and "Qubit B"; they are a single system sharing a probability distribution.</li>
</ul>

<h3>2. The Bell State ($|\\Phi^+\\rangle$)</h3>
<p>The canonical example of entanglement is the <strong>Bell State</strong>:</p>

$$|\\Phi^+\\rangle = \\frac{1}{\\sqrt{2}} (|00\\rangle + |11\\rangle) = \\frac{1}{\\sqrt{2}} \\begin{pmatrix} 1 \\\\ 0 \\\\ 0 \\\\ 1 \\end{pmatrix}$$

<p>Look closely at this vector. It is a superposition of "Both Zero" and "Both One".</p>
<p>It contains <strong>zero</strong> probability for the states $|01\\rangle$ and $|10\\rangle$.</p>

<h3>3. The Consequence: Correlation</h3>
<p>If you measure the first qubit of the $|\\Phi^+\\rangle$ state:</p>
<ol>
    <li><strong>Randomness:</strong> You have a 50% chance of measuring $0$ and a 50% chance of measuring $1$.</li>
    <li><strong>Collapse:</strong>
        <ul>
            <li>If you measure <strong>0</strong>, the state collapses to $|00\\rangle$. The second qubit <em>instantly</em> becomes $|0\\rangle$.</li>
            <li>If you measure <strong>1</strong>, the state collapses to $|11\\rangle$. The second qubit <em>instantly</em> becomes $|1\\rangle$.</li>
        </ul>
    </li>
</ol>

<p>There is no time delay. There is no signal sent between them. The correlation is absolute. If you know one, you know the other.</p>

<hr>

<h3>Your Task: The Proof of Impossibility</h3>
<p>You need to prove to yourself that $|\\Phi^+\\rangle$ cannot be broken down.</p>

<p>Assume that $|\\Phi^+\\rangle$ <em>could</em> be written as a product of two independent qubits:</p>
$$(\\alpha|0\\rangle + \\beta|1\\rangle) \\otimes (\\gamma|0\\rangle + \\delta|1\\rangle) = \\frac{1}{\\sqrt{2}}|00\\rangle + \\frac{1}{\\sqrt{2}}|11\\rangle$$

<p>Expand the tensor product on the left:</p>
$$\\alpha\\gamma|00\\rangle + \\alpha\\delta|01\\rangle + \\beta\\gamma|10\\rangle + \\beta\\delta|11\\rangle$$

<p>Now, match the coefficients with the Bell State on the right:</p>
<ol>
    <li>$\\alpha\\gamma = \\frac{1}{\\sqrt{2}}$ (Must be non-zero)</li>
    <li>$\\beta\\delta = \\frac{1}{\\sqrt{2}}$ (Must be non-zero)</li>
    <li>$\\alpha\\delta = 0$ (Middle terms must vanish)</li>
    <li>$\\beta\\gamma = 0$ (Middle terms must vanish)</li>
</ol>

<p><strong>The Logic Puzzle:</strong></p>
<p>Look at equations 3 and 4. For $\\alpha\\delta$ to be 0, either $\\alpha$ or $\\delta$ must be 0.</p>
<ul>
    <li>If $\\alpha = 0$, then equation 1 ($\\alpha\\gamma$) becomes 0. <strong>Contradiction.</strong></li>
    <li>If $\\delta = 0$, then equation 2 ($\\beta\\delta$) becomes 0. <strong>Contradiction.</strong></li>
</ul>

<p><strong>Conclusion:</strong> The system of equations has <strong>no solution</strong>.</p>

<p><strong>Question for you:</strong><br>
Since you cannot describe the Bell State using individual qubit coefficients ($\\alpha, \\beta, \\gamma, \\delta$), what does this imply about the "state" of Qubit 1 before it is measured? Does Qubit 1 even <em>have</em> a state?</p>
                    """,
                    "position": 7,
                    "task_json": json.dumps({
                        "description": "Create a Bell Pair (|00> and |11> only). Use H on q0, then CNOT (q0 controls q1).",
                        "criteria": "bell_pair",
                        "qubits": 2
                    }),
                    "section": "multi-qubit-systems"
                },
                {
                    "slug": "multi-qubit-bell-states",
                    "title": "8. Multi-Qubit: The Bell States",
                    "content": r"""
<h2>The Bell States</h2>
<p>You have analyzed the concept of entanglement (the "what"). Now you need the <strong>toolkit</strong> (the "how"). The <strong>Bell States</strong> are not just random entangled vectors. They are the <strong>four specific, maximally entangled states</strong> that form a complete orthonormal basis for the two-qubit Hilbert space. Just as $|00\\rangle, |01\\rangle, |10\\rangle, |11\\rangle$ form the standard "Computational Basis," the four Bell states form the "Bell Basis."</p>

<h3>1. The Four Bell States</h3>
<p>These are the "North, South, East, and West" of the entangled world.</p>
<ol>
    <li><strong>$|\\Phi^+\\rangle$ (Phi-Plus):</strong> The standard Bell state. $$|\\Phi^+\\rangle = \\frac{|00\\rangle + |11\\rangle}{\\sqrt{2}}$$ <em>(Correlation: Same results. If you measure 0, they measure 0.)</em></li>
    <li><strong>$|\\Phi^-\\rangle$ (Phi-Minus):</strong> The phase-flipped version. $$|\\Phi^-\\rangle = \\frac{|00\\rangle - |11\\rangle}{\\sqrt{2}}$$ <em>(Correlation: Same results, but carries a phase difference).</em></li>
    <li><strong>$|\\Psi^+\\rangle$ (Psi-Plus):</strong> The "parity" flip. $$|\\Psi^+\\rangle = \\frac{|01\\rangle + |10\\rangle}{\\sqrt{2}}$$ <em>(Correlation: Opposite results. If you measure 0, they measure 1.)</em></li>
    <li><strong>$|\\Psi^-\\rangle$ (Psi-Minus):</strong> The "singlet" state (crucial in physics). $$|\\Psi^-\\rangle = \\frac{|01\\rangle - |10\\rangle}{\\sqrt{2}}$$ <em>(Correlation: Opposite results, with a phase difference).</em></li>
</ol>

<h3>2. The Circuit: How to Make Them</h3>
<p>You don't find these in nature; you build them. The recipe is universal for all quantum computers.</p>
<p><strong>The Ingredients:</strong></p>
<ol>
    <li>Two qubits.</li>
    <li>One <strong>Hadamard (H)</strong> gate.</li>
    <li>One <strong>CNOT</strong> gate.</li>
</ol>
<p><strong>The Process (to create $|\\Phi^+\\rangle$):</strong></p>
<ol>
    <li><strong>Start:</strong> Initialize both qubits to $|00\\rangle$ (Qubit A is left, Qubit B is right).</li>
    <li><strong>Superposition:</strong> Apply $H$ to <strong>Qubit A</strong>. $$|00\\rangle \\xrightarrow{H \\otimes I} \\frac{(|0\\rangle + |1\\rangle)}{\\sqrt{2}} \\otimes |0\\rangle = \\frac{|00\\rangle + |10\\rangle}{\\sqrt{2}}$$</li>
    <li><strong>Entanglement:</strong> Apply CNOT with <strong>Qubit A as Control</strong> and <strong>Qubit B as Target</strong>.
        <ul>
            <li>$|00\\rangle \\to |00\\rangle$ (Control is 0, do nothing).</li>
            <li>$|10\\rangle \\to |11\\rangle$ (Control is 1, flip target).</li>
            <li><strong>Result:</strong> $\\frac{|00\\rangle + |11\\rangle}{\\sqrt{2}}$</li>
        </ul>
    </li>
</ol>

<h3>3. Why This Matters: Change of Basis</h3>
<p>Because these four states form a valid <strong>Basis</strong>, you can measure a two-qubit system <em>in the Bell Basis</em>. This is the secret sauce behind <strong>Quantum Teleportation</strong> and <strong>Superdense Coding</strong>.</p>
<p>In Teleportation, you don't measure "0" or "1"; you measure "Which of the 4 Bell states are these two qubits in?" The answer tells you how to reconstruct the state on the other side of the universe.</p>

<hr>

<h3>Your Task: Deriving the "Singlet" ($|\\Psi^-\\rangle$)</h3>
<p>To master quantum circuits, you must be able to trace the state vector step-by-step. You want to generate the state $|\\Psi^-\\rangle = \\frac{|01\\rangle - |10\\rangle}{\\sqrt{2}}$.</p>

<p><strong>The Setup:</strong></p>
<ul>
    <li><strong>Input State:</strong> $|11\\rangle$ (Qubit A is 1, Qubit B is 1).</li>
    <li><strong>Gate Sequence:</strong> Apply $H$ to Qubit A, then apply CNOT (Control A, Target B).</li>
</ul>

<p><strong>Derive the final state:</strong></p>
<ol>
    <li><strong>After H on A:</strong> Apply the Hadamard to the first $|1\\rangle$. Recall that $H|1\\rangle = \\frac{|0\\rangle - |1\\rangle}{\\sqrt{2}}$. What is the combined 2-qubit state vector at this midpoint?</li>
    <li><strong>After CNOT:</strong> Take the result from step 1 and apply the CNOT logic. (Remember: flip the second bit <em>only</em> if the first bit is 1). Does your result match the definition of $|\\Psi^-\\rangle$ above?</li>
</ol>
                    """,
                    "position": 8,
                    "task_json": json.dumps({
                        "description": "Derive |Ψ-> from input state |11> using H on q0 then CNOT (q0 controls q1).",
                        "criteria": "singlet_state_derivation",
                        "qubits": 2
                    }),
                    "section": "multi-qubit-systems"
                },
                {
                    "slug": "quantum-gates-pauli",
                    "title": "9. Gates: Pauli Matrices",
                    "content": r"""
<h2>The Pauli Matrices</h2>
<p>The <strong>Pauli Matrices</strong> are the alphabet of single-qubit quantum operations. Any single-qubit gate you ever see is a function or rotation based on these three matrices and the Identity matrix ($I$). They are the simplest, non-trivial, $2 \\times 2$ <strong>Hermitian</strong> matrices (Postulate 3: they can act as observables) and they are <strong>unitary</strong> (Postulate 2: they are valid gates).</p>

<h3>1. The Pauli Group ($\\{I, X, Y, Z\\}$)</h3>
<table class="table table-bordered">
    <thead>
        <tr>
            <th>Gate</th>
            <th>Matrix ($\\sigma$)</th>
            <th>Description</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>I</strong></td>
            <td>$\\begin{pmatrix} 1 & 0 \\\\ 0 & 1 \\end{pmatrix}$</td>
            <td><strong>Identity:</strong> Do nothing.</td>
        </tr>
        <tr>
            <td><strong>$X$</strong> ($\\sigma_x$)</td>
            <td>$\\begin{pmatrix} 0 & 1 \\\\ 1 & 0 \\end{pmatrix}$</td>
            <td><strong>Bit-Flip (NOT):</strong> Flips $|0\\rangle \\leftrightarrow |1\\rangle$. (Rotation about X-axis).</td>
        </tr>
        <tr>
            <td><strong>$Z$</strong> ($\\sigma_z$)</td>
            <td>$\\begin{pmatrix} 1 & 0 \\\\ 0 & -1 \\end{pmatrix}$</td>
            <td><strong>Phase-Flip:</strong> Flips the phase of $|1\\rangle$. (Rotation about Z-axis).</td>
        </tr>
        <tr>
            <td><strong>$Y$</strong> ($\\sigma_y$)</td>
            <td>$\\begin{pmatrix} 0 & -i \\\\ i & 0 \\end{pmatrix}$</td>
            <td><strong>Bit & Phase Flip:</strong> Combination of $X$ and $Z$.</td>
        </tr>
    </tbody>
</table>

<h3>2. Physical and Mathematical Significance</h3>
<ul>
    <li><strong>Observables:</strong> Since they are Hermitian ($M = M^\\dagger$), they represent measurable physical properties (like spin).</li>
    <li><strong>Rotations:</strong> On the Bloch sphere (Postulate 2), $X, Y, Z$ are the axes of rotation. Applying any Pauli matrix is a $180^\\circ$ rotation about its respective axis.</li>
    <li><strong>Eigenstates:</strong> The eigenstates of $X$ ($|+\\rangle, |-\\rangle$) and $Y$ ($|i+\\rangle, |i-\\rangle$) form alternative measurement bases.</li>
</ul>

<h3>3. The Relationship: Anti-Commutation</h3>
<p>The Pauli matrices satisfy fundamental anti-commutation relations. For example:</p>
$$XY = -YX$$
<p>This means the order in which you apply the gates <em>absolutely</em> matters. Changing the order of two operations in a quantum circuit changes the physics, which is often crucial for algorithms.</p>

<hr>

<h3>Your Task: Analyzing Pauli-Y</h3>
<p>The Pauli-Y gate is the only one that explicitly contains the complex number $i$. This is where complex arithmetic is unavoidable. Apply the Pauli-Y gate to the computational basis state $|0\\rangle$:</p>
$$Y|0\\rangle = \\begin{pmatrix} 0 & -i \\\\ i & 0 \\end{pmatrix} \\begin{pmatrix} 1 \\\\ 0 \\end{pmatrix}$$
<ol>
    <li>What is the resulting column vector?</li>
    <li>Rewrite the result in Dirac notation (e.g., $\\alpha|0\\rangle + \\beta|1\\rangle$).</li>
    <li>Based on the final state, describe the physical effect of $Y|0\\rangle$ in terms of bit flip and phase shift.</li>
</ol>
                    """,
                    "position": 9,
                    "task_json": json.dumps({
                        "description": "Apply the Y gate to |0> and verify the result matches the mathematical prediction (i|1>).",
                        "criteria": "state_y_0",
                        "qubits": 1
                    }),
                    "section": "quantum-gates"
                },
                {
                    "slug": "quantum-gates-hadamard",
                    "title": "10. Gates: Hadamard",
                    "content": r"""<h2>10. Gates: Hadamard</h2>
<p>The <strong>Hadamard Gate ($H$)</strong> is the indispensable single-qubit tool. It is the gate that generates balanced <strong>superposition</strong> and enables the ability to measure the qubit in a new basis, which is necessary for algorithms like the Quantum Fourier Transform.</p>

<h3>1. The Matrix and the Operation</h3>
<p>The Hadamard gate is a $2\times 2$ unitary matrix:</p>
$$H = \frac{1}{\sqrt{2}} \begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}$$
<p>Its action is to map the computational basis states ($|0\rangle, |1\rangle$) to the new basis states, often called the <strong>Hadamard Basis</strong> or the <strong>X-Basis</strong> states ($|+\rangle, |-\rangle$):</p>
$$H|0\rangle = |+\rangle = \frac{|0\rangle + |1\rangle}{\sqrt{2}}$$
$$H|1\rangle = |-\rangle = \frac{|0\rangle - |1\rangle}{\sqrt{2}}$$

<h3>2. Physical Significance: Basis Change</h3>
<p>On the Bloch sphere, the Hadamard gate represents a specific sequence of rotations (a $90^\circ$ rotation about the Y-axis followed by a $180^\circ$ rotation about the X-axis) that effectively swaps the Z-axis with the X-axis.</p>

<div style="text-align:center; margin:20px;">
  <img src="/static/images/bloch-sphere.png" alt="Bloch Sphere" style="max-width: 400px; border-radius: 8px;">
</div>

<ul>
  <li>When you apply $H$ to $|0\rangle$, the state vector moves from the North Pole (Z-axis) to the positive X-axis ($|+\rangle$).</li>
  <li>If you measure the state $|+\rangle$ in the Z-basis, the result is random (50/50).</li>
  <li>However, if you apply $H$ again, the state returns to $|0\rangle$. Now, if you measure, the result is deterministic ($100\%$ probability of $|0\rangle$).</li>
</ul>
<p>This ability to switch bases is what allows quantum computation to function. Interference effects (which rely on the relative phase $\phi$) are only visible when the state is measured in the correct basis.</p>

<h3>Your Task: Proving Reversibility</h3>
<p>Since $H$ is a valid quantum gate, it must be <strong>unitary</strong> (Postulate 2). The simplest way to show this is to prove that the gate is its own inverse, meaning applying it twice returns the original state.</p>
<p>Prove that:</p>
$$H^2 = I$$
<p>where $I = \begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix}$ is the Identity matrix.</p>
<p>Show the matrix multiplication $H \cdot H$ step-by-step.</p>
""",
                    "position": 10,
                    "task_json": json.dumps({
                        "description": "Apply the Hadamard (H) gate to the |0> state to create the |+> superposition state.",
                        "criteria": "state_plus",
                        "qubits": 1
                    }),
                    "section": "quantum-gates"
                },
                {
                    "slug": "quantum-gates-cnot",
                    "title": "11. Gates: CNOT",
                    "content": r"""<h2>Controlled-NOT (CNOT)</h2>
<p>You have mastered the single-qubit rotations. Now you need the tool that links them.</p>
<p>The <strong>Controlled-NOT (CNOT)</strong> is the single most important multi-qubit gate, as it is the only non-local operation required to achieve <strong>universality</strong> in quantum computing.</p>

<h3>1. The Matrix and the Operation</h3>
<p>The CNOT gate acts on two qubits: a <strong>Control</strong> qubit and a <strong>Target</strong> qubit.</p>
<ul>
    <li><strong>The Rule:</strong> The state of the <strong>Target qubit is flipped (NOT)</strong> <em>if and only if</em> the <strong>Control qubit is $|1\rangle$</strong>. Otherwise, nothing happens.</li>
</ul>

<p><strong>The Matrix (Control Qubit 0, Target Qubit 1):</strong></p>
<p>The CNOT is a $4 \times 4$ unitary matrix:</p>
$$CNOT = \begin{pmatrix} 1 & 0 & 0 & 0 \\ 0 & 1 & 0 & 0 \\ 0 & 0 & 0 & 1 \\ 0 & 0 & 1 & 0 \end{pmatrix}$$
<p>The $2 \times 2$ blocks along the diagonal show the conditional action:</p>
<ul>
    <li>The upper-left $2 \times 2$ block is the <strong>Identity ($I$)</strong> matrix, acting when the Control is $|0\rangle$.</li>
    <li>The lower-right $2 \times 2$ block is the <strong>Pauli-X ($X$)</strong> matrix, acting when the Control is $|1\rangle$.</li>
</ul>
<p>This block structure is often written as:</p>
$$CNOT = |0\rangle \langle 0| \otimes I + |1\rangle \langle 1| \otimes X$$

<h3>2. Physical Significance: Creating Entanglement</h3>
<p>The CNOT gate is a <strong>reversible</strong> gate that acts on a specific basis. Crucially, when the Control qubit is in a <strong>superposition</strong> (e.g., $|+\rangle$), the CNOT links the two qubits' states, transforming a product state into an <strong>entangled state</strong>.</p>
<p>This ability to couple the computational basis with the NOT operation is what creates the non-local correlations of entanglement.</p>

<hr>

<h3>Your Task: Entanglement by CNOT</h3>
<p>As demonstrated when building the Bell states, the CNOT gate is the essential tool for linking the two qubits.</p>
<p>Start with the product state $|\psi\rangle$ where the Control qubit ($Q_0$) is in superposition and the Target qubit ($Q_1$) is $|0\rangle$:</p>
$$|\psi\rangle = |+\rangle \otimes |0\rangle = \frac{1}{\sqrt{2}}(|00\rangle + |10\rangle)$$
<p>Apply the $CNOT$ gate (Control $Q_0$, Target $Q_1$) to $|\psi\rangle$.</p>
<ol>
    <li>How does $CNOT$ transform the $|00\rangle$ component?</li>
    <li>How does $CNOT$ transform the $|10\rangle$ component?</li>
    <li>What is the resulting state vector in Dirac notation? (This should be one of the Bell states you previously derived.)</li>
</ol>
                    """,
                    "position": 11,
                    "task_json": json.dumps({
                        "description": "Create the Bell State |Φ+> = (|00> + |11>)/√2. Start with |00>, apply H to q0, then CNOT (q0 controls q1).",
                        "criteria": "bell_phi_plus",
                        "qubits": 2
                    }),
                    "section": "quantum-gates"
                },
                {
                    "slug": "quantum-gates-phase",
                    "title": "12. Gates: Phase Gates",
                    "content": r"""
<h2>Phase Gates</h2>
<p>Phase Gates are the family of single-qubit operations that directly manipulate the <strong>relative phase ($\phi$)</strong> of a superposition. This ability to precisely dial in phase is where <strong>quantum interference</strong> originates, making this family of gates indispensable.</p>

<h3>1. The General Phase Rotation ($R_z(\theta)$)</h3>
<p>Phase gates perform a rotation of the state vector around the <strong>Z-axis</strong> of the Bloch sphere.</p>
<p>The standard textbook matrix for a Z-axis rotation by an angle $\theta$ is:</p>
$$R_z(\theta) = \begin{pmatrix} e^{-i\theta/2} & 0 \\\\ 0 & e^{i\theta/2} \end{pmatrix}$$

<h4>⚛️ The Action</h4>
<p>On a general state $\alpha|0\rangle + \beta|1\rangle$, this acts as:</p>
$$R_z(\theta) (\alpha|0\rangle + \beta|1\rangle) = \alpha e^{-i\theta/2}|0\rangle + \beta e^{i\theta/2}|1\rangle.$$
<p>You can factor out the global phase $e^{-i\theta/2}$ (which has no physical effect) to see that only the <strong>relative phase</strong> between $|0\rangle$ and $|1\rangle$ changes by $\theta$:</p>
$$R_z(\theta) (\alpha|0\rangle + \beta|1\rangle) \sim \alpha|0\rangle + \beta e^{i\theta}|1\rangle.$$
<p>This phase-only change leaves the measurement probabilities of $|0\rangle$ and $|1\rangle$ unchanged (since $|e^{i\theta}|^2 = 1$).</p>

<hr>

<h3>2. The Standard Library: $S$ and $T$ Gates</h3>
<p>Most quantum hardware platforms implement the following fixed phase gates, as they are essential building blocks:</p>
<table>
<thead>
<tr>
<th style="text-align: center;">Gate</th>
<th style="text-align: center;">Name</th>
<th style="text-align: center;">Rotation $\theta$</th>
<th style="text-align: center;">Matrix</th>
<th style="text-align: center;">Significance</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: center;"><strong>Z</strong></td>
<td style="text-align: center;">Pauli-Z</td>
<td style="text-align: center;">$\pi$ ($180^\circ$)</td>
<td style="text-align: center;">$\begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}$</td>
<td style="text-align: center;">Flips sign of $|1\rangle$ coefficient.</td>
</tr>
<tr>
<td style="text-align: center;"><strong>S</strong></td>
<td style="text-align: center;">Phase Gate</td>
<td style="text-align: center;">$\pi/2$ ($90^\circ$)</td>
<td style="text-align: center;">$\begin{pmatrix} 1 & 0 \\ 0 & i \end{pmatrix}$</td>
<td style="text-align: center;">Applies a $90^\circ$ rotation about Z-axis.</td>
</tr>
<tr>
<td style="text-align: center;"><strong>T</strong></td>
<td style="text-align: center;">$\pi/8$ Gate</td>
<td style="text-align: center;">$\pi/4$ ($45^\circ$)</td>
<td style="text-align: center;">$\begin{pmatrix} 1 & 0 \\ 0 & e^{i\pi/4} \end{pmatrix}$</td>
<td style="text-align: center;">The smallest rotation, crucial for <strong>universality</strong>.</td>
</tr>
</tbody>
</table>

<h4>🔑 Universality</h4>
<p>The $H$ gate combined with an arbitrary phase gate like $R_z(\theta)$ (or even just the $T$ gate) is sufficient to perform <strong>any arbitrary single-qubit unitary operation</strong>. $H$ allows you to rotate between bases, and $R_z(\theta)$ allows you to perform any rotation angle required for the algorithm.</p>

<hr>

<h3>Your Task: Applying the Phase Shift</h3>
<p>The $S$ gate ($R_z(\pi/2)$) is often used to rotate states from the X-axis ($|+\rangle$) to the Y-axis ($|i+\rangle$) on the Bloch sphere.</p>
<p>Apply the $S$ gate to the $|+\rangle$ state:</p>
$$S|+\rangle = \frac{1}{\sqrt{2}} S(|0\rangle + |1\rangle)$$
<ol>
<li>Write the matrix multiplication to calculate the resulting column vector.</li>
<li>Rewrite the result in Dirac notation.</li>
<li>Does the coefficient of $|0\rangle$ change its magnitude or phase? Does the coefficient of $|1\rangle$ change its magnitude or phase?</li>
</ol>
                    """,
                    "position": 12,
                    "task_json": json.dumps({
                        "description": "Create the state |+i> = (|0> + i|1>)/√2. Start with |0>, create a superposition, then apply the S gate to rotate the phase by 90 degrees.",
                        "criteria": "phase_s_gate",
                        "qubits": 1
                    }),
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
                    "content": r"""
<h2>The Circuit Model & Reading Scores</h2>
<p>We are at the first stage of actually building algorithms: <strong>The Circuit Model</strong>. A quantum circuit is simply a sequence of unitary gates applied to an initial state, followed by <strong>measurement</strong>.</p>
<p>Your ability to read the output—the <strong>reading scores</strong>—is the final translation step from quantum probability to classical data.</p>

<h3>1. The Reality of Measurement (Shots)</h3>
<p>Due to <strong>Postulate 3 (Measurement)</strong>, the quantum computer does not give you the state vector $|\psi\rangle$. It collapses the vector to a classical bit string. This outcome is <strong>probabilistic</strong> unless the state is a pure basis state (like $|0\rangle$).</p>
<p>Therefore, to estimate the underlying probability distribution ($P(|x\rangle) = |\langle x | \psi \rangle|^2$), you must run the circuit many times. Each run is called a <strong>shot</strong>.</p>

<h3>2. The Output: The Histogram</h3>
<p>The output of a quantum computation is not a single number, but a <strong>histogram</strong> showing the count of each possible outcome over the total number of shots.</p>
<p>For an $N$-qubit system, there are $2^N$ possible outcomes (bit strings $|00\dots\rangle$ to $|11\dots\rangle$). The histogram gives you $C_x$ (the count for outcome $x$) for all $2^N$ outcomes.</p>
$$P_{estimated}(x) = \frac{C_x}{\text{Total Shots}}$$

<h3>3. The Objective: Expectation Value</h3>
<p>Recall the <strong>Expectation Value ($E[X]$)</strong> from our probability lesson. In practice, quantum algorithms are designed to bias the probability distribution so that the answer is highly likely to be the outcome with the highest count.</p>
<p>The goal of reading the scores is to use the experimental counts to calculate the <strong>physical observable</strong> being estimated by the algorithm (e.g., the energy level of a molecule, or the bias $\langle Z \rangle$).</p>
                    """,
                    "position": 1,
                    "task_json": json.dumps({
                        "description": "Create a superposition state (|0> + |1>)/√2 using the H gate. Run the simulation (which defaults to 1024 shots for measurement tasks) and observe the histogram results.",
                        "criteria": "state_plus",
                        "qubits": 1
                    }),
                    "section": "circuit-model"
                },
                {
                    "slug": "quantum-parallelism-deutsch-jozsa",
                    "title": "2. Parallelism: Deutsch-Jozsa",
                    "content": r"""
<h2>The Deutsch-Jozsa Algorithm</h2>
<p>You are now moving from the components to the system. The Deutsch-Jozsa (DJ) algorithm is the first demonstration of <strong>quantum parallelism</strong>—the ability of a quantum computer to evaluate a function for many inputs simultaneously.</p>

<h3>1. The Problem Definition</h3>
<p>The DJ algorithm solves a specific "black-box function" problem (known as an <strong>oracle problem</strong>). Given a function $f(x)$ that takes $N$ input bits and returns 1 output bit, we are promised that the function is either:</p>
<ol>
    <li><strong>Constant:</strong> $f(x)$ returns the same value (0 or 1) for all inputs $x$.</li>
    <li><strong>Balanced:</strong> $f(x)$ returns 0 for exactly half of the inputs and 1 for the other half.</li>
</ol>
<p>The challenge is to determine which category $f(x)$ belongs to.</p>

<h3>2. The Quantum Advantage: Exponential Speedup</h3>
<table>
  <thead>
    <tr>
      <th style="text-align: center;">Metric</th>
      <th style="text-align: center;">Classical Worst Case</th>
      <th style="text-align: center;">Quantum Solution</th>
      <th style="text-align: center;">Speedup</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="text-align: center;"><strong>Queries to $f(x)$</strong></td>
      <td style="text-align: center;">$2^{N-1} + 1$</td>
      <td style="text-align: center;"><strong>1</strong></td>
      <td style="text-align: center;"><strong>Exponential</strong></td>
    </tr>
  </tbody>
</table>
<ul>
    <li><strong>Classical Failure:</strong> To guarantee the answer classically, you must query more than half the possible inputs. For $N=10$ qubits, that's $513$ queries.</li>
    <li><strong>Quantum Success:</strong> DJ solves it in <strong>one single query</strong> to the function.</li>
</ul>

<h3>3. The Mechanism: Phase Kickback</h3>
<p>The speedup is achieved through two steps:</p>

<h4>A. Quantum Parallelism</h4>
<p>The circuit starts by applying a Hadamard gate to all $N$ input qubits, creating a uniform superposition over all $2^N$ possible inputs:</p>
$$|\psi_{in}\rangle = |+\rangle^{\otimes N} |-\rangle$$
$$|\psi_{in}\rangle = \frac{1}{\sqrt{2^N}} \sum_{x \in \{0, 1\}^N} |x\rangle \otimes |-\rangle$$
<p>When the oracle $U_f$ (the quantum black box) is applied, it computes $f(x)$ for <strong>every single input $x$ simultaneously</strong>.</p>

<h4>B. Phase Encoding (The Kickback)</h4>
<p>The crucial trick involves setting the auxiliary qubit to $|-\rangle$. When the oracle acts, it results in a sign change on the input register based on $f(x)$—a process called <strong>phase kickback</strong>:</p>
$$U_f |x\rangle |-\rangle = (-1)^{f(x)} |x\rangle |-\rangle$$
<p>The final state of the input register contains all the function information encoded in the phase:</p>
$$|\psi_{final}\rangle = \frac{1}{\sqrt{2^N}} \sum_{x} (-1)^{f(x)} |x\rangle$$

<h3>4. The Measurement</h3>
<p>The final state $|\psi_{final}\rangle$ is then passed through another layer of Hadamard gates. This acts as an interference mechanism:</p>
<ul>
    <li>If $f(x)$ is <strong>constant</strong>, the phases are all the same, leading to <strong>constructive interference</strong> in the $|0\dots0\rangle$ state.</li>
    <li>If $f(x)$ is <strong>balanced</strong>, the positive and negative phases cancel each other out, leading to <strong>destructive interference</strong> in the $|0\dots0\rangle$ state.</li>
</ul>

<hr>

<h3>Your Task: Interpreting the Result</h3>
<p>The final measurement of the input register determines the function type.</p>
<p>Below, you will find questions to test your understanding of these measurement outcomes.</p>
                    """,
                    "position": 2,
                    "task_json": json.dumps({
                        "description": "Prepare the input state for the Deutsch-Jozsa algorithm on 2 qubits. Qubit 0 (data) should be in superposition |+> (apply H) and Qubit 1 (aux) should be in state |-> (apply X then H).",
                        "criteria": "dj_prep",
                        "qubits": 2
                    }),
                    "section": "quantum-parallelism"
                },
                {
                    "slug": "amplitude-amplification-grover",
                    "title": "3. Amplification: Grover’s Algorithm",
                    "content": r"""
<h2>Grover’s Algorithm</h2>
<p>You have seen the power of quantum parallelism with DJ. Now you must master <strong>Amplitude Amplification</strong>—the core technique behind <strong>Grover's Algorithm</strong>. Grover's is the most powerful quantum algorithm to solve an <strong>unstructured search problem</strong>, providing a dramatic <strong>quadratic speedup</strong> over the best possible classical solution.</p>

<h3>1. The Problem: Unstructured Search</h3>
<p>Given a database or list of $N$ items where the items are <strong>unsorted</strong> (no index, no pattern), find the one item $x_w$ that satisfies a specific search condition (the "winner").</p>
<ul>
    <li><strong>Classical Time:</strong> Finding $x_w$ requires querying the list, on average, $N/2$ times. The complexity is linear: $O(N)$.</li>
    <li><strong>Quantum Time:</strong> Grover's algorithm finds $x_w$ in approximately $\frac{\pi}{4}\sqrt{N}$ queries. The complexity is $O(\sqrt{N})$.</li>
</ul>
<p>This is a polynomial speedup, not exponential, but for a large database (e.g., $N=10^{18}$), the difference is monumental.</p>

<h3>2. The Mechanism: Amplitude Amplification</h3>
<p>Grover's algorithm works by defining a 2D subspace spanned by the "winner" state $|x_w\rangle$ and the uniform superposition of the "non-winner" states. The process consists of two operations repeated iteratively:</p>

<h4>A. The Oracle ($U_w$)</h4>
<p>The quantum oracle, similar to DJ, <strong>marks</strong> the winning state $|x_w\rangle$ by flipping its phase. The goal is to identify this state by its sign change:</p>
$$U_w |x\rangle = (-1)^{f(x)} |x\rangle$$

<h4>B. The Diffusion Operator ($D$)</h4>
<p>This is the heart of the amplification. The diffusion operator $D$ performs an <strong>inversion about the mean</strong> of all amplitudes.</p>
<ol>
    <li>The marked state has a negative amplitude.</li>
    <li>The average amplitude $\langle A \rangle$ drops because of the negative contribution.</li>
    <li>The diffusion operator reflects the state vector around the mean, performing a rotation that effectively <strong>boosts the amplitude of the marked state above the mean</strong> and suppresses the amplitudes of all non-marked states.</li>
</ol>

<h3>3. The Process: Iterative Rotation</h3>
<p>The combination of the Oracle ($U_w$) and the Diffusion Operator ($D$) is called the <strong>Grover Iteration</strong> ($G = D U_w$). Each iteration is a single, identical rotation of the state vector toward the desired state $|x_w\rangle$. By applying $G$ for the correct number of times ($\approx \frac{\pi}{4}\sqrt{N}$), the probability of measuring the state $|x_w\rangle$ goes from $1/N$ to nearly $1$.</p>

<hr>

<h3>Your Task: The Cost of Over-Rotation</h3>
<p>Amplitude amplification relies on a very precise number of rotations.</p>
<ol>
    <li>If you run the Grover iteration <strong>too few</strong> times, what is the consequence for the final measurement result?</li>
    <li>If you run the Grover iteration <strong>too many</strong> times (e.g., $2 \times (\frac{\pi}{4}\sqrt{N})$), what happens to the amplitude of the marked state, and why is this disastrous for the algorithm?</li>
</ol>
                    """,
                    "position": 3,
                    "task_json": json.dumps({
                        "description": "Use Grover's Amplitude Amplification to find the state |11>. 1. Start with H on both. 2. Oracle: Mark |11> (use CZ). 3. Diffusion: Apply H, X, CZ, X, H to reflect about the mean.",
                        "criteria": "grover_search",
                        "qubits": 2
                    }),
                    "section": "amplitude-amplification"
                },
                {
                    "slug": "qft-phase-estimation",
                    "title": "4. QFT: Phase Estimation",
                    "content": r"""
<h2>Quantum Phase Estimation (QPE)</h2>
<p>You have seen how the Hadamard creates superposition and how the CNOT creates entanglement. The Quantum Phase Estimation (QPE) algorithm combines these tools with the Quantum Fourier Transform (QFT) to solve problems exponentially faster than any classical counterpart.</p>

<h3>1. The Problem: Finding the Phase $\phi$</h3>
<p>Given a unitary operator $U$ and one of its eigenvectors $|\psi\rangle$, we know that applying $U$ results in a phase factor $e^{2\pi i \phi}$:</p>
$$U|\psi\rangle = e^{2\pi i \phi}|\psi\rangle$$
<p>The goal of QPE is to determine the unknown phase $\phi \in [0, 1)$ with high precision. This phase is the key to solving complex problems like factoring and simulating physics.</p>

<h3>2. The Mechanism: Three Essential Steps</h3>
<p>The QPE circuit uses two registers: a Counting Register (to store the phase result) and a State Register (to hold the eigenvector $|\psi\rangle$).</p>

<h4>A. Preparation (Creating the Parallel Input)</h4>
<p>Hadamard gates are applied to all $t$ qubits in the counting register to create a uniform superposition:</p>
$$\frac{1}{\sqrt{2^t}} \sum_{j=0}^{2^t-1} |j\rangle$$

<h4>B. Controlled-Unitary Operations</h4>
<p>This is the heart of the algorithm. We apply a sequence of Controlled-$U^k$ gates. The $j^{th}$ control qubit controls the operation $U^{2^j}$.</p>
<p>The Controlled-$U^k$ operation uses the <strong>phase kickback</strong> mechanism (like in Deutsch-Jozsa) to imprint the phase $e^{2\pi i \phi}$ onto the counting register. By using exponentially increasing powers of $U$ ($U^1, U^2, U^4, \dots, U^{2^{t-1}}$), the phase information is encoded into the full $t$-bit resolution of the counting register.</p>

<h4>C. Inverse Quantum Fourier Transform ($\text{QFT}^\dagger$)</h4>
<p>The state of the counting register after step B is a complex superposition whose amplitudes are Fourier components of the phase information $\phi$. Applying the Inverse QFT transforms this complex encoding back into the simple computational basis.</p>
<p>The final state of the counting register is the binary approximation $|\tilde{\phi}\rangle$:</p>
$$|\tilde{\phi}\rangle \otimes |\psi\rangle$$
<p>Measurement of the counting register yields $\tilde{\phi}$.</p>

<div class="text-center my-4">
    <img src="/static/images/QFT.jpeg" class="img-fluid rounded shadow" alt="Quantum Fourier Transform and Phase Estimation" style="max-width: 600px;">
</div>

<h3>Your Task: The Necessity of Exponentiation</h3>
<p>The controlled operations are not just $C-U$ repeated $t$ times. They are $C-U^1, C-U^2, C-U^4, \dots, C-U^{2^{t-1}}$.</p>
<p>If the circuit used only $C-U$ gates (i.e., $C-U^1$ repeated $t$ times), the final measurement would only reveal the phase modulo $2\pi$. Why would this fail to distinguish between phases like $\phi=0.5$ and $\phi=0.0001$?</p>
<p>Explain the role of the final term, $C-U^{2^{t-1}}$, in the context of precision.</p>
""",
                    "position": 4,
                    "task_json": json.dumps({
                        "description": "Perform Phase Estimation on the Z gate. 1. Prepare eigenstate |1> on q1. 2. Create superposition on q0. 3. Apply Controlled-Z (kickback). 4. Apply Inverse QFT (H) on q0.",
                        "criteria": "qpe_z_gate",
                        "qubits": 2
                    }),
                    "section": "quantum-fourier-transform"
                },
                {
                    "slug": "qft-shors",
                    "title": "5. QFT: Shor’s Algorithm",
                    "content": r"""
<h2>Shor's Algorithm</h2>
<p>You have arrived at the reason most governments and banks fear quantum computing. <strong>Shor's Algorithm</strong> offers an exponential speedup for the one computational problem whose difficulty protects modern public-key cryptography (RSA): <strong>factoring large numbers</strong>.</p>

<h3>1. The Problem: Factoring</h3>
<p>Given a large composite integer $N$, find its prime factors $p$ and $q$ such that $N = p \times q$.</p>
<ul>
    <li><strong>Classical Time:</strong> The best classical algorithm (General Number Field Sieve) runs in sub-exponential time $O(e^{c \sqrt[3]{\log N}})$. This is too slow for numbers with hundreds of digits, making RSA secure.</li>
    <li><strong>Quantum Time:</strong> Shor's algorithm runs in polynomial time $O((\log N)^3)$. This is an <strong>exponential speedup</strong> that makes factoring large keys trivial.</li>
</ul>

<h3>2. The Insight: Reduction to Period Finding</h3>
<p>Shor's algorithm does not factor $N$ directly. Instead, it uses number theory to reduce the hard problem (factoring) to an equivalent, but structured, problem (<strong>period finding</strong>) that is solvable by QPE.</p>

<h4>A. Classical Reduction</h4>
<p>Using properties of modular arithmetic (specifically, picking a random number $a$ coprime to $N$), factoring $N$ can be reduced to finding the <strong>period $r$</strong> of the function:</p>
$$f(x) = a^x \pmod N$$
<p>The period $r$ is the smallest positive integer such that $a^r \equiv 1 \pmod N$. Once $r$ is found, the factors of $N$ can be calculated with high probability using simple classical operations (like $\text{gcd}(a^{r/2} \pm 1, N)$).</p>

<h4>B. The Quantum Solution (QPE)</h4>
<p>The quantum computer's job is solely to find the period $r$ using the <strong>Quantum Phase Estimation (QPE)</strong> primitive.</p>
<p>We define a unitary operator $U_a$:</p>
$$U_a|x\rangle = |ax \pmod N\rangle$$
<p>The period $r$ is deeply embedded within the eigenvalues of $U_a$. By finding the phase $\phi$ of the eigenvalues using <strong>QPE</strong>, we can extract the fraction $\frac{\text{integer}}{r}$.</p>
<p>The $\text{QFT}^\dagger$ outputs an approximation of $\frac{s}{r}$ (where $s$ is an integer).</p>

<h4>C. Classical Post-Processing</h4>
<p>The approximate fraction $\frac{s}{r}$ is measured. A final, simple classical algorithm called the <strong>Continued Fraction Algorithm</strong> is used to extract the denominator $r$ (the period) from the measured fraction.</p>

<h3>Your Task: The Necessity of Modular Arithmetic</h3>
<p>Shor's algorithm is a hybrid of classical math and quantum computation.</p>
<p>Why is it mathematically necessary to reduce the factoring problem (finding $p$ and $q$ of $N$) to the <strong>Period Finding Problem</strong> before applying the quantum step? (Hint: Think back to Postulate 2 and the requirements for QPE).</p>
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
                    "content": r"""
<h2>Decoherence: The Enemy</h2>
<p>You have moved from the theory of what quantum computers <em>can</em> do to the hard engineering problem of what they <em>must</em> overcome. <strong>Decoherence</strong> is the primary enemy of quantum computation.</p>

<h3>1. The Definition: Loss of Coherence</h3>
<p><strong>Decoherence</strong> is the process by which a quantum system loses its characteristic quantum properties—<strong>superposition</strong> and <strong>entanglement</strong>—due to unwanted interaction with its external environment.</p>
<p>It is the physical consequence of violating <strong>Postulate 2</strong>: the requirement that the quantum system must remain <strong>isolated and closed</strong>. In reality, no system is perfectly isolated. Any stray photon, thermal fluctuation, or magnetic field is the environment coupling to the qubit.</p>

<h3>2. The Cause: Uncontrolled Measurement</h3>
<p>The environmental interaction acts like an uncontrolled, continuous <strong>measurement</strong> (an uncontrolled application of Postulate 3). The environment "learns" something about the qubit's state, but because the environment is non-unitary and we can't observe it, the information is effectively lost.</p>
<p>This interaction forces the qubit's state vector $|\psi\rangle$ to evolve into a <strong>classical, mixed state</strong> (a probabilistic mixture) instead of evolving unitarily as a pure state.</p>

<h3>3. The Two Fundamental Quantum Errors</h3>
<p>Decoherence results in two primary types of errors that Quantum Error Correction (QEC) schemes are designed to detect and fix:</p>

<h4>A. Bit-Flip Error ($X$ Error)</h4>
<p>This is the quantum analog of a classical data flip: $|0\rangle \leftrightarrow |1\rangle$. This is caused by energy fluctuations (e.g., a thermal jump).</p>

<h4>B. Phase-Flip Error ($Z$ Error)</h4>
<p>This error is purely quantum. It flips the <strong>relative sign</strong> of the superposition:</p>
$$\alpha|0\rangle + \beta|1\rangle \to \alpha|0\rangle - \beta|1\rangle$$
<p>This destroys the interference pattern. A phase error is often caused by magnetic field fluctuations affecting the phase evolution.</p>

<div class="text-center my-4">
    <img src="/static/images/Decoherence.jpeg" class="img-fluid rounded shadow" alt="Quantum Decoherence" style="max-width: 600px;">
</div>

<hr>

<h3>Your Task: The Phase-Flip Trap</h3>
<p>Classical error correction codes (like Hamming codes) can easily detect a <strong>bit-flip error</strong> (0 becomes 1).</p>
<p>Explain why a <strong>Phase-Flip Error</strong> ($|\psi\rangle \to Z|\psi\rangle$) is fundamentally impossible to detect using only classical error correction techniques based on <strong>measuring the $|0\rangle/|1\rangle$ basis</strong>.</p>
<p>(Hint: What is the probability distribution $P(|0\rangle)$ and $P(|1\rangle)$ for the state $|\psi\rangle$ compared to the state $Z|\psi\rangle$?)</p>
""",
                    "position": 1,
                    "task_json": None,
                    "section": "quantum-error-correction"
                },
                {
                    "slug": "qec-surface-codes",
                    "title": "2. QEC: Surface Codes",
                    "content": r"""
<h2>Surface Codes & Fault Tolerance</h2>
<p>You have reached the bleeding edge. This is where the dream of quantum computing meets the nightmare of engineering reality.</p>
<p><strong>Surface Codes</strong> are currently the industry standard for Quantum Error Correction (QEC). Why? Because they are the only known architecture that balances high error tolerance with the physical constraints of building chips (connections are only required between nearest neighbors).</p>

<h3>1. The Fundamental Paradox</h3>
<p>Here is the problem you must solve: To fix an error, you must know what the error is. But if you measure a quantum state to find the error, <strong>you destroy the quantum state</strong> (Postulate 3).</p>
<p><strong>The Solution:</strong> You never look at the data qubits directly. You only look at the <strong>parity</strong> (correlations) between them. This is called <strong>Syndrome Measurement</strong>.</p>

<h3>2. The Architecture: The Checkerboard</h3>
<p>The Surface Code arranges qubits in a 2D lattice.</p>
<ul>
    <li><strong>Data Qubits:</strong> These hold the actual quantum information.</li>
    <li><strong>Ancilla (Measurement) Qubits:</strong> These are interspersed between the data qubits. Their <em>only</em> job is to constantly query their neighbors.</li>
</ul>

<div style="text-align: center; margin: 20px 0;">
    <div style="background-color: #f0f0f0; padding: 40px; border-radius: 8px; border: 2px dashed #ccc;">
        <p style="color: #666; font-style: italic;">[Interactive Surface Code Checkerboard Visualization]</p>
    </div>
</div>

<p>The ancilla qubits perform "stabilizer measurements."</p>
<ol>
    <li><strong>Z-Ancillas:</strong> Measure the parity of 4 surrounding data qubits to detect <strong>Bit-Flips (X errors)</strong>.</li>
    <li><strong>X-Ancillas:</strong> Measure the parity of 4 surrounding data qubits to detect <strong>Phase-Flips (Z errors)</strong>.</li>
</ol>

<h3>3. Topological Protection</h3>
<p>This is why it's called "Surface" code. The information isn't stored in a single particle; it is stored <strong>topologically</strong> across the entire grid (a "patch" of qubits).</p>
<ul>
    <li><strong>Logical "0" and "1":</strong> Defined by a chain of operators spanning the entire lattice from one boundary to another.</li>
    <li><strong>The Error Chain:</strong> When a physical error occurs, it flips a measurement outcome on the nearby ancilla. This creates a "defect" or "anyon" on the surface.</li>
    <li><strong>Correction:</strong> A classical decoding algorithm (running on a fast classical CPU) looks at these defects, matches them up, and applies a correction to neutralize the error chain.</li>
</ul>

<h3>4. The Cost: The "Physical-to-Logical" Ratio</h3>
<p>This is the brutal reality check for anyone optimistic about quantum timelines.</p>
<p>To build <strong>one</strong> perfect, error-corrected "Logical Qubit," you cannot just use one physical qubit. You need a massive patch of them to suppress the errors.</p>
<ul>
    <li><strong>Current Estimates:</strong> You need between <strong>1,000 and 10,000 physical qubits</strong> to build <strong>1 single logical qubit</strong>.</li>
    <li><strong>Implication:</strong> To run Shor's Algorithm (which needs ~4,000 logical qubits), you don't need a 4,000-qubit processor. You need a <strong>4 to 40 million</strong> qubit processor. We are currently at ~1,000 physical qubits.</li>
</ul>

<h3>Your Task: The Threshold Theorem</h3>
<p>The beauty of the Surface Code is the <strong>Threshold Theorem</strong>. It states that if the physical error rate ($p$) of your individual gates is below a specific constant ($p_{th} \approx 1\%$), you can make the logical error rate ($P_L$) arbitrarily low by increasing the size of the grid (distance $d$).</p>
<p><strong>Scenario:</strong> You have a quantum processor where the physical gate error rate is $p = 0.5\%$. The threshold for your surface code is $p_{th} = 1\%$.</p>
<ol>
    <li><strong>Case A:</strong> You build a small surface code grid ($d=3$). It has a certain logical error rate.</li>
    <li><strong>Case B:</strong> You decide to "upgrade" to a massive surface code grid ($d=9$).</li>
</ol>
<p><strong>Question:</strong> Does the logical error rate <strong>increase</strong> or <strong>decrease</strong> in Case B compared to Case A? <em>Conversely, what would happen if your physical error rate was $2\%$ (above the threshold)?</em></p>
""",
                    "position": 2,
                    "task_json": None,
                    "section": "quantum-error-correction"
                },
                {
                    "slug": "complexity-bqp",
                    "title": "3. Complexity: BQP vs P vs NP",
                    "content": r"""
<h2>Quantum Complexity Theory</h2>
<p>This is the reality check. If you tell a computer scientist "Quantum computers can solve NP-Complete problems," they will laugh you out of the room. You need to understand exactly where quantum computers fit in the hierarchy of computational hardness to avoid making embarrassing, hype-driven claims.</p>

<h3>1. The Cast of Characters</h3>
<ul>
    <li><strong>P (Polynomial Time):</strong> Problems a <strong>classical</strong> computer can solve efficiently (e.g., multiplication, sorting a list).</li>
    <li><strong>NP (Nondeterministic Polynomial Time):</strong> Problems where, if you are <em>given</em> the answer, a classical computer can <strong>verify</strong> it efficiently. (e.g., Sudoku, Factoring).
        <ul>
            <li><em>Note:</em> All <strong>P</strong> problems are also <strong>NP</strong> (if you can solve it, you can verify it).</li>
        </ul>
    </li>
    <li><strong>NP-Complete:</strong> The hardest problems in NP (e.g., The Traveling Salesman Problem). If you solve one of these efficiently, you solve <em>all</em> NP problems efficiently.</li>
</ul>

<h3>2. Enter BQP (Bounded-Error Quantum Polynomial Time)</h3>
<p><strong>BQP</strong> is the class of problems a <strong>quantum</strong> computer can solve efficiently (in polynomial time) with a probability of error $\le 1/3$.</p>
<p><strong>The Hierarchy:</strong></p>
<ol>
    <li><strong>P $\subseteq$ BQP:</strong> Anything a classical computer can do, a quantum computer can do (it can simulate classical logic).</li>
    <li><strong>BQP $\neq$ NP-Complete (Most Likely):</strong> Quantum computers are <strong>not</strong> magic machines that try every combination instantly. They require <strong>mathematical structure</strong> (like periodicity) to create interference. NP-Complete problems generally lack this structure.</li>
</ol>
<p><em>Brutal Truth:</em> We do not expect quantum computers to solve the Traveling Salesman Problem efficiently.</p>

<h3>3. The Sweet Spot: BQP, but not P</h3>
<p>The "Holy Grail" of quantum computing lies in the specific region where a problem is <strong>inside BQP</strong> (quantum solvable) but <strong>outside P</strong> (classically hard).</p>
<ul>
    <li><strong>Factoring (Shor's Algorithm):</strong> This is the poster child. It is in NP (easy to check: just multiply the factors). It is likely <em>not</em> in P (we haven't found a fast classical way). It <strong>is</strong> in BQP.</li>
    <li><strong>Simulation of Quantum Systems:</strong> Predicting chemical reactions or material properties. This is naturally in BQP but exponentially hard for P.</li>
</ul>

<h3>4. The Misconception: The "Brute Force" Myth</h3>
<p>You often hear: "A quantum computer checks all answers at once." <strong>False.</strong></p>
<p>While it creates a superposition of all answers, measuring it gives you a <strong>random</strong> answer. You need an algorithm (like Grover's) to amplify the right one.</p>
<ul>
    <li>Grover's Algorithm gives a <strong>Quadratic Speedup</strong> ($N \to \sqrt{N}$).</li>
    <li>To solve NP-Complete problems efficiently, you need an <strong>Exponential Speedup</strong> ($2^N \to N$).</li>
    <li>Therefore, for unstructured search problems, quantum computers provide a boost, but they do not break the complexity barrier.</li>
</ul>

<hr>

<h3>Your Task: Classifying the Threat</h3>
<p>You are a security analyst evaluating encryption algorithms.</p>
<ol>
    <li><strong>AES-256 (Symmetric Key):</strong> Security relies on the fact that you have to guess the key. There is no hidden mathematical "period" to exploit. The best attack is a search.
        <ul>
            <li><em>Which algorithm applies?</em> (Shor's or Grover's?)</li>
            <li><em>Is the speedup Exponential or Quadratic?</em></li>
        </ul>
    </li>
    <li><strong>RSA-2048 (Public Key):</strong> Security relies on the difficulty of factoring large numbers, which has a hidden periodic structure.
        <ul>
            <li><em>Which algorithm applies?</em></li>
            <li><em>Is the speedup Exponential or Quadratic?</em></li>
        </ul>
    </li>
</ol>
<p><em>Based on this, which encryption standard is effectively "dead" in a post-quantum world, and which one just needs a larger key size?</em></p>
                    """,
                    "position": 3,
                    "task_json": None,
                    "section": "quantum-complexity-theory"
                },
                {
                    "slug": "hardware-superconducting",
                    "title": "4. Hardware: Superconducting",
                    "content": r"""
<h2>Superconducting Qubits (Transmons)</h2>
<p>This is the leading candidate. When you see a "quantum computer" in the news—the golden chandeliers from IBM, Google, or Rigetti—you are looking at <strong>Superconducting Qubits</strong>.</p>
<p>These are not natural particles like atoms or electrons. They are <strong>artificial atoms</strong>: macroscopic electrical circuits printed on a silicon chip that behave quantum mechanically because they are cooled to near absolute zero ($~15 \text{ mK}$).</p>

<h3>1. The Harmonic Oscillator Problem</h3>
<p>To build a qubit, you need two isolated energy levels, $|0\rangle$ and $|1\rangle$.</p>
<p>A standard electrical circuit with a Capacitor ($C$) and an Inductor ($L$) creates an <strong>LC Oscillator</strong>.</p>
<p>Classically, the energy sloshes back and forth between the electric field of the capacitor and the magnetic field of the inductor. Quantum mechanically, this is a <strong>Quantum Harmonic Oscillator</strong>.</p>
<p>The energy levels are:</p>
$$E_n = \hbar \omega \left(n + \frac{1}{2}\right)$$
<p><strong>The Fatal Flaw:</strong> The levels are <strong>equally spaced</strong>. The energy gap between $|0\rangle \to |1\rangle$ is exactly the same as $|1\rangle \to |2\rangle$.</p>
$$\Delta E = E_1 - E_0 = E_2 - E_1 = \hbar \omega$$
<p>If you send a microwave pulse at frequency $\omega$ to flip the qubit from $|0\rangle$ to $|1\rangle$, you might accidentally push it up to $|2\rangle$, $|3\rangle$, and so on. You cannot isolate the qubit. It is uncontrollable.</p>

<h3>2. The Solution: The Josephson Junction</h3>
<p>To fix this, we need to make the circuit <strong>anharmonic</strong> (unevenly spaced). We need a non-linear inductor.</p>
<p>Enter the <strong>Josephson Junction (JJ)</strong>. It consists of two superconducting metals separated by a vanishingly thin insulating barrier.</p>
<ul>
    <li>Instead of the linear relationship of a normal inductor ($V = L \cdot dI/dt$), the supercurrent $I$ tunnels through the barrier: $I = I_c \sin(\delta)$.</li>
    <li>This changes the potential energy landscape from a Parabola (Harmonic) to a <strong>Cosine</strong> wave.</li>
</ul>

<p>Now, the energy levels get closer together as you go up.</p>
$$E_{1} - E_{0} \neq E_{2} - E_{1}$$
<p>This difference is called the <strong>Anharmonicity ($\alpha$)</strong>. It allows us to tune our microwave laser to exactly the $|0\rangle \to |1\rangle$ frequency without touching the $|1\rangle \to |2\rangle$ transition.</p>

<h3>3. The Transmon Design</h3>
<p>The most popular design today is the <strong>Transmon</strong> (Transmission Line Shunted Plasma Oscillation). It puts a large Capacitor in parallel with the Josephson Junction.</p>
<ul>
    <li><strong>Benefit:</strong> It dramatically reduces sensitivity to <strong>charge noise</strong> (electric field fluctuations), which was the killer of early superconducting qubits (Cooper Pair Boxes).</li>
    <li><strong>Trade-off:</strong> It reduces the anharmonicity ($\alpha$), meaning we have to be very precise with our control pulses to avoid leakage into higher states.</li>
</ul>

<hr>

<h3>Your Task: The Leakage Danger</h3>
<p>You are calibrating a Transmon qubit.</p>
<ul>
    <li>The transition frequency from $|0\rangle$ to $|1\rangle$ is $f_{01} = 5.0 \text{ GHz}$.</li>
    <li>The anharmonicity is $\alpha = -300 \text{ MHz}$. (This means the next gap is smaller by $300 \text{ MHz}$).</li>
</ul>
<ol>
    <li>Calculate the transition frequency for the "leakage" state, $f_{12}$ (the gap between $|1\rangle$ and $|2\rangle$).
        $$f_{12} = f_{01} + \alpha$$
    </li>
    <li><strong>The Engineering Constraint:</strong> You act on the qubit with a microwave pulse. In frequency space, a short pulse is "wide" (it covers a range of frequencies).
        If your control pulse has a bandwidth of $400 \text{ MHz}$ centered at $5.0 \text{ GHz}$, will you accidentally excite the $|1\rangle \to |2\rangle$ transition?
        <em>(Compare the pulse range to your answer in step 1).</em>
    </li>
</ol>
                    """,
                    "position": 4,
                    "task_json": None,
                    "section": "physical-implementations"
                },
                {
                    "slug": "hardware-ions-photonics",
                    "title": "5. Hardware: Ions & Photonics",
                    "content": r"""
<h2>Trapped Ions & Photonics</h2>
<p>You have reviewed the current leader (Superconducting). Now you must understand the two primary competitors. Trapped Ions offer the highest fidelity, and Photonics offers the greatest speed. Both pose distinct scaling challenges.</p>

<hr>

<h3>1. Trapped Ions (The Perfect Qubit)</h3>
<p>Trapped Ion systems use nature's qubits: individual atoms (ions) whose energy levels are fundamentally stable. They are the <strong>gold standard for qubit quality and fidelity</strong>.</p>

<h4>The Mechanism: Laser Control</h4>
<p>The qubit is encoded in the long-lived <strong>electronic energy levels</strong> of an ion (e.g., Ytterbium, Barium).</p>
<ul>
    <li><strong>Trapping:</strong> The ions are suspended in a high vacuum using electric fields generated by microscopic electrodes (the <strong>Paul Trap</strong>). This prevents physical contact and decoherence.</li>
    <li><strong>Initialization & Gates:</strong> Highly precise <strong>lasers</strong> are used to perform all operations:
        <ul>
            <li><strong>Initialization:</strong> Lasers cool the ions to near-motionless states.</li>
            <li><strong>Single-Qubit Gates:</strong> Lasers drive transitions between $|0\rangle$ and $|1\rangle$.</li>
            <li><strong>Two-Qubit Gates:</strong> Lasers couple the internal state of one ion to the <strong>collective motion</strong> (vibrational mode) shared by all ions, which then couples to the second ion. This mechanism allows <strong>all-to-all connectivity</strong>—any qubit can talk to any other qubit in the trap.</li>
        </ul>
    </li>
</ul>

<h4>The Trade-Offs (High Fidelity, Low Speed)</h4>
<table class="table table-bordered">
    <thead>
        <tr>
            <th>Metric</th>
            <th>Pro</th>
            <th>Con (The Scaling Hurdle)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>Fidelity</strong></td>
            <td><strong>Highest in the industry</strong> ($>99.9\%$). Long coherence times (minutes).</td>
            <td><strong>Slowest gate speed</strong> ($\approx 10$ milliseconds). Very slow circuit execution.</td>
        </tr>
        <tr>
            <td><strong>Connectivity</strong></td>
            <td><strong>All-to-all connectivity</strong> in a single trap.</td>
            <td><strong>Hard to scale</strong> past $\approx 50$ qubits in a single, stable chain.</td>
        </tr>
    </tbody>
</table>

<hr>

<h3>2. Photonics (The Speed Demon)</h3>
<p>Photonic quantum computing uses <strong>photons</strong> (particles of light) as qubits. This system operates at room temperature and at the speed of light, making it the fastest platform.</p>

<h4>The Mechanism: Integrated Optics</h4>
<p>The qubit state is typically encoded in the <strong>polarization</strong> (horizontal $|H\rangle=|0\rangle$ or vertical $|V\rangle=|1\rangle$) or the <strong>path</strong> of the single photon.</p>
<ul>
    <li><strong>Circuits:</strong> Operations are performed using standard optical components (lenses, mirrors, beam splitters), often integrated onto a silicon chip (integrated optics).</li>
    <li><strong>Single-Qubit Gates:</strong> Phase shifters and waveplates perform arbitrary single-qubit rotations.</li>
    <li><strong>Measurement:</strong> Detectors measure the final state.</li>
</ul>

<h4>The Trade-Offs (Fast but Probabilistic)</h4>
<table class="table table-bordered">
    <thead>
        <tr>
            <th>Metric</th>
            <th>Pro</th>
            <th>Con (The Reliability Hurdle)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>Speed</strong></td>
            <td><strong>Extremely Fast</strong> (operations at the speed of light). Room temperature operation.</td>
            <td><strong>No quantum memory.</strong> The qubit is lost once it moves past the detector.</td>
        </tr>
        <tr>
            <td><strong>Reliability</strong></td>
            <td><strong>Networking potential</strong> (can send qubits long distance).</td>
            <td><strong>Probabilistic two-qubit gates.</strong> Entangling gates often succeed less than $1\%$ of the time (using the required KLM protocol).</td>
        </tr>
    </tbody>
</table>

<hr>

<h3>Your Task: The Engineering Constraint</h3>
<p>Imagine you are designing a quantum algorithm.</p>
<ol>
    <li>If your algorithm requires extremely <strong>deep circuits</strong> (thousands of sequential gates), which hardware platform—<strong>Trapped Ions</strong> or <strong>Superconducting</strong> (which typically have $\sim 100 \text{ nanosecond}$ gate times)—will impose the greater time penalty and why?</li>
    <li>If your algorithm requires highly reliable, near-perfect entanglement between non-neighboring qubits, which platform—<strong>Trapped Ions</strong> or <strong>Photonics</strong>—provides a structural advantage?</li>
</ol>
                    """,
                    "position": 5,
                    "task_json": None,
                    "section": "physical-implementations"
                },
                {
                    "slug": "qml-vqe",
                    "title": "6. QML: VQE",
                    "content": r"""
<h2>Variational Quantum Eigensolvers (VQE)</h2>
<p>The Variational Quantum Eigensolver (<strong>VQE</strong>) is arguably the most promising <strong>near-term</strong> quantum algorithm. It is the flagship application of Quantum Machine Learning (QML), designed not for exponential speedup, but for <strong>pragmatism</strong> on current noisy hardware.</p>

<hr>

<h3>1. The Problem: The Ground State Energy ⚛️</h3>
<p>The primary goal of quantum chemistry is to calculate the <strong>ground state energy</strong> ($E_0$) of a molecule (e.g., the energy of the stable state of Lithium Hydride, $\text{LiH}$). This is required to predict chemical reaction rates, bond strengths, and material properties.</p>
<p>Classically, solving the <strong>Schrödinger Equation</strong> for large molecules is exponentially hard.</p>

<hr>

<h3>2. The Variational Principle (The Foundation)</h3>
<p>VQE is based entirely on the <strong>Variational Principle</strong> from quantum mechanics:</p>
<p>For any arbitrary normalized quantum state $|\psi\rangle$, the expectation value of the Hamiltonian $H$ is always <strong>greater than or equal to</strong> the true ground state energy $E_0$.</p>
$$E(\theta) = \frac{\langle \psi(\theta) | H | \psi(\theta) \rangle}{\langle \psi(\theta) | \psi(\theta) \rangle} \ge E_0$$
<p>The goal is to iteratively adjust the state $|\psi(\theta)\rangle$ until $E(\theta)$ converges to the minimum possible value, thereby finding $E_0$.</p>

<hr>

<h3>3. The Mechanism: The Hybrid Loop 🔄</h3>
<p>VQE is a <strong>hybrid quantum-classical algorithm</strong>. It intelligently splits the computational burden: the hard quantum evaluation happens on the QPU, and the optimization happens on the classical CPU.</p>

<ol>
    <li><strong>Classical Initialization:</strong> A classical computer selects initial parameters $\theta = (\theta_1, \theta_2, \dots)$ for the quantum circuit.</li>
    <li><strong>Quantum Evaluation (The Ansatz):</strong> The parameters $\theta$ are used to build and run a <strong>parameterized quantum circuit</strong> (the <strong>Ansatz</strong>), which prepares the trial state $|\psi(\theta)\rangle$. The QPU then measures the energy $E(\theta)$.
        <ul>
            <li><em>The Hamiltonian ($H$) is measured piece by piece via <strong>Expectation Value</strong> (Reading Scores).</em></li>
        </ul>
    </li>
    <li><strong>Classical Optimization:</strong> The classical CPU receives the measured energy $E(\theta)$. It uses a classical optimizer (e.g., gradient descent) to calculate new, better parameters $\theta'$ that minimize the energy.</li>
    <li><strong>Iteration:</strong> The new parameters $\theta'$ are sent back to the QPU, and the loop repeats until the energy converges to a stable minimum.</li>
</ol>

<hr>

<h3>4. Significance: The NISQ Advantage</h3>
<p>VQE is perfect for <strong>NISQ</strong> (Noisy Intermediate-Scale Quantum) devices because:</p>
<ul>
    <li><strong>Shallow Circuits:</strong> The Ansatz circuits are typically much shallower than those required for complex exponential-speedup algorithms (like Shor's). This limits the chance of <strong>decoherence</strong> destroying the computation.</li>
    <li><strong>Error Management:</strong> The classical optimizer can often adapt to and filter out some of the inherent noise and measurement error.</li>
</ul>

<hr>

<h3>Your Task: The Ansatz Trade-off</h3>
<p>The <strong>Ansatz</strong> ($|\psi(\theta)\rangle$) is the parameterized circuit designed to explore the possible state space of the molecule.</p>
<ol>
    <li>If the Ansatz is <strong>too simple</strong> (too shallow, too few parameters), what is the inevitable consequence for the final energy calculation $E(\theta)$?</li>
    <li>If the Ansatz is <strong>too complex</strong> (too deep, too many parameters), what is the inevitable consequence for both the <strong>quantum hardware</strong> and the <strong>classical optimizer</strong>?</li>
</ol>
                    """,
                    "position": 6,
                    "task_json": None,
                    "section": "quantum-machine-learning"
                },
                {
                    "slug": "qml-qaoa",
                    "title": "7. QML: QAOA",
                    "content": r"""
<h2>Quantum Approximate Optimization (QAOA)</h2>
<p>You are moving deeper into pragmatic NISQ (Noisy Intermediate-Scale Quantum) applications. The <strong>Quantum Approximate Optimization Algorithm (QAOA)</strong> is designed to tackle <strong>Combinatorial Optimization</strong>—finding the best discrete configuration—a class that includes many NP-hard problems.</p>

<h3>1. The Problem: Combinatorial Optimization</h3>
<p>QAOA aims to find a <strong>high-quality approximation</strong> of the optimal solution for problems like:</p>
<ul>
    <li><strong>Max-Cut:</strong> Dividing a network's nodes into two groups to maximize the number of connections between the groups.</li>
    <li><strong>Traveling Salesman Problem (TSP):</strong> Finding the shortest possible route that visits a list of cities and returns to the origin.</li>
    <li><strong>Scheduling/Logistics:</strong> Optimizing complex resource allocation.</li>
</ul>
<p>The core difficulty is that the possible number of configurations is often exponential ($2^N$), making classical brute-force impossible.</p>

<h3>2. The Mechanism: Alternating Unitaries 🔄</h3>
<p>Like VQE, QAOA is a <strong>hybrid quantum-classical algorithm</strong>. The quantum circuit (the Ansatz) is very specific, designed to explore the solution space by alternating two types of simple, parameterized unitary operations.</p>

<h4>A. The Cost Unitary ($U_C$)</h4>
<p>The Cost Unitary is based on the problem's cost Hamiltonian ($H_C$). It takes the current state and applies a phase shift proportional to how good that state is (how high the cost is):</p>
<p>$$U_C(\gamma) = e^{-i\gamma H_C}$$</p>
<p>This operator "marks" the good solutions by rotating their phase, similar to the oracle in Grover's algorithm. The parameter $\gamma$ controls the magnitude of the rotation.</p>

<h4>B. The Mixer Unitary ($U_B$)</h4>
<p>The Mixer Unitary (usually just a simple Pauli-X operation on all qubits) is responsible for <strong>driving the search</strong> and <strong>creating superposition</strong> to explore new states:</p>
<p>$$U_B(\beta) = e^{-i\beta H_B}$$</p>
<p>This introduces quantum fluctuations, allowing the system to jump out of local minima. The parameter $\beta$ controls the degree of mixing.</p>

<h3>3. The QAOA Loop</h3>
<p>The entire circuit (the <strong>Ansatz</strong>) is built by repeating the $U_C(\gamma_k) U_B(\beta_k)$ sequence $p$ times:</p>
<p>$$|\psi(\vec{\gamma}, \vec{\beta})\rangle = U_B(\beta_p) U_C(\gamma_p) \dots U_B(\beta_1) U_C(\gamma_1) |+\rangle^{\otimes n}$$</p>
<ol>
    <li><strong>Quantum Step:</strong> The QPU runs the parameterized circuit and measures the expectation value of the cost Hamiltonian: $F(\vec{\gamma}, \vec{\beta}) = \langle \psi | H_C | \psi \rangle$.</li>
    <li><strong>Classical Step:</strong> A classical optimizer (running on a CPU) receives the result $F$. It adjusts the parameters $\vec{\gamma}$ and $\vec{\beta}$ to find the maximum cost $F$ (the best approximation).</li>
    <li><strong>The Result:</strong> QAOA provides a solution with a provable approximation ratio for certain problems (e.g., $0.6924$ for Max-Cut with $p=1$), which improves as $p$ increases.</li>
</ol>

<hr>

<h3>Your Task: The Layer ($p$) Trade-off</h3>
<p>The variable $p$ represents the number of alternating layers in the QAOA circuit. This is the primary tuning knob for the algorithm's power and depth.</p>
<ol>
    <li>If the number of layers is set to $p=1$, the circuit is shallow and fast, but the search space exploration is limited. What is the consequence for the quality of the final solution?</li>
    <li>If the number of layers $p$ becomes very large, the circuit theoretically approaches the optimal solution. However, this dramatically increases the number of parameters the classical optimizer must tune ($2p$ total parameters). This leads to the problem known as <strong>"Barren Plateaus."</strong> Explain this consequence for the <strong>classical optimization step</strong> when $p$ is large.</li>
</ol>
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


    # 17. Add a Quiz for "Gates: Phase Gates"
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("quantum-gates-phase",))
        ph_row = cur.fetchone()
        ph_lesson_id = _row_get(ph_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("quantum-gates-phase",))
        ph_row = cur.fetchone()
        ph_lesson_id = _row_get(ph_row, 'id', 0)

    if ph_lesson_id:
        quiz_title = "Phase Gate Knowledge Check"
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (ph_lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (ph_lesson_id, quiz_title))
        
        existing_quiz = cur.fetchone()
        if not existing_quiz:
            # Q1
            q1_text = "The S gate applies a phase rotation of 90 degrees (π/2). If you apply the S gate twice (S^2), which gate is it equivalent to?"
            q1_options = json.dumps([
                "The Identity (I)",
                "The Pauli-Z (Z)",
                "The Pauli-X (X)",
                "The Hadamard (H)"
            ])
            q1_correct = 1
            
            # Q2
            q2_text = "If you start with the superposition |+> and apply the S gate, what is the resulting state?"
            q2_options = json.dumps([
                "|- > (Minus state)",
                "|1 > (One state)",
                "|+i> (or |R>: (|0> + i|1>)/√2)",
                "|0 > (Zero state)"
            ])
            q2_correct = 2
            
            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (ph_lesson_id, quiz_title))
                quiz_row = cur.fetchone()
                quiz_id = _row_get(quiz_row, 'id', 0)
                
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)", 
                    (quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)", 
                    (quiz_id, q2_text, q2_options, q2_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (ph_lesson_id, quiz_title))
                quiz_id = cur.lastrowid
                
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)", 
                    (quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)", 
                    (quiz_id, q2_text, q2_options, q2_correct))
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

    # 16. Add a Quiz for "The Qubit: The Bloch Sphere"
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("the-qubit-bloch-sphere",))
        bs_row = cur.fetchone()
        bs_lesson_id = _row_get(bs_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("the-qubit-bloch-sphere",))
        bs_row = cur.fetchone()
        bs_lesson_id = _row_get(bs_row, 'id', 0)

    if bs_lesson_id:
        quiz_title = "Bloch Sphere Coordinates"
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (bs_lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (bs_lesson_id, quiz_title))

        existing_quiz = cur.fetchone()
        if not existing_quiz:
            q1_text = "For the state |+> = 1/√2(|0> + |1>), what is the value of the polar angle θ on the Bloch Sphere?"
            q1_options = json.dumps([
                "0",
                "π (180°)",
                "π/2 (90°)",
                "π/4 (45°)"
            ])
            q1_correct = 2

            q2_text = "For the same state |+>, what is the value of the azimuthal angle φ?"
            q2_options = json.dumps([
                "0",
                "π",
                "π/2",
                "2π"
            ])
            q2_correct = 0

            q3_text = "What happens to the state vector on the Bloch Sphere when you apply a Z gate?"
            q3_options = json.dumps([
                "It rotates 180° around the X-axis",
                "It rotates around the Z-axis (changing φ)",
                "It moves to the North Pole",
                "It does nothing"
            ])
            q3_correct = 1

            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (bs_lesson_id, quiz_title))
                bs_quiz_row = cur.fetchone()
                bs_quiz_id = _row_get(bs_quiz_row, 'id', 0)

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (bs_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (bs_quiz_id, q2_text, q2_options, q2_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (bs_quiz_id, q3_text, q3_options, q3_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (bs_lesson_id, quiz_title))
                bs_quiz_id = cur.lastrowid

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (bs_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (bs_quiz_id, q2_text, q2_options, q2_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (bs_quiz_id, q3_text, q3_options, q3_correct))
        else:
            print(f"Quiz '{quiz_title}' already exists.")

    # 17. Add a Quiz for "Multi-Qubit: Tensor Products"
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("multi-qubit-tensor-products",))
        mq_row = cur.fetchone()
        mq_lesson_id = _row_get(mq_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("multi-qubit-tensor-products",))
        mq_row = cur.fetchone()
        mq_lesson_id = _row_get(mq_row, 'id', 0)

    if mq_lesson_id:
        quiz_title = "Tensor Product Calculation"
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (mq_lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (mq_lesson_id, quiz_title))

        existing_quiz = cur.fetchone()
        if not existing_quiz:
            q1_text = "What is the dimension of the combined Hilbert space for two qubits?"
            q1_options = json.dumps(["2", "4", "8", "It depends on the state"])
            q1_correct = 1

            q2_text = "Calculate the tensor product |1> ⊗ |+>."
            q2_options = json.dumps([
                "1/√2 (|00> + |01>)",
                "1/√2 (|10> + |11>)",
                "1/√2 (|01> + |11>)",
                "|11>"
            ])
            q2_correct = 1

            q3_text = "If |ψ> = [a, b] and |φ> = [c, d], what is the first element of |ψ> ⊗ |φ>?"
            q3_options = json.dumps(["ac", "ad", "bc", "bd"])
            q3_correct = 0

            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (mq_lesson_id, quiz_title))
                mq_quiz_row = cur.fetchone()
                mq_quiz_id = _row_get(mq_quiz_row, 'id', 0)
                
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (mq_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (mq_quiz_id, q2_text, q2_options, q2_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (mq_quiz_id, q3_text, q3_options, q3_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (mq_lesson_id, quiz_title))
                mq_quiz_id = cur.lastrowid
                
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (mq_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (mq_quiz_id, q2_text, q2_options, q2_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (mq_quiz_id, q3_text, q3_options, q3_correct))
        else:
            print(f"Quiz '{quiz_title}' already exists.")

    # 18. Add a Quiz for "Multi-Qubit: Entanglement"
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("multi-qubit-entanglement",))
        me_row = cur.fetchone()
        me_lesson_id = _row_get(me_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("multi-qubit-entanglement",))
        me_row = cur.fetchone()
        me_lesson_id = _row_get(me_row, 'id', 0)

    if me_lesson_id:
        quiz_title = "Entanglement & Bell States"
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (me_lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (me_lesson_id, quiz_title))

        existing_quiz = cur.fetchone()
        if not existing_quiz:
            q1_text = "What defines an Entangled State?"
            q1_options = json.dumps([
                "It is a product of two independent qubit states.",
                "It cannot be written as a tensor product of individual qubit states.",
                "It only happens when qubits are close together.",
                "It has zero energy."
            ])
            q1_correct = 1

            q2_text = "In the Bell State |Φ+> = (|00> + |11>)/√2, if you measure Qubit 1 and get '0', what is the state of Qubit 2?"
            q2_options = json.dumps([
                "|0> (100%)",
                "|1> (100%)",
                "Still in superposition |+>",
                "Random (50/50)"
            ])
            q2_correct = 0

            q3_text = "Why did the system of equations for factoring the Bell State fail (Proof of Impossibility)?"
            q3_options = json.dumps([
                "The math was too hard.",
                "We needed complex numbers.",
                "It led to a contradiction where non-zero terms were forced to be zero.",
                "The Bell State is not a valid quantum state."
            ])
            q3_correct = 2

            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (me_lesson_id, quiz_title))
                me_quiz_row = cur.fetchone()
                me_quiz_id = _row_get(me_quiz_row, 'id', 0)
                
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (me_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (me_quiz_id, q2_text, q2_options, q2_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (me_quiz_id, q3_text, q3_options, q3_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (me_lesson_id, quiz_title))
                me_quiz_id = cur.lastrowid
                
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (me_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (me_quiz_id, q2_text, q2_options, q2_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (me_quiz_id, q3_text, q3_options, q3_correct))
        else:
            print(f"Quiz '{quiz_title}' already exists.")

    # 19. Add a Quiz for "Multi-Qubit: The Bell States"
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("multi-qubit-bell-states",))
        mb_row = cur.fetchone()
        mb_lesson_id = _row_get(mb_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("multi-qubit-bell-states",))
        mb_row = cur.fetchone()
        mb_lesson_id = _row_get(mb_row, 'id', 0)

    if mb_lesson_id:
        quiz_title = "Bell Basis & Circuit Logic"
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (mb_lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (mb_lesson_id, quiz_title))

        existing_quiz = cur.fetchone()
        if not existing_quiz:
            q1_text = "Why do we use the Bell Basis instead of the computational basis (|00>, |01>, etc.)?"
            q1_options = json.dumps([
                "It is easier to measure physically.",
                "It describes entangled states, enabling protocols like Teleportation.",
                "It uses fewer qubits.",
                "It avoids using complex numbers."
            ])
            q1_correct = 1

            q2_text = "Which gate sequence creates the Bell State |Φ+> from |00>?"
            q2_options = json.dumps([
                "H on q0, then CNOT (q0→q1)",
                "X on q0, then H on q1",
                "CNOT (q0→q1), then H on q0",
                "H on both q0 and q1"
            ])
            q2_correct = 0

            q3_text = "What is the result of measuring the first qubit of a Bell State?"
            q3_options = json.dumps([
                "Always 0",
                "Always 1",
                "Random (50/50), but correlated with the second qubit",
                "It destroys the qubit"
            ])
            q3_correct = 2

            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (mb_lesson_id, quiz_title))
                mb_quiz_row = cur.fetchone()
                mb_quiz_id = _row_get(mb_quiz_row, 'id', 0)
                
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (mb_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (mb_quiz_id, q2_text, q2_options, q2_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (mb_quiz_id, q3_text, q3_options, q3_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (mb_lesson_id, quiz_title))
                mb_quiz_id = cur.lastrowid
                
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (mb_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (mb_quiz_id, q2_text, q2_options, q2_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (mb_quiz_id, q3_text, q3_options, q3_correct))
        else:
            print(f"Quiz '{quiz_title}' already exists.")

    # 20. Add a Quiz for "Gates: Pauli Matrices"
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("quantum-gates-pauli",))
        gp_row = cur.fetchone()
        gp_lesson_id = _row_get(gp_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("quantum-gates-pauli",))
        gp_row = cur.fetchone()
        gp_lesson_id = _row_get(gp_row, 'id', 0)

    if gp_lesson_id:
        quiz_title = "Pauli-Y Gate Analysis"
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (gp_lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (gp_lesson_id, quiz_title))

        existing_quiz = cur.fetchone()
        if not existing_quiz:
            q1_text = "Calculate Y|0>. What is the resulting column vector?"
            q1_options = json.dumps([
                "[0, i] (top: 0, bottom: i)",
                "[i, 0] (top: i, bottom: 0)",
                "[0, 1] (top: 0, bottom: 1)",
                "[1, 0] (top: 1, bottom: 0)"
            ])
            q1_correct = 0

            q2_text = "Rewrite the result in Dirac notation."
            q2_options = json.dumps([
                "i|1>",
                "-i|1>",
                "i|0>",
                "|1>"
            ])
            q2_correct = 0

            q3_text = "What is the physical effect of Y|0>?"
            q3_options = json.dumps([
                "Bit flip AND phase shift (factor of i)",
                "Bit flip only (|0> -> |1>)",
                "Phase flip only",
                "No change"
            ])
            q3_correct = 0

            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (gp_lesson_id, quiz_title))
                gp_quiz_row = cur.fetchone()
                gp_quiz_id = _row_get(gp_quiz_row, 'id', 0)
                
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (gp_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (gp_quiz_id, q2_text, q2_options, q2_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (gp_quiz_id, q3_text, q3_options, q3_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (gp_lesson_id, quiz_title))
                gp_quiz_id = cur.lastrowid
                
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (gp_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (gp_quiz_id, q2_text, q2_options, q2_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (gp_quiz_id, q3_text, q3_options, q3_correct))
        else:
            print(f"Quiz '{quiz_title}' already exists.")


    # 15. Add a sample Quiz for "Gates: Hadamard"
    # Find lesson id
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("quantum-gates-hadamard",))
        lesson_row = cur.fetchone()
        lesson_id = _row_get(lesson_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("quantum-gates-hadamard",))
        lesson_row = cur.fetchone()
        lesson_id = _row_get(lesson_row, 'id', 0)
        
    if lesson_id:
        quiz_title = "Hadamard Gate Check"
        # Check if quiz exists
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (lesson_id, quiz_title))
        
        existing_quiz = cur.fetchone()
        if not existing_quiz:
            question_text = "What happens if you apply the Hadamard gate twice to a qubit starting in state |0>?"
            # Options: 
            # 1. It becomes |1>
            # 2. It becomes |+> (Superposition)
            # 3. It returns to |0>
            # 4. It becomes |->
            options = json.dumps(["It becomes |1>", "It becomes |+>", "It returns to |0>", "It becomes |->"])
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

    
    # 16. Add a Quiz for "Gates: CNOT"
    # Find lesson id
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("quantum-gates-cnot",))
        lesson_row = cur.fetchone()
        lesson_id = _row_get(lesson_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("quantum-gates-cnot",))
        lesson_row = cur.fetchone()
        lesson_id = _row_get(lesson_row, 'id', 0)
        
    if lesson_id:
        quiz_title = "CNOT Gate Check"
        # Check if quiz exists
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (lesson_id, quiz_title))
        
        existing_quiz = cur.fetchone()
        if not existing_quiz:
            # Q1
            q1_text = "What condition must be met for the CNOT gate to flip the Target qubit?"
            q1_options = json.dumps([
                "The Control qubit must be |0>",
                "The Control qubit must be |1>",
                "The Target qubit must be |1>",
                "The Target qubit must be in superposition"
            ])
            q1_correct = 1
            
            # Q2
            q2_text = "If the Control qubit is in superposition (|+>), what happens to the two qubits after a CNOT?"
            q2_options = json.dumps([
                "They remain independent product states.",
                "They become entangled.",
                "The Target qubit is always flipped.",
                "The Control qubit collapses to |0> or |1>."
            ])
            q2_correct = 1
            
            # Q3
            q3_text = "What is the matrix representation of the CNOT gate?"
            q3_options = json.dumps([
                "A 2x2 matrix",
                "A 4x4 matrix where the bottom-right 2x2 block is X",
                "A 4x4 matrix where the top-left 2x2 block is X",
                "A 4x4 identity matrix"
            ])
            q3_correct = 1
            
            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (lesson_id, quiz_title))
                quiz_row = cur.fetchone()
                quiz_id = _row_get(quiz_row, 'id', 0)
                
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)", 
                    (quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)", 
                    (quiz_id, q2_text, q2_options, q2_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)", 
                    (quiz_id, q3_text, q3_options, q3_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (lesson_id, quiz_title))
                quiz_id = cur.lastrowid
                
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)", 
                    (quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)", 
                    (quiz_id, q2_text, q2_options, q2_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)", 
                    (quiz_id, q3_text, q3_options, q3_correct))
        else:
             print(f"Quiz '{quiz_title}' already exists.")


    # 21. Add a Quiz for "The Circuit Model: Reading Scores"
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("circuit-model-reading",))
        cm_row = cur.fetchone()
        cm_lesson_id = _row_get(cm_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("circuit-model-reading",))
        cm_row = cur.fetchone()
        cm_lesson_id = _row_get(cm_row, 'id', 0)

    if cm_lesson_id:
        quiz_title = "Circuit Model & Expectation Values"
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (cm_lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (cm_lesson_id, quiz_title))

        existing_quiz = cur.fetchone()
        if not existing_quiz:
            q1_text = "A two-qubit circuit is run for 4000 shots. The theoretical probabilities are P(00)=0.65, P(01)=0.15, P(10)=0.05, P(11)=0.15. What are the expected counts for |00> and |10>?"
            q1_options = json.dumps([
                "2600 and 200",
                "650 and 50",
                "2600 and 600",
                "200 and 2600"
            ])
            q1_correct = 0

            q2_text = "Using the same probabilities, what is the Expectation Value <Z1Z0> (Parity)? Recall: <Z1Z0> = P(00) + P(11) - P(01) - P(10)."
            q2_options = json.dumps([
                "0.60",
                "0.80",
                "1.00",
                "0.00"
            ])
            q2_correct = 0

            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (cm_lesson_id, quiz_title))
                cm_quiz_row = cur.fetchone()
                cm_quiz_id = _row_get(cm_quiz_row, 'id', 0)
                
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (cm_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (cm_quiz_id, q2_text, q2_options, q2_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (cm_lesson_id, quiz_title))
                cm_quiz_id = cur.lastrowid
                
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (cm_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (cm_quiz_id, q2_text, q2_options, q2_correct))
        else:
            print(f"Quiz '{quiz_title}' already exists.")


    # 18. Add a Quiz for "Deutsch-Jozsa Algorithm"
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("quantum-parallelism-deutsch-jozsa",))
        dj_row = cur.fetchone()
        dj_lesson_id = _row_get(dj_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("quantum-parallelism-deutsch-jozsa",))
        dj_row = cur.fetchone()
        dj_lesson_id = _row_get(dj_row, 'id', 0)

    if dj_lesson_id:
        quiz_title = "Deutsch-Jozsa Check"
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (dj_lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (dj_lesson_id, quiz_title))

        existing_quiz = cur.fetchone()
        if not existing_quiz:
            q1_text = "If the function f(x) is CONSTANT, what is the single, deterministic outcome you will measure on the input qubits?"
            q1_options = json.dumps([
                "|00...0>",
                "|11...1>",
                "A uniform superposition",
                "It is random"
            ])
            q1_correct = 0

            q2_text = "If the function f(x) is BALANCED, what is the probability of measuring the all-zero state |00...0>?"
            q2_options = json.dumps([
                "0",
                "0.5",
                "1",
                "1/2^N"
            ])
            q2_correct = 0

            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (dj_lesson_id, quiz_title))
                dj_quiz_row = cur.fetchone()
                dj_quiz_id = _row_get(dj_quiz_row, 'id', 0)
                
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (dj_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (dj_quiz_id, q2_text, q2_options, q2_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (dj_lesson_id, quiz_title))
                dj_quiz_id = cur.lastrowid
                
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (dj_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (dj_quiz_id, q2_text, q2_options, q2_correct))
        else:
            print(f"Quiz '{quiz_title}' already exists.")


    # 22. Add a Quiz for "Grover's Algorithm"
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("amplitude-amplification-grover",))
        gr_row = cur.fetchone()
        gr_lesson_id = _row_get(gr_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("amplitude-amplification-grover",))
        gr_row = cur.fetchone()
        gr_lesson_id = _row_get(gr_row, 'id', 0)

    if gr_lesson_id:
        quiz_title = "Grover's Algorithm Check"
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (gr_lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (gr_lesson_id, quiz_title))

        existing_quiz = cur.fetchone()
        if not existing_quiz:
            q1_text = "If you run the Grover iteration too few times, what is the consequence?"
            q1_options = json.dumps([
                "The quantum computer crashes.",
                "The probability of the correct answer is low, and you are likely to measure a random wrong answer.",
                "The state vector becomes all zeros.",
                "The answer is still guaranteed, but with lower precision."
            ])
            q1_correct = 1

            q2_text = "If you run the Grover iteration too many times (over-rotation), what happens?"
            q2_options = json.dumps([
                "The probability of the correct answer continues to increase towards 100%.",
                "The probability of the correct answer starts to decrease as the state vector rotates past the target.",
                "The system resets to the initial state.",
                "Nothing happens; the state stays stable."
            ])
            q2_correct = 1

            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (gr_lesson_id, quiz_title))
                gr_quiz_row = cur.fetchone()
                gr_quiz_id = _row_get(gr_quiz_row, 'id', 0)
                
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (gr_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (gr_quiz_id, q2_text, q2_options, q2_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (gr_lesson_id, quiz_title))
                gr_quiz_id = cur.lastrowid
                
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (gr_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (gr_quiz_id, q2_text, q2_options, q2_correct))
        else:
            print(f"Quiz '{quiz_title}' already exists.")


    # Add Quiz for "QFT: Phase Estimation"
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("qft-phase-estimation",))
        qpe_row = cur.fetchone()
        qpe_lesson_id = _row_get(qpe_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("qft-phase-estimation",))
        qpe_row = cur.fetchone()
        qpe_lesson_id = _row_get(qpe_row, 'id', 0)

    if qpe_lesson_id:
        quiz_title = "QPE Precision & Exponentiation"
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (qpe_lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (qpe_lesson_id, quiz_title))

        existing_quiz = cur.fetchone()
        if not existing_quiz:
            q1_text = "Why do we use controlled-U^(2^j) gates instead of just repeating controlled-U?"
            q1_options = json.dumps([
                "To save energy by running fewer gates.",
                "To encode phase information into higher bits for exponential precision.",
                "Because U is unstable and decays.",
                "To ensure the qubits remain entangled."
            ])
            q1_correct = 1

            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (qpe_lesson_id, quiz_title))
                qpe_quiz_row = cur.fetchone()
                qpe_quiz_id = _row_get(qpe_quiz_row, 'id', 0)

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (qpe_quiz_id, q1_text, q1_options, q1_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (qpe_lesson_id, quiz_title))
                qpe_quiz_id = cur.lastrowid

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (qpe_quiz_id, q1_text, q1_options, q1_correct))
        else:
            print(f"Quiz '{quiz_title}' already exists.")

    # Add Quiz for "QFT: Shor's Algorithm"
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("qft-shors",))
        shor_row = cur.fetchone()
        shor_lesson_id = _row_get(shor_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("qft-shors",))
        shor_row = cur.fetchone()
        shor_lesson_id = _row_get(shor_row, 'id', 0)

    if shor_lesson_id:
        quiz_title = "Shor's Algorithm Logic"
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (shor_lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (shor_lesson_id, quiz_title))

        existing_quiz = cur.fetchone()
        if not existing_quiz:
            q1_text = "Why must we reduce factoring to period finding (modular exponentiation) for the quantum step?"
            q1_options = json.dumps([
                "Because quantum computers can only solve problems involving periodicity.",
                "Because the modular exponentiation operation U|x> = |ax mod N> is Unitary (reversible), fitting the requirement for QPE.",
                "Because factoring N directly is impossible even for a quantum computer.",
                "Because classical computers cannot calculate the greatest common divisor (GCD)."
            ])
            q1_correct = 1

            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (shor_lesson_id, quiz_title))
                shor_quiz_row = cur.fetchone()
                shor_quiz_id = _row_get(shor_quiz_row, 'id', 0)

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (shor_quiz_id, q1_text, q1_options, q1_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (shor_lesson_id, quiz_title))
                shor_quiz_id = cur.lastrowid

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (shor_quiz_id, q1_text, q1_options, q1_correct))
        else:
            print(f"Quiz '{quiz_title}' already exists.")

    # Add Quiz for "QEC: Decoherence"
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("qec-decoherence",))
        decoherence_row = cur.fetchone()
        decoherence_lesson_id = _row_get(decoherence_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("qec-decoherence",))
        decoherence_row = cur.fetchone()
        decoherence_lesson_id = _row_get(decoherence_row, 'id', 0)

    if decoherence_lesson_id:
        quiz_title = "The Phase-Flip Trap"
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (decoherence_lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (decoherence_lesson_id, quiz_title))

        existing_quiz = cur.fetchone()
        if not existing_quiz:
            q1_text = "Why is a Phase-Flip Error (Z error) undetectable if you only measure in the computational basis (|0>, |1>)?"
            q1_options = json.dumps([
                "It changes the probability of measuring 0.",
                "It changes the probability of measuring 1.",
                "It only changes the relative phase, leaving the probabilities |α|^2 and |β|^2 unchanged.",
                "It causes the qubit to decay to |0> immediately."
            ])
            q1_correct = 2

            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (decoherence_lesson_id, quiz_title))
                decoherence_quiz_row = cur.fetchone()
                decoherence_quiz_id = _row_get(decoherence_quiz_row, 'id', 0)

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (decoherence_quiz_id, q1_text, q1_options, q1_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (decoherence_lesson_id, quiz_title))
                decoherence_quiz_id = cur.lastrowid

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (decoherence_quiz_id, q1_text, q1_options, q1_correct))
        else:
            print(f"Quiz '{quiz_title}' already exists.")

    # Add Quiz for "QEC: Surface Codes"
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("qec-surface-codes",))
        sc_row = cur.fetchone()
        sc_lesson_id = _row_get(sc_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("qec-surface-codes",))
        sc_row = cur.fetchone()
        sc_lesson_id = _row_get(sc_row, 'id', 0)

    if sc_lesson_id:
        quiz_title = "The Threshold Theorem"
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (sc_lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (sc_lesson_id, quiz_title))

        existing_quiz = cur.fetchone()
        if not existing_quiz:
            q1_text = "If your physical error rate (p=0.5%) is BELOW the threshold (pth=1%), what happens to the logical error rate as you increase the grid size (distance d)?"
            q1_options = json.dumps([
                "The logical error rate decreases exponentially (it gets better).",
                "The logical error rate increases (it gets worse because there are more components to fail).",
                "The logical error rate stays the same.",
                "The quantum computer explodes."
            ])
            q1_correct = 0

            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (sc_lesson_id, quiz_title))
                sc_quiz_row = cur.fetchone()
                sc_quiz_id = _row_get(sc_quiz_row, 'id', 0)

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (sc_quiz_id, q1_text, q1_options, q1_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (sc_lesson_id, quiz_title))
                sc_quiz_id = cur.lastrowid

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (sc_quiz_id, q1_text, q1_options, q1_correct))
        else:
            print(f"Quiz '{quiz_title}' already exists.")

    # Add Quiz for "Complexity: BQP vs P vs NP"
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("complexity-bqp",))
        bqp_row = cur.fetchone()
        bqp_lesson_id = _row_get(bqp_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("complexity-bqp",))
        bqp_row = cur.fetchone()
        bqp_lesson_id = _row_get(bqp_row, 'id', 0)

    if bqp_lesson_id:
        quiz_title = "Post-Quantum Security Check"
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (bqp_lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (bqp_lesson_id, quiz_title))

        existing_quiz = cur.fetchone()
        if not existing_quiz:
            q1_text = "Which encryption standard is considered effectively 'dead' (broken by exponential speedup) and which one just needs larger keys (weakened by quadratic speedup)?"
            q1_options = json.dumps([
                "RSA is dead (Shor's exp speedup); AES needs larger keys (Grover's quad speedup).",
                "AES is dead (Grover's exp speedup); RSA needs larger keys (Shor's quad speedup).",
                "Both are dead.",
                "Neither is affected."
            ])
            q1_correct = 0

            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (bqp_lesson_id, quiz_title))
                bqp_quiz_row = cur.fetchone()
                bqp_quiz_id = _row_get(bqp_quiz_row, 'id', 0)

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (bqp_quiz_id, q1_text, q1_options, q1_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (bqp_lesson_id, quiz_title))
                bqp_quiz_id = cur.lastrowid

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (bqp_quiz_id, q1_text, q1_options, q1_correct))
        else:
            print(f"Quiz '{quiz_title}' already exists.")

    # Add Quiz for "Hardware: Superconducting"
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("hardware-superconducting",))
        hw_row = cur.fetchone()
        hw_lesson_id = _row_get(hw_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("hardware-superconducting",))
        hw_row = cur.fetchone()
        hw_lesson_id = _row_get(hw_row, 'id', 0)

    if hw_lesson_id:
        quiz_title = "The Leakage Danger"
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (hw_lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (hw_lesson_id, quiz_title))

        existing_quiz = cur.fetchone()
        if not existing_quiz:
            q1_text = "Given f_01 = 5.0 GHz and anharmonicity alpha = -300 MHz, what is f_12? If a control pulse has a bandwidth of 400 MHz centered at 5.0 GHz, is there a risk of leakage?"
            q1_options = json.dumps([
                "f_12 = 5.3 GHz. No risk.",
                "f_12 = 4.7 GHz. No risk (strictly outside the 4.8-5.2 GHz range).",
                "f_12 = 4.7 GHz. Yes, risk exists (bandwidth > anharmonicity implies spectral overlap).",
                "f_12 = 5.0 GHz. Yes, risk is inevitable."
            ])
            q1_correct = 2

            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (hw_lesson_id, quiz_title))
                hw_quiz_row = cur.fetchone()
                hw_quiz_id = _row_get(hw_quiz_row, 'id', 0)

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (hw_quiz_id, q1_text, q1_options, q1_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (hw_lesson_id, quiz_title))
                hw_quiz_id = cur.lastrowid

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (hw_quiz_id, q1_text, q1_options, q1_correct))
        else:
            print(f"Quiz '{quiz_title}' already exists.")

    # Add Quiz for "Hardware: Ions & Photonics"
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("hardware-ions-photonics",))
        ions_row = cur.fetchone()
        ions_lesson_id = _row_get(ions_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("hardware-ions-photonics",))
        ions_row = cur.fetchone()
        ions_lesson_id = _row_get(ions_row, 'id', 0)

    if ions_lesson_id:
        quiz_title = "The Engineering Constraint"
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (ions_lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (ions_lesson_id, quiz_title))

        existing_quiz = cur.fetchone()
        if not existing_quiz:
            q1_text = "Your algorithm requires extremely deep circuits (thousands of sequential gates). Comparing Trapped Ions (gate time ~10ms) vs Superconducting (gate time ~100ns), which platform imposes the greater execution time penalty?"
            q1_options = json.dumps([
                "Superconducting (slower gates)",
                "Trapped Ions (slower gates)",
                "Both are equivalent",
                "Photonics (fastest)"
            ])
            q1_correct = 1
            
            q2_text = "You need highly reliable, near-perfect entanglement between non-neighboring qubits. Which platform offers 'all-to-all' connectivity natively?"
            q2_options = json.dumps([
                "Superconducting (Transmons)",
                "Photonics (Integrated Optics)",
                "Trapped Ions (Paul Trap)",
                "Neutral Atoms"
            ])
            q2_correct = 2

            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (ions_lesson_id, quiz_title))
                ions_quiz_row = cur.fetchone()
                ions_quiz_id = _row_get(ions_quiz_row, 'id', 0)

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (ions_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (ions_quiz_id, q2_text, q2_options, q2_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (ions_lesson_id, quiz_title))
                ions_quiz_id = cur.lastrowid

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (ions_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (ions_quiz_id, q2_text, q2_options, q2_correct))
        else:
            print(f"Quiz '{quiz_title}' already exists.")

    # Add Quiz for "QML: VQE"
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("qml-vqe",))
        vqe_row = cur.fetchone()
        vqe_lesson_id = _row_get(vqe_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("qml-vqe",))
        vqe_row = cur.fetchone()
        vqe_lesson_id = _row_get(vqe_row, 'id', 0)

    if vqe_lesson_id:
        quiz_title = "The Ansatz Trade-off"
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (vqe_lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (vqe_lesson_id, quiz_title))

        existing_quiz = cur.fetchone()
        if not existing_quiz:
            q1_text = "If the VQE Ansatz is too simple (shallow, few parameters), what is the inevitable consequence?"
            q1_options = json.dumps([
                "It will be too slow to execute on the QPU.",
                "It cannot reach the true ground state energy (Underfitting).",
                "The classical optimizer will diverge.",
                "It will cause excessive decoherence."
            ])
            q1_correct = 1
            
            q2_text = "If the VQE Ansatz is too complex (deep, many parameters), what are the consequences?"
            q2_options = json.dumps([
                "The QPU suffers from decoherence/noise (Barren Plateaus) AND the classical optimizer struggles to converge.",
                "It guarantees finding the exact ground state quickly.",
                "It requires less classical memory.",
                "The energy calculation becomes perfectly accurate."
            ])
            q2_correct = 0

            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (vqe_lesson_id, quiz_title))
                vqe_quiz_row = cur.fetchone()
                vqe_quiz_id = _row_get(vqe_quiz_row, 'id', 0)

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (vqe_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (vqe_quiz_id, q2_text, q2_options, q2_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (vqe_lesson_id, quiz_title))
                vqe_quiz_id = cur.lastrowid

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (vqe_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (vqe_quiz_id, q2_text, q2_options, q2_correct))
        else:
            print(f"Quiz '{quiz_title}' already exists.")

    # Add Quiz for "QML: QAOA"
    if db_type == "postgres":
        cur.execute("SELECT id FROM lessons WHERE slug=%s", ("qml-qaoa",))
        qaoa_row = cur.fetchone()
        qaoa_lesson_id = _row_get(qaoa_row, 'id', 0)
    else:
        cur.execute("SELECT id FROM lessons WHERE slug=?", ("qml-qaoa",))
        qaoa_row = cur.fetchone()
        qaoa_lesson_id = _row_get(qaoa_row, 'id', 0)

    if qaoa_lesson_id:
        quiz_title = "The Layer (p) Trade-off"
        if db_type == "postgres":
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=%s AND title=%s", (qaoa_lesson_id, quiz_title))
        else:
            cur.execute("SELECT id FROM quizzes WHERE lesson_id=? AND title=?", (qaoa_lesson_id, quiz_title))

        existing_quiz = cur.fetchone()
        if not existing_quiz:
            q1_text = "If the number of layers is set to p=1, what is the consequence for the quality of the final solution?"
            q1_options = json.dumps([
                "It will be the optimal solution.",
                "It will be a low-quality approximation due to limited search space exploration.",
                "It will be too slow to execute on the QPU.",
                "It will cause excessive decoherence."
            ])
            q1_correct = 1
            
            q2_text = "If the number of layers p becomes very large, what is the consequence of barren plateaus for the classical optimization step?"
            q2_options = json.dumps([
                "The classical optimizer will converge faster.",
                "The classical optimizer will struggle to find meaningful parameter updates due to vanishing gradients.",
                "The quantum circuit will run more efficiently.",
                "The solution quality will decrease."
            ])
            q2_correct = 1

            if db_type == "postgres":
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(%s, %s) RETURNING id", (qaoa_lesson_id, quiz_title))
                qaoa_quiz_row = cur.fetchone()
                qaoa_quiz_id = _row_get(qaoa_quiz_row, 'id', 0)

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (qaoa_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(%s, %s, %s, %s)",
                            (qaoa_quiz_id, q2_text, q2_options, q2_correct))
            else:
                cur.execute("INSERT INTO quizzes(lesson_id, title) VALUES(?, ?)", (qaoa_lesson_id, quiz_title))
                qaoa_quiz_id = cur.lastrowid

                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (qaoa_quiz_id, q1_text, q1_options, q1_correct))
                cur.execute("INSERT INTO quiz_questions(quiz_id, question_text, options_json, correct_option_index) VALUES(?, ?, ?, ?)",
                            (qaoa_quiz_id, q2_text, q2_options, q2_correct))
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
