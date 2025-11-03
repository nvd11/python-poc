import asyncio
import os
import requests
from urllib.parse import urlparse
from loguru import logger
from src.decorators.time_decorator import log_execution_time

list_url = [
    "https://download.microsoft.com/download/8/1/d/81d1f546-f951-45c5-964d-56bdbd758ba4/w2k3sp2_3959_usa_x64fre_spcd.iso",
    "https://download.microsoft.com/download/5/9/7/59797dff-d8eb-4f46-9319-ea8326141ee9/w2k3sp2_3959_jpn_x64fre_spcd.iso",
    "https://download.microsoft.com/download/8/8/0/880bca75-79dd-466a-927d-1abf1f5454b0/PBIDesktopSetup_x64.exe"
]





@log_execution_time
async def download_file_with_requests(url, save_path):
    loop = asyncio.get_running_loop()

    # as lib requests does not supports async.. we need to run it in executor, 
    # to convert it to async Future(actually it will be run in a sepreated thread
    # the worker number of default thread pool is min(32, os.cpu_count() + 4)
    future = loop.run_in_executor(None, requests.get, url)

    response = await future
    file_name = os.path.basename(urlparse(url).path)
    save_path = os.path.join(save_path, file_name)
    
    with open(save_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    logger.info(f"Downloaded file from {url} to {save_path}")



@log_execution_time
async def async_files_concurrent(urls, save_path):
   tasks = [download_file_with_requests(url, save_path) for url in urls]
   await asyncio.gather(*tasks)


if __name__ == "__main__":
    save_path = "/tmp/"
    os.makedirs(save_path, exist_ok=True)
    asyncio.run(async_files_concurrent(list_url, save_path))