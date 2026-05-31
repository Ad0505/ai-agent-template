from llm import ensure_model
import subprocess
import time
import requests
import signal
import sys
import os
from log_util import clear_log
from platform_utils import get_ollama_executable

OLLAMA_PATH = get_ollama_executable()
OLLAMA_URL = "http://localhost:11434"
API_URL = "http://localhost:8000/chat"

ollama_process = None
api_process = None


# -------------------------
# Start Ollama
# -------------------------
def start_ollama():
    global ollama_process

    print("Starting Ollama...")

    env = os.environ.copy()

    # Set models directory (relative → absolute path)
    models_path = os.path.abspath(os.path.join("ollama", "models"))
    os.makedirs(models_path, exist_ok=True)

    env["OLLAMA_MODELS"] = models_path

    ollama_process = subprocess.Popen(
        [OLLAMA_PATH, "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env
    )

    # wait for server
    for _ in range(20):
        try:
            requests.get("http://localhost:11434")
            print("Ollama is running.")
            return
        except:
            time.sleep(0.5)

    print("Failed to start Ollama.")
    cleanup()
    sys.exit(1)


# -------------------------
# Start FastAPI (uvicorn)
# -------------------------
def start_api():
    global api_process

    print("Starting FastAPI server...")

    api_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # wait until API is ready
    for _ in range(20):
        try:
            requests.get("http://localhost:8000")
            print("API is running.")
            return
        except:
            time.sleep(0.5)

    print("Failed to start API.")
    cleanup()
    sys.exit(1)


# -------------------------
# Chat loop
# -------------------------
def chat_loop():
    print("\n=== AI Agent Chat ===")
    print("Type 'exit' to quit\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() in ["exit", "quit"]:
            break

        try:
            response = requests.post(API_URL, params={"query": user_input})
            data = response.json()
            print("AI:", data["response"], "\n")
        except Exception as e:
            print("Error talking to API:", e)


# -------------------------
# Cleanup
# -------------------------
def cleanup():
    global ollama_process, api_process

    print("\nShutting down...")

    if api_process:
        api_process.terminate()
        api_process.wait()

    if ollama_process:
        ollama_process.terminate()
        ollama_process.wait()

    print("Done.")


# -------------------------
# Handle CTRL+C
# -------------------------
def handle_exit(sig, frame):
    cleanup()
    sys.exit(0)


signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)


# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    try:
        clear_log()
        start_ollama()
        ensure_model()
        start_api()
        chat_loop()
    finally:
        cleanup()