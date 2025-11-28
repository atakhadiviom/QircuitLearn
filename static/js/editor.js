const state = {
    qubits: 3,
    steps: 20,
    gates: [], // { type, target, step, control? }
    draggedType: null,
    pendingCNOT: null // { target, step }
};

const editor = document.getElementById('editor');
const output = document.getElementById('output');
const loading = document.getElementById('loading');

function init() {
    // Initialize state from task if available
    if (window.currentTask && window.currentTask.qubits) {
        state.qubits = window.currentTask.qubits;
    }

    setupPalette();
    setupControls();
    updateQubitCount();
    render();

    // Update lines on resize
    window.addEventListener('resize', () => {
        const container = document.querySelector('.circuit-grid');
        if (container) {
            updateCircuitLines(container);
        }
    });
}

function setupPalette() {
    document.querySelectorAll('.gate-btn').forEach(btn => {
        btn.setAttribute('draggable', 'true');
        btn.addEventListener('dragstart', (e) => {
            state.draggedType = btn.dataset.type;
            e.dataTransfer.effectAllowed = 'copy';
            e.dataTransfer.setData('text/plain', btn.dataset.type);
            btn.classList.add('dragging');
            editor.classList.add('dragging-active');
        });
        btn.addEventListener('dragend', () => {
            btn.classList.remove('dragging');
            editor.classList.remove('dragging-active');
            state.draggedType = null;
        });
    });
}

function setupControls() {
    document.getElementById('add-qubit').onclick = () => {
        if (state.qubits < 8) {
            state.qubits++;
            updateQubitCount();
            render();
        }
    };
    document.getElementById('remove-qubit').onclick = () => {
        if (state.qubits > 1) {
            state.qubits--;
            // Remove gates on the removed qubit
            state.gates = state.gates.filter(g => g.target < state.qubits && (g.control === undefined || g.control < state.qubits));
            updateQubitCount();
            render();
        }
    };
    document.getElementById('clear').onclick = () => {
        state.gates = [];
        state.pendingCNOT = null;
        render();
        output.innerHTML = '<div class="placeholder">Run simulation to see results...</div>';
    };
    document.getElementById('simulate').onclick = callBackend;
}

function updateQubitCount() {
    document.getElementById('qubit-count').textContent = state.qubits;
}

function handleDrop(e, qubit, step) {
    e.preventDefault();
    const type = state.draggedType;
    if (!type) return;

    // Check if slot is occupied
    const existing = state.gates.find(g => g.target === qubit && g.step === step);
    if (existing) {
        // Replace or ignore? Let's replace.
        state.gates = state.gates.filter(g => g !== existing);
    }

    // Also check if this slot is a control for another gate
    const existingControl = state.gates.find(g => g.control === qubit && g.step === step);
    if (existingControl) {
        alert("Cannot place gate here: This qubit is a control for another gate at this step.");
        return;
    }

    if (type === 'CNOT') {
        state.pendingCNOT = { target: qubit, step: step };
        // Temporarily add incomplete gate
        state.gates.push({ type: 'CNOT', target: qubit, step: step, control: null });
        render();
    } else if (['RX', 'RY', 'RZ'].includes(type)) {
        const val = prompt(`Enter rotation angle for ${type} (in radians, e.g. 1.57 for π/2):`, "1.57");
        let theta = parseFloat(val);
        if (isNaN(theta)) theta = 0;
        state.gates.push({ type: type, target: qubit, step: step, params: { theta } });
        render();
    } else {
        state.gates.push({ type: type, target: qubit, step: step });
        render();
    }
}

function handleZoneClick(qubit, step) {
    // If we are in pendingCNOT mode, this click sets the control
    if (state.pendingCNOT) {
        if (state.pendingCNOT.step !== step) {
            // Clicked wrong column, maybe cancel?
            cancelPendingCNOT();
            return;
        }
        if (state.pendingCNOT.target === qubit) {
            alert("Control cannot be the same as target.");
            return;
        }

        // Finalize CNOT
        const gate = state.gates.find(g => g.target === state.pendingCNOT.target && g.step === state.pendingCNOT.step && g.type === 'CNOT');
        if (gate) {
            gate.control = qubit;
        }
        state.pendingCNOT = null;
        render();
        return;
    }

    // Otherwise, maybe remove gate if one exists?
    const gateIndex = state.gates.findIndex(g => g.target === qubit && g.step === step);
    if (gateIndex !== -1) {
        state.gates.splice(gateIndex, 1);
        render();
        return;
    }

    // Check if it's a control point
    const controlGateIndex = state.gates.findIndex(g => g.control === qubit && g.step === step);
    if (controlGateIndex !== -1) {
        state.gates.splice(controlGateIndex, 1);
        render();
    }
}

function cancelPendingCNOT() {
    if (!state.pendingCNOT) return;
    // Remove the incomplete gate
    state.gates = state.gates.filter(g => !(g.target === state.pendingCNOT.target && g.step === state.pendingCNOT.step && g.type === 'CNOT' && g.control === null));
    state.pendingCNOT = null;
    render();
}

function render() {
    editor.innerHTML = '';

    if (state.pendingCNOT) {
        const banner = document.createElement('div');
        banner.style.background = 'rgba(16, 185, 129, 0.2)';
        banner.style.color = '#6ee7b7';
        banner.style.padding = '10px';
        banner.style.textAlign = 'center';
        banner.style.borderRadius = '4px';
        banner.style.marginBottom = '10px';
        banner.style.fontWeight = 'bold';
        banner.textContent = 'Select a Control Qubit (click a green zone)';
        editor.appendChild(banner);
    }

    const container = document.createElement('div');
    container.className = 'circuit-grid';

    // SVG Container for lines (CNOT connections)
    const svgNS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("class", "circuit-overlay");
    container.appendChild(svg);

    for (let q = 0; q < state.qubits; q++) {
        const row = document.createElement('div');
        row.className = 'qubit-row';

        const label = document.createElement('div');
        label.className = 'qubit-label';
        label.textContent = `q${q}`;
        row.appendChild(label);

        const wireContainer = document.createElement('div');
        wireContainer.className = 'wire-container';

        const wireLine = document.createElement('div');
        wireLine.className = 'wire-line';
        wireContainer.appendChild(wireLine);

        // Create drop zones for each step
        for (let s = 0; s < state.steps; s++) {
            const zone = document.createElement('div');
            zone.className = 'drop-zone';
            zone.dataset.qubit = q;
            zone.dataset.step = s;

            // Drag events
            zone.ondragover = (e) => {
                e.preventDefault(); // Allow drop
                zone.classList.add('drag-over');
            };
            zone.ondragleave = () => {
                zone.classList.remove('drag-over');
            };
            zone.ondrop = (e) => {
                zone.classList.remove('drag-over');
                handleDrop(e, q, s);
            };

            // Click handler (remove or set control)
            zone.onclick = () => handleZoneClick(q, s);

            // Render Gate if exists
            const gate = state.gates.find(g => g.target === q && g.step === s);
            if (gate) {
                const el = document.createElement('div');
                el.className = 'placed-gate';
                el.textContent = gate.type;
                
                if (gate.params && gate.params.theta !== undefined) {
                     el.style.fontSize = '0.7em';
                     el.style.display = 'flex';
                     el.style.alignItems = 'center';
                     el.style.justifyContent = 'center';
                     el.textContent = `${gate.type}\n(${gate.params.theta.toFixed(1)})`;
                }

                if (gate.type === 'CNOT' && gate.control === null) {
                    el.style.opacity = '0.5';
                    el.textContent = '?';
                    el.title = "Click a control qubit in this column";
                }
                // Prevent drag on placed gates for now (simple)
                // Or make them draggable to move?
                // Let's keep it simple: Click to delete/move.
                zone.appendChild(el);
            }

            // Render Control point if exists
            const controlledGate = state.gates.find(g => g.control === q && g.step === s);
            if (controlledGate) {
                const el = document.createElement('div');
                el.className = 'placed-gate control';
                // Make transparent so SVG dot shows, but keep for interaction
                el.style.opacity = '0';
                el.title = `Control for q${controlledGate.target}`;
                zone.appendChild(el);
            }

            // Highlight if valid target for pending CNOT
            if (state.pendingCNOT && state.pendingCNOT.step === s && state.pendingCNOT.target !== q) {
                zone.style.background = 'rgba(16, 185, 129, 0.2)'; // Green tint hint
                zone.style.cursor = 'pointer';
            }

            wireContainer.appendChild(zone);
        }

        row.appendChild(wireContainer);
        container.appendChild(row);
    }

    editor.appendChild(container);

    // Draw lines after layout
    requestAnimationFrame(() => updateCircuitLines(container));
}

function updateCircuitLines(container) {
    const svg = container.querySelector('.circuit-overlay');
    // Clear existing
    while (svg.firstChild) {
        svg.removeChild(svg.firstChild);
    }

    const svgNS = "http://www.w3.org/2000/svg";
    const containerRect = container.getBoundingClientRect();

    // Draw lines for CNOTs
    state.gates.forEach(g => {
        if (g.type === 'CNOT' && g.control !== null && g.control !== undefined) {
            const controlQ = g.control;
            const targetQ = g.target;
            const step = g.step;

            // Find zones
            const controlZone = container.querySelector(`.drop-zone[data-qubit="${controlQ}"][data-step="${step}"]`);
            const targetZone = container.querySelector(`.drop-zone[data-qubit="${targetQ}"][data-step="${step}"]`);

            if (controlZone && targetZone) {
                const cRect = controlZone.getBoundingClientRect();
                const tRect = targetZone.getBoundingClientRect();

                const x1 = cRect.left + cRect.width / 2 - containerRect.left;
                const y1 = cRect.top + cRect.height / 2 - containerRect.top;
                const x2 = tRect.left + tRect.width / 2 - containerRect.left;
                const y2 = tRect.top + tRect.height / 2 - containerRect.top;

                // Draw Line
                const line = document.createElementNS(svgNS, "line");
                line.setAttribute("x1", x1);
                line.setAttribute("y1", y1);
                line.setAttribute("x2", x2);
                line.setAttribute("y2", y2);
                line.setAttribute("class", "cnot-line");
                svg.appendChild(line);

                // Draw Control Dot
                const circle = document.createElementNS(svgNS, "circle");
                circle.setAttribute("cx", x1);
                circle.setAttribute("cy", y1);
                circle.setAttribute("r", "5");
                circle.setAttribute("class", "cnot-control");
                svg.appendChild(circle);
            }
        }
    });
}


let resultsChart = null;

async function callBackend() {
    loading.classList.remove('hidden');
    output.textContent = 'Running...';

    // Reset chart
    const chartContainer = document.querySelector('.chart-container');
    chartContainer.style.display = 'none';
    if (resultsChart) {
        resultsChart.destroy();
        resultsChart = null;
    }

    try {
        // Sort gates by step
        const sortedGates = [...state.gates]
            .filter(g => !(g.type === 'CNOT' && g.control === null)) // Filter incomplete CNOTs
            .sort((a, b) => a.step - b.step);

        const payload = {
            circuit: {
                qubits: state.qubits,
                gates: sortedGates
            },
            shots: 0 // 0 for statevector/probabilities
        };

        const res = await fetch('/api/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (data.error) {
            output.textContent = `Error: ${data.error}`;
        } else {
            let outStr = '';
            const labels = [];
            const values = [];

            if (data.probabilities) {
                outStr += 'State Vector Probabilities:\n';
                data.probabilities.forEach((p, i) => {
                    const bin = i.toString(2).padStart(state.qubits, '0');
                    const pct = (p * 100).toFixed(1);

                    if (p > 0.0001) {
                        outStr += `|${bin}⟩: ${pct}%\n`;
                        labels.push(`|${bin}⟩`);
                        values.push(p * 100);
                    }
                });

                // Render Chart
                if (labels.length > 0) {
                    chartContainer.style.display = 'block';
                    renderChart(labels, values);
                }

                // Render Bloch Spheres
                if (data.statevector) {
                    renderBlochSpheres(data.statevector, state.qubits);
                }
                
                // Validate Task
                if (typeof validateTask === 'function') {
                    validateTask(data);
                }

            } else {
                outStr += JSON.stringify(data, null, 2);
            }
            output.textContent = outStr;
        }
    } catch (e) {
        output.textContent = `Error: ${e.message}`;
    } finally {
        loading.classList.add('hidden');
    }
}

function renderChart(labels, data) {
    const ctx = document.getElementById('resultsChart').getContext('2d');
    resultsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Probability (%)',
                data: data,
                backgroundColor: 'rgba(146, 112, 82, 0.6)',
                borderColor: '#927052',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    ticks: { color: '#94a3b8' },
                    grid: { color: '#334155' }
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { color: '#94a3b8' },
                    grid: { color: '#334155' },
                    title: {
                        display: true,
                        text: 'Probability (%)',
                        color: '#94a3b8'
                    }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    titleColor: '#f8fafc',
                    bodyColor: '#f8fafc',
                    backgroundColor: '#1e293b',
                    borderColor: '#334155',
                    borderWidth: 1
                }
            }
        }
    });
}

// --- Bloch Sphere Logic ---

function parseComplex(str) {
    // Format: (real+imagj) or (real-imagj)
    // Remove ()
    str = str.replace(/[()]/g, '');
    let real = 0;
    let imag = 0;

    // Handle 'j' at the end
    if (str.endsWith('j')) {
        str = str.slice(0, -1); // remove j
    } else {
        // Real number only?
        return { re: parseFloat(str), im: 0 };
    }

    // Find the last + or - to split
    // But be careful of scientific notation e.g. 1e-5
    // And the first sign

    // Easier approach: use regex
    // Matches: (real part)(sign)(imag part)
    // But python complex str is a bit tricky: 1+2j, 1-2j, 1j, -1j

    // Let's try a simpler split
    const parts = str.split(/(?=[+-])/);
    // parts might be ["1", "+2"] or ["-1", "-2"]

    parts.forEach(p => {
        if (!p) return;
        if (p === '+' || p === '-') return; // shouldn't happen with lookahead

        let val = parseFloat(p);
        if (isNaN(val)) {
            // maybe just "j" or "-j"? Python outputs 1j usually
            if (p === 'j' || p === '+j') val = 1;
            else if (p === '-j') val = -1;
        }

        // In Python str(complex), the imaginary part is always last and has 'j' (we removed it)
        // Actually we removed 'j' from the very end of the whole string.
        // So if we are processing the last part, it was the imaginary part.

        // Wait, let's restart parsing to be robust.
        // Python: (1+2j) -> 1+2j
    });

    // Robust parsing of Python complex string
    // It's usually (r+ij)
    const match = str.match(/^([+-]?[\d\.eE]+)?([+-]?[\d\.eE]+)?$/);
    // This is getting complicated. Let's assume standard format.

    // Let's just use a simple parser assuming "real+imag" structure
    let s = str;
    let re = 0, im = 0;

    // Find split index
    let splitIdx = -1;
    // Start from end, skip last char (which was j)
    for (let i = s.length - 1; i > 0; i--) {
        if (s[i] === '+' || s[i] === '-') {
            // Check if it's e-5 or e+5
            if (s[i - 1] === 'e' || s[i - 1] === 'E') continue;
            splitIdx = i;
            break;
        }
    }

    if (splitIdx === -1) {
        // Pure imaginary or pure real?
        // We stripped 'j' from end. If it was there, it's imaginary.
        // But we don't know if 'j' was there in this scope.
        // Let's pass the original string with 'j' to this function.
        return { re: 0, im: 0 }; // Fallback
    }

    re = parseFloat(s.substring(0, splitIdx));
    im = parseFloat(s.substring(splitIdx));
    return { re, im };
}

function parseComplexPython(str) {
    // str is like "(0.7071067811865476+0j)"
    str = str.replace(/[()]/g, '');

    // Check for 'j'
    if (!str.includes('j')) {
        return { re: parseFloat(str), im: 0 };
    }

    // Remove 'j'
    str = str.replace('j', '');

    // Find the separator between real and imag
    // Scan from right to left to find + or - that is NOT part of scientific notation
    let sep = -1;
    for (let i = str.length - 1; i > 0; i--) {
        if (str[i] === '+' || str[i] === '-') {
            const prev = str[i - 1].toLowerCase();
            if (prev !== 'e') {
                sep = i;
                break;
            }
        }
    }

    if (sep === -1) {
        // Pure imaginary e.g. "1j" -> "1"
        return { re: 0, im: parseFloat(str) };
    }

    const reStr = str.substring(0, sep);
    const imStr = str.substring(sep);

    return { re: parseFloat(reStr), im: parseFloat(imStr) };
}

function getBlochVector(qubit, nQubits, statevector) {
    // Calculate <X>, <Y>, <Z> for the given qubit
    let x = 0, y = 0, z = 0;

    // Iterate over all basis states
    const N = 1 << nQubits;

    for (let i = 0; i < N; i++) {
        // Get amplitude alpha_i
        const amp = parseComplexPython(statevector[i]);

        // Check if k-th bit is 0 or 1
        // qubit 0 is usually the last bit in binary string (Little Endian? Cirq uses Big Endian by default for printing but let's check)
        // Cirq state vector is usually Big Endian (q0 is MSB? No, usually q0 is first in tensor product)
        // Let's assume standard order: |q0 q1 ... qn>
        // So q0 is the MSB (index 0).
        // i = b0 b1 ... bn
        // bit val is (i >> (nQubits - 1 - qubit)) & 1

        const shift = nQubits - 1 - qubit;
        const bit = (i >> shift) & 1;

        // <Z> calculation
        // If bit is 0, contrib is |amp|^2
        // If bit is 1, contrib is -|amp|^2
        const magSq = amp.re * amp.re + amp.im * amp.im;
        z += (bit === 0 ? 1 : -1) * magSq;

        // For X and Y, we need pairs (i, j) where i has bit 0 and j has bit 1
        if (bit === 0) {
            const j = i | (1 << shift);
            const ampJ = parseComplexPython(statevector[j]);

            // <X>: 2 * Re(amp_i * conj(amp_j)) ??
            // Wait, formula: <psi|X|psi> = sum_k psi_k* (X psi)_k
            // X flips bit. (X psi)_i = psi_j
            // term i: psi_i* psi_j
            // term j: psi_j* psi_i
            // Sum = psi_i* psi_j + psi_j* psi_i = 2 Re(psi_i* psi_j)
            // psi_i * psi_j = (re_i - i im_i) * (re_j + i im_j)
            // = (re_i re_j + im_i im_j) + i(re_i im_j - im_i re_j)
            // We want conjugate of i times j?
            // psi_i* = re_i - i im_i
            // psi_i* psi_j = (re_i - i im_i)(re_j + i im_j)
            // Real part: re_i re_j + im_i im_j

            x += 2 * (amp.re * ampJ.re + amp.im * ampJ.im);

            // <Y>: 2 * Im(psi_i* psi_j)
            // Y|0> = i|1>, Y|1> = -i|0>
            // (Y psi)_i = -i psi_j
            // (Y psi)_j = i psi_i
            // term i: psi_i* (-i psi_j) = -i psi_i* psi_j
            // term j: psi_j* (i psi_i) = i psi_j* psi_i
            // Sum = i (psi_j* psi_i - psi_i* psi_j)
            // Let z = psi_i* psi_j. Then psi_j* psi_i = z*
            // i (z* - z) = i (-2i Im(z)) = 2 Im(z)
            // So we need 2 * Im(psi_i* psi_j)
            // Im(psi_i* psi_j) = re_i im_j - im_i re_j

            y += 2 * (amp.re * ampJ.im - amp.im * ampJ.re);
        }
    }
    return { x, y, z };
}

function renderBlochSpheres(statevector, nQubits) {
    const container = document.getElementById('bloch-container');
    container.innerHTML = '';

    for (let q = 0; q < nQubits; q++) {
        const vec = getBlochVector(q, nQubits, statevector);
        
        const wrapper = document.createElement('div');
        wrapper.className = 'bloch-wrapper';
        wrapper.style.textAlign = 'center';

        const canvas = document.createElement('canvas');
        canvas.width = 200;
        canvas.height = 200;
        wrapper.appendChild(canvas);

        const label = document.createElement('div');
        label.textContent = `Qubit ${q}`;
        wrapper.appendChild(label);

        container.appendChild(wrapper);

        drawBlochSphere(canvas, vec);
    }
}

function drawBlochSphere(canvas, vec) {
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const r = w * 0.35;

    ctx.clearRect(0, 0, w, h);

    // Draw sphere outline
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, 2 * Math.PI);
    ctx.strokeStyle = '#334155';
    ctx.stroke();

    // Draw equator
    ctx.beginPath();
    ctx.ellipse(cx, cy, r, r * 0.3, 0, 0, 2 * Math.PI);
    ctx.strokeStyle = '#475569';
    ctx.stroke();

    // Draw axes
    // Z axis
    ctx.beginPath();
    ctx.moveTo(cx, cy - r);
    ctx.lineTo(cx, cy + r);
    ctx.strokeStyle = '#475569';
    ctx.stroke();
    
    ctx.fillStyle = '#94a3b8';
    ctx.fillText('|0⟩', cx - 10, cy - r - 5);
    ctx.fillText('|1⟩', cx - 10, cy + r + 15);

    // Draw Vector
    // Project 3D (x, y, z) to 2D
    // Simple projection: 
    // screenX = cx + x * r * 0.7 + y * r * 0.5 (perspective)
    // Actually, standard Bloch projection:
    // x comes out of page (or right), y goes right (or into page), z goes up
    // Let's use: x is right-down, y is right-up? 
    // Standard: z is up. x is forward-left, y is forward-right?
    // Let's stick to a simple 2D projection where we see Z clearly.
    // x is horizontal, z is vertical? No, that's a circle.
    // Let's try: x projects to x-axis offset, y projects to depth?
    
    // Simple isometric-ish:
    // x axis: points to right-down
    // y axis: points to right-up
    // z axis: points up
    
    // For 2D canvas, let's just project x to x-axis and z to y-axis (inverted)
    // And y adds some depth offset?
    
    // Let's assume standard view:
    // Z is up (-y in canvas)
    // Y is right (+x in canvas)
    // X is coming at viewer (diagonal)

    // vector tip:
    const screenX = cx + vec.y * r - vec.x * r * 0.4;
    const screenY = cy - vec.z * r + vec.x * r * 0.4;

    // Draw line
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(screenX, screenY);
    ctx.strokeStyle = '#927052'; // Primary Copper
    ctx.lineWidth = 2;
    ctx.stroke();

    // Draw tip
    ctx.beginPath();
    ctx.arc(screenX, screenY, 4, 0, 2 * Math.PI);
    ctx.fillStyle = '#927052'; // Primary Copper
    ctx.fill();
    
    // Debug text
    // ctx.fillStyle = 'black';
    // ctx.fillText(`x:${vec.x.toFixed(2)}`, 10, 20);
    // ctx.fillText(`y:${vec.y.toFixed(2)}`, 10, 35);
    // ctx.fillText(`z:${vec.z.toFixed(2)}`, 10, 50);
}

// Init
init();

// --- Task Validation & Progress ---

function validateTask(data) {
    if (!window.currentTask) return;
    
    const task = window.currentTask;
    const criteria = task.criteria;
    let success = false;
    let message = "";

    if (criteria === 'superposition') {
        // Check if probabilities are roughly 50/50 for 0 and 1
        // Assuming 1 qubit for now as per task description
        if (data.probabilities && data.probabilities.length >= 2) {
            const p0 = data.probabilities[0];
            const p1 = data.probabilities[1];
            if (Math.abs(p0 - 0.5) < 0.1 && Math.abs(p1 - 0.5) < 0.1) {
                success = true;
                message = "Great job! You created a superposition.";
            } else {
                message = `Not quite. Probabilities are ${Math.round(p0*100)}% and ${Math.round(p1*100)}%. Aim for 50/50.`;
            }
        }
    } else if (criteria === 'bell_pair') {
        // Check for |00> and |11> with ~50% prob each
        // |00> is index 0, |11> is index 3 (binary 11)
        if (data.probabilities && data.probabilities.length >= 4) {
             const p00 = data.probabilities[0];
             const p11 = data.probabilities[3];
             const p01 = data.probabilities[1];
             const p10 = data.probabilities[2];
             
             if (Math.abs(p00 - 0.5) < 0.1 && Math.abs(p11 - 0.5) < 0.1 && p01 < 0.01 && p10 < 0.01) {
                 success = true;
                 message = "Excellent! You created a Bell Pair entanglement.";
             } else {
                 message = "Close, but not a perfect Bell Pair. Make sure you have 50% |00> and 50% |11>.";
             }
        }
    }

    const taskBox = document.getElementById('task-box');
    const taskStatus = document.getElementById('task-status');
    
    if (taskBox && taskStatus) {
        if (success) {
            taskStatus.className = 'status-success';
            taskStatus.textContent = '✅ ' + message;
            saveProgress();
        } else {
            taskStatus.className = 'status-fail';
            taskStatus.textContent = '❌ ' + message;
        }
    }
}

async function saveProgress() {
    if (!window.currentLessonId) return;

    try {
        await fetch('/api/progress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                lesson_id: window.currentLessonId,
                status: 'completed'
            })
        });
        console.log("Progress saved!");
    } catch (e) {
        console.error("Failed to save progress", e);
    }
}
