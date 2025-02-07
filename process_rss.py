import feedparser
import os
import requests
import subprocess
import tempfile
from urllib.parse import urlparse

# 从环境变量中获取RSS地址
RSS_URL = os.environ.get('RSS_URL')
PROCESSED_FILE = 'processed.txt'
ARIA2C_PATH = "/usr/bin/aria2c"  # 确保 aria2c 在你的 PATH 中，或者填入绝对路径

def download_torrent(torrent_url):
    """下载 .torrent 文件"""
    response = requests.get(torrent_url)
    response.raise_for_status()

    # 将 .torrent 文件保存到临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix='.torrent') as temp_file:
        temp_file.write(response.content)
        temp_file_path = temp_file.name
        print(f"Downloaded torrent file: {temp_file_path}")
    
    return temp_file_path

def download_files_using_aria2(torrent_file_path):
    """使用 aria2 下载 .torrent 文件中的内容"""
    # 创建一个临时目录来保存下载的文件
    download_dir = tempfile.mkdtemp()
    print(f"Downloading files to: {download_dir}")
    
    # 使用 aria2c 下载 .torrent 文件
    try:
        subprocess.run([ARIA2C_PATH, '--dir', download_dir, '--seed-time=0', torrent_file_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error while downloading with aria2: {e}")
        return None
    
    return download_dir

def main():
    # 读取已处理条目
    processed = set()
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r') as f:
            processed = set(line.strip() for line in f)

    # 解析RSS
    feed = feedparser.parse(RSS_URL)
    new_entries = []

    for entry in feed.entries:
        entry_id = entry.get('guid', entry.link)  # 使用guid作为唯一标识符
        if entry_id not in processed:
            # 找到 <enclosure> 中的 .torrent 文件 URL
            torrent_url = None
            for enclosure in entry.get('enclosures', []):
                if enclosure.get('type') == 'application/x-bittorrent':
                    torrent_url = enclosure.get('url')
                    break
            
            if torrent_url:
                try:
                    # 下载 .torrent 文件
                    torrent_file_path = download_torrent(torrent_url)
                    
                    # 使用 aria2 下载文件
                    download_dir = download_files_using_aria2(torrent_file_path)
                    
                    if download_dir:
                        # 文件下载成功后，将文件夹内的内容上传到 GitHub Release
                        new_entries.append(entry_id)
                        processed.add(entry_id)
                        print(f"Downloaded files from torrent: {torrent_file_path}")
                    
                    # 删除临时 .torrent 文件
                    os.remove(torrent_file_path)
                    
                except Exception as e:
                    print(f"Error processing {torrent_url}: {str(e)}")

    # 更新已处理条目的记录
    if new_entries:
        with open(PROCESSED_FILE, 'a') as f:
            for entry_id in new_entries:
                f.write(f"{entry_id}\n")

if __name__ == "__main__":
    main()
