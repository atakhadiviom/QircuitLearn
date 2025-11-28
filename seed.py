import sqlite3
import os

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

    # 1. Insert Course
    course_title = "Quantum Computing: The No-Nonsense Guide"
    course_slug = "quantum-no-nonsense"
    description = "A concept-first approach to understanding why quantum computing matters, without drowning in math."
    
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
        cur.execute("INSERT INTO courses(slug, title, description) VALUES(?, ?, ?)", (course_slug, course_title, description))
        course_id = cur.lastrowid
    
    # 2. Define Lessons
    lessons = [
        # --- Phase 1: The Wall (Why We Need This) ---
        {
            "slug": "impossible-dinner-party",
            "title": "1. The Impossible Dinner Party",
            "content": """
<h2>Combinatorial Explosion</h2>
<p>Imagine you have to seat 100 people at a wedding so that no enemies sit together. It sounds simple, right?</p>
<p>But for a classical computer, this is a nightmare. It has to check every single combination one by one to see if it works. For 100 guests, the number of combinations is greater than the number of atoms in the universe.</p>
<p><strong>The Takeaway:</strong> Classical computers choke on problems with too many variables. They don't "think"; they just count very fast. If the number of possibilities is too huge, even the fastest supercomputer will take longer than the age of the universe to solve it.</p>
            """,
            "position": 1
        },
        {
            "slug": "bits-are-boring",
            "title": "2. Bits are Boring (The Light Switch)",
            "content": """
<h2>Binary Code (0s and 1s)</h2>
<p>A classical bit is like a light switch. It is either <strong>ON</strong> or <strong>OFF</strong>. You can't be "kind of" on.</p>
<p>This binary nature is rigid. It's great for arithmetic and logic, but it's inefficient for mimicking nature, which is fluid and complex.</p>
<p><strong>The Takeaway:</strong> We need a computer that behaves like nature, not like a switch. To simulate the real world—molecules, fluids, financial markets—we need a system that can handle nuance and uncertainty natively.</p>
            """,
            "position": 2
        },

        # --- Phase 2: The Quantum Weirdness (Core Mechanics) ---
        {
            "slug": "spinning-coin",
            "title": "3. The Spinning Coin (Superposition)",
            "content": """
<h2>Superposition</h2>
<p>Let's upgrade our analogy.</p>
<ul>
    <li><strong>Classical Bit:</strong> A coin flat on the table. It is definitely <strong>Heads</strong> OR <strong>Tails</strong>.</li>
    <li><strong>Qubit:</strong> A coin <em>spinning</em> on the table. Is it Heads or Tails? It’s <strong>both and neither</strong> at the same time.</li>
</ul>
<p>This state is called <strong>Superposition</strong>. The coin keeps spinning until you slap your hand down on it—this is <strong>measurement</strong>. Only then does it force itself to be Heads or Tails.</p>
<p><strong>The Takeaway:</strong> A quantum computer calculates with the "spinning" coin, allowing it to hold multiple possibilities at once. Instead of being just a 0 or a 1, a qubit can explore a complex combination of both.</p>
<p><strong>Interactive Task:</strong> Drag an <strong>H</strong> (Hadamard) gate to the circuit and run it. You'll see a 50/50 chance of measuring 0 or 1. That's the spinning coin!</p>
            """,
            "position": 3
        },
        {
            "slug": "spooky-connection",
            "title": "4. The Spooky Connection (Entanglement)",
            "content": """
<h2>Entanglement</h2>
<p>Imagine you have two dice. You throw one in New York and one in Tokyo.</p>
<p>If they are <strong>entangled</strong>, every time the New York die lands on 6, the Tokyo die <em>instantly</em> lands on 6. No signal is sent. They just know.</p>
<p>This phenomenon confused even Einstein, who called it "spooky action at a distance."</p>
<p><strong>The Takeaway:</strong> Entanglement allows quantum computers to link qubits together so they work as a massive, unified brain rather than isolated bits. Changing one qubit instantly affects its partner, no matter the distance.</p>
<p><strong>Interactive Task:</strong> Create a Bell Pair. Use an <strong>H</strong> gate on q0, then a <strong>CNOT</strong> gate (control q0, target q1). Measure both. They will always match!</p>
            """,
            "position": 4
        },

        # --- Phase 3: The "Quantum Speedup" (How It Works) ---
        {
            "slug": "maze-vs-god-view",
            "title": "5. The Maze vs. The God’s Eye View",
            "content": """
<h2>Parallelism & Interference</h2>
<p>How does a quantum computer solve problems faster? It's not about speed; it's about the path.</p>
<ul>
    <li><strong>Classical Computer:</strong> A mouse in a maze. It hits a wall, turns back, tries a new path. It tries every path one by one until it finds the cheese.</li>
    <li><strong>Quantum Computer:</strong> You pour water into the maze. The water goes down <em>all paths at once</em>. It doesn't "try" them; it flows through them simultaneously to find the exit.</li>
</ul>
<p><strong>The Takeaway:</strong> Quantum computers don't do steps faster; they take fewer steps. They use the properties of waves (interference) to cancel out wrong answers and amplify the correct one.</p>
            """,
            "position": 5
        },

        # --- Phase 4: The Reality Check (Hardware & Hype) ---
        {
            "slug": "noise-problem",
            "title": "6. The Noise Problem (Why It Breaks)",
            "content": """
<h2>Decoherence & Noise</h2>
<p>If quantum computers are so powerful, why don't we all have one?</p>
<p><strong>The Analogy:</strong> Balancing a pencil on its tip.</p>
<p>Quantum states are incredibly fragile. A tiny vibration, a change in temperature, or a stray Wi-Fi signal causes the "spinning coin" to fall flat. This collapse is called <strong>decoherence</strong>.</p>
<p><strong>The Takeaway:</strong> Building a quantum computer is like trying to balance a house of cards in a hurricane. This is why we don't have them on our desks yet. Engineers are fighting a constant battle against noise.</p>
            """,
            "position": 6
        },
        {
            "slug": "breaking-internet",
            "title": "7. Breaking the Internet (Encryption)",
            "content": """
<h2>Shor’s Algorithm</h2>
<p>Why is there so much hype (and fear) around quantum computing?</p>
<p>Most internet security (like HTTPS) relies on the fact that math is hard—specifically, factoring very large numbers. A classical supercomputer might take millions of years to crack your credit card encryption.</p>
<p><strong>The Threat:</strong> A powerful enough quantum computer, running <strong>Shor's Algorithm</strong>, could turn that "hard" math problem into an easy one, cracking the code in hours.</p>
<p><strong>The Takeaway:</strong> Quantum computers are a potential threat to current cybersecurity, which is why governments and tech giants are racing to build them first—and to develop new "quantum-resistant" encryption.</p>
            """,
            "position": 7
        },

        # --- Phase 5: The "Killer Apps" (Where the Money Is) ---
        {
            "slug": "simulation-battery",
            "title": "8. Simulation (Why Your Battery Sucks)",
            "content": """
<h2>Quantum Simulation</h2>
<p>Classical computers are terrible at simulating chemistry because molecules follow quantum rules. To simulate a caffeine molecule perfectly on a classical computer, you’d need more memory than there are atoms in the universe.</p>
<p><strong>The Takeaway:</strong> Quantum computers can simulate new materials (better batteries, carbon capture, new drugs) because they speak the same language as nature.</p>
            """,
            "position": 8
        },
        {
            "slug": "traveling-salesman",
            "title": "9. The Traveling Salesman from Hell (Optimization)",
            "content": """
<h2>Combinatorial Optimization</h2>
<p>Imagine a delivery driver needs to visit 50 cities. Finding the perfect route is mathematically impossible for current supercomputers (too many combinations).</p>
<p><strong>The Takeaway:</strong> Quantum computers can potentially look at the "energy landscape" of the problem and find the lowest point (the best route) much faster. This revolutionizes logistics, financial portfolios, and traffic flow.</p>
            """,
            "position": 9
        },

        # --- Phase 6: The Logic (How to "Speak" Quantum) ---
        {
            "slug": "rotations-not-switches",
            "title": "10. Rotations, Not Switches (Quantum Gates)",
            "content": """
<h2>Quantum Gates (Hadamard, X-Gate)</h2>
<h3>The Analogy: The Globe</h3>
<p><strong>Classical Logic:</strong> A switch that flips up or down.</p>
<p><strong>Quantum Logic:</strong> Imagine the qubit is a point on a globe. A "gate" isn't a flip; it's a <em>rotation</em>. You rotate the point from the North Pole (0) to the Equator (Superposition).</p>
<p><strong>The Takeaway:</strong> Programming a quantum computer is like navigating a ship on a sphere, not flipping switches on a board.</p>
            """,
            "position": 10
        },
        {
            "slug": "music-score-circuits",
            "title": "11. The Music Score (Quantum Circuits)",
            "content": """
<h2>Algorithms & Circuits</h2>
<p>Look at the simulator below. It looks like a musical score, right?</p>
<p><strong>The Visual:</strong> Time moves from left to right. Each horizontal line is a qubit (an instrument). The boxes you drag onto them are the notes (operations) we play to create a result at the end.</p>
<p><strong>The Takeaway:</strong> We compose quantum algorithms like music, sequencing operations in time to manipulate the state of the qubits.</p>
            """,
            "position": 11
        },

        # --- Phase 7: The "Valley of Death" (The Roadmap) ---
        {
            "slug": "math-wall",
            "title": "12. The Math Wall (Linear Algebra)",
            "content": """
<h2>Linear Algebra: The Math Wall</h2>
<p>The Brutal Truth: You cannot go further than this without Linear Algebra (Vectors and Matrices).</p>
<p><strong>The Advice:</strong> If you want to be a practitioner, you must learn how to multiply matrices. If you just want to be a manager or investor, you can stop here.</p>
            """,
            "position": 12
        },
        {
            "slug": "get-hands-dirty",
            "title": "13. Get Your Hands Dirty (Coding)",
            "content": """
<h2>Get Your Hands Dirty</h2>
<p>You can actually run a real quantum job on a real quantum computer in the cloud right now for free (usually small, 5-7 qubit machines) using libraries like <strong>IBM Qiskit</strong> or <strong>Google Cirq</strong>.</p>
<p><strong>The Takeaway:</strong> Writing <code>Hadamard(qubit)</code> in Python makes the theory real. But here, you can do it with drag-and-drop!</p>
<p><strong>Final Challenge:</strong> Use the simulator below to create a Bell Pair (Entanglement) one last time. H on q0, CNOT on q0-q1. Verify the probability matches 50% 00 and 50% 11. You are now a quantum practitioner!</p>
            """,
            "position": 13
        }
    ]
    
    for l in lessons:
        if db_type == "postgres":
            cur.execute(
                "INSERT INTO lessons(course_id, slug, title, content, position) VALUES(%s, %s, %s, %s, %s) "
                "ON CONFLICT (course_id, slug) DO UPDATE SET title=EXCLUDED.title, content=EXCLUDED.content, position=EXCLUDED.position",
                (course_id, l["slug"], l["title"], l["content"], l["position"]))
        else:
            cur.execute("INSERT INTO lessons(course_id, slug, title, content, position) VALUES(?, ?, ?, ?, ?)",
                        (course_id, l["slug"], l["title"], l["content"], l["position"]))
        
    conn.commit()
    conn.close()
    print("Database seeded successfully with Zero to Hero curriculum!")

if __name__ == "__main__":
    seed()
