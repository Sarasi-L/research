import requests

url = "http://127.0.0.1:8000/process_audio"
file_path = r"D:\My Documents\SLIIT\DS4.1\Research Project\multi_notation_generator_\backend\audio_input\mix4.mp3"

with open(file_path, "rb") as f:
    files = {"file": f}
    r = requests.post(url, files=files)
    print(r.json())
