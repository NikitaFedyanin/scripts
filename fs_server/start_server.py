import os
from base64 import b64decode
from fastapi import FastAPI
import uvicorn
import asyncio
from pydantic import BaseModel

app = FastAPI()


async def write_file(file_data, file_path):
    base_root = '/var/file_storage'
    file_path = file_path.replace('\\', '/')
    file_path = os.path.join(base_root, file_path)
    base_dir = os.path.dirname(file_path)
    if not os.path.isdir(base_dir):
        os.makedirs(base_dir)
    with open(file_path, 'wb') as f:
        f.write(b64decode(file_data))
    return 'OK'


class Item(BaseModel):
    file_data: str
    file_path: str


@app.post("/push_file")
async def push_file(item: Item):
    file_data = item.file_data
    file_path = item.file_path
    asyncio.create_task(write_file(file_data, file_path))
    return 'OK'


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5000)
