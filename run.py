from app import create_app
import os

app = create_app()

print("Starting app...")
if __name__ == "__main__":
    print("In main block...")
    port = int(os.environ.get("PORT", 5001))
    try:
        app.run(host="0.0.0.0", port=port, debug=True)
    except Exception as e:
        print(f"Error: {e}")
