import requests
import json
from base64 import b64encode

with open('test.jpeg', 'rb') as f:
    file = b64encode(f.read()).decode()

body = {'file_data': file,
        'file_path': r'mobile_screenshots/communicator/TestClass/my_file.jpg'}

params = json.dumps(body, ensure_ascii=False).encode('utf-8')
requests.post('http://10.76.164.62:5000/push_file', data=params)