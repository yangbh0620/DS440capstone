import threading
import requests

TARGET_URL = "http://127.0.0.1:8000/search"

def attack_server():
    try:
        # Require the server to respond within 0.2 seconds, otherwise it's a timeout error
        response = requests.get(TARGET_URL, timeout=0.2)
        print(f"Success: {response.status_code}")
    except Exception as e:
        # Print the error when the server chokes
        print(f"🔥 CRASH! Server failed to respond: {type(e).__name__}")

print("🚀 Launching concurrent attack on FastAPI...")

# Launch 500 simultaneous requests
threads = []
for i in range(500):
    t = threading.Thread(target=attack_server)
    threads.append(t)
    t.start()

for t in threads:
    t.join()
print("🛑 Attack finished.")