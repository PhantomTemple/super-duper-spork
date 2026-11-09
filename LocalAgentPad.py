import requests
import json

# ===================== 使用者自定义区域 =====================
AGENT_NAME = "Assistant"
SYSTEM_PROMPT = "You are a local assistant, answer concisely and accurately."
OLLAMA_BASE_URL = "http://127.0.0.1:11434"
MEMORY_SERVICE_URL = "http://127.0.0.1:8080/mem"
MODEL = "qwen:latest"
ENABLE_EXTERNAL_MEMORY = True
MAX_RECALL = 3
TIMEOUT_OLLAMA = 180
TIMEOUT_MEMORY = 15
# ==========================================================

def ping_ollama() -> bool:
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        return resp.status_code == 200
    except Exception:
        return False

def ping_memory_service() -> bool:
    if not ENABLE_EXTERNAL_MEMORY:
        return False
    try:
        resp = requests.get(MEMORY_SERVICE_URL, timeout=8)
        return resp.status_code == 200
    except Exception:
        return False

def fetch_memory(query: str, top_n: int) -> list:
    if not ENABLE_EXTERNAL_MEMORY:
        return []
    try:
        payload = {"query": query, "top_n": top_n}
        resp = requests.post(MEMORY_SERVICE_URL, json=payload, timeout=TIMEOUT_MEMORY)
        resp.raise_for_status()
        data = resp.json()
        return data.get("result", [])
    except Exception as e:
        print(f"\n⚠️ Memory service fetch failed: {e}, fallback to no memory")
        return []

def save_memory_record(text: str):
    if not ENABLE_EXTERNAL_MEMORY:
        return
    try:
        payload = {"content": text}
        requests.post(f"{MEMORY_SERVICE_URL}/add", json=payload, timeout=TIMEOUT_MEMORY)
    except Exception:
        pass

def clear_all_memory():
    if not ENABLE_EXTERNAL_MEMORY:
        return
    try:
        requests.post(f"{MEMORY_SERVICE_URL}/clear", timeout=TIMEOUT_MEMORY)
        print("✅ Memory cleared")
    except Exception as e:
        print(f"❌ Clear memory failed: {e}")

def stream_chat(user_input: str, recall_list: list):
    recall_block = ""
    if recall_list:
        recall_block = "\n".join([f"【Memory】{item}" for item in recall_list])
    full_system = f"{SYSTEM_PROMPT}\n{recall_block}"

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": full_system},
            {"role": "user", "content": user_input}
        ],
        "stream": True
    }
    try:
        resp = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=TIMEOUT_OLLAMA, stream=True)
        resp.raise_for_status()
        print(f"\n{AGENT_NAME}: ", end="", flush=True)
        full_reply = ""
        for line in resp.iter_lines():
            if not line:
                continue
            data = json.loads(line.decode("utf-8"))
            chunk = data.get("message", {}).get("content", "")
            print(chunk, end="", flush=True)
            full_reply += chunk
        print("\n")
        return full_reply
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection error: Ollama unreachable")
    except requests.exceptions.Timeout:
        print("\n❌ Ollama request timeout")
    except Exception as e:
        print(f"\n❌ Stream error: {e}")
    return ""

def run_chat_loop():
    global MODEL
    print(f"===== LocalAgentPad | {AGENT_NAME} =====")
    print("Available commands:")
    print("  exit      - quit")
    print("  ping      - check Ollama status")
    print("  memstat   - check memory plugin status")
    print("  clear     - clear all memory")
    print("  model <name> - switch ollama model")
    print("----------------------------------------")
    if not ping_ollama():
        print("❌ Ollama offline, start ollama serve first")
        return

    while True:
        user_input = input("You: ")
        cmd = user_input.strip().lower()
        if cmd == "exit":
            print("Bye")
            break
        if cmd == "ping":
            if ping_ollama():
                print("✅ Ollama online\n")
            else:
                print("❌ Ollama offline\n")
            continue
        if cmd == "memstat":
            if ping_memory_service():
                print("✅ Memory plugin online\n")
            else:
                print("❌ Memory plugin offline or disabled\n")
            continue
        if cmd == "clear":
            clear_all_memory()
            continue
        if cmd.startswith("model "):
            new_model = user_input.split(" ", 1)[1]
            MODEL = new_model
            print(f"✅ Switched model to {MODEL}\n")
            continue

        recall_list = fetch_memory(user_input, MAX_RECALL)
        reply = stream_chat(user_input, recall_list)
        if reply and ENABLE_EXTERNAL_MEMORY:
            save_memory_record(f"User: {user_input} | Reply: {reply}")

if __name__ == "__main__":
    run_chat_loop()
