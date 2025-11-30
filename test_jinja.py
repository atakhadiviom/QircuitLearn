
import sqlite3
from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("CREATE TABLE test (id INTEGER, slug TEXT)")
    cur.execute("INSERT INTO test VALUES (1, 'slug1')")
    row = cur.fetchone()
    
    user_progress = {1: 'completed'}
    
    # Template using dot notation
    tmpl_dot = "{{ row.id }} | {{ user_progress.get(row.id) }}"
    # Template using bracket notation
    tmpl_bracket = "{{ row['id'] }} | {{ user_progress.get(row['id']) }}"
    
    res_dot = render_template_string(tmpl_dot, row=row, user_progress=user_progress)
    res_bracket = render_template_string(tmpl_bracket, row=row, user_progress=user_progress)
    
    return f"Dot: {res_dot}\nBracket: {res_bracket}"

if __name__ == '__main__':
    app.run(port=5002)
