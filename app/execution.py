import io
import contextlib
import traceback
import sys

def execute_code(code_str):
    """
    Executes the provided Python code string and captures stdout.
    Returns a dictionary with 'success', 'output', and optionally 'error'.
    """
    # Capture stdout
    f = io.StringIO()
    
    # Create a fresh dictionary for locals to avoid polluting the global namespace
    # and to provide a clean slate for each execution.
    local_scope = {}
    
    try:
        # Redirect stdout to capture print statements
        with contextlib.redirect_stdout(f):
            # We use a copy of globals() or just an empty dict for globals?
            # Using empty dict for globals means they have to import everything, which is good for learning.
            # However, builtins are usually needed.
            exec(code_str, {"__builtins__": __builtins__}, local_scope)
            
        output = f.getvalue()
        return {"success": True, "output": output}
    except Exception:
        # Capture the full traceback
        return {"success": False, "error": traceback.format_exc()}
