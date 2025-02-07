import feedparser
import os
import requests
from urllib.parse import urlparse

RSS_URL = os.environ.get('RSS_URL')
PROCESSED_FILE = 'processed.txt'

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
        entry_id = entry.get('id', entry.link)
        if entry_id not in processed:
            torrent_url = entry.link  # 假设链接是种子文件
            try:
                response = requests.get(torrent_url)
                response.raise_for_status()
                
                # 从URL提取文件名
                path = urlparse(torrent_url).path
                filename = os.path.basename(path) or f"{entry_id}.torrent"
                
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                new_entries.append(entry_id)
                processed.add(entry_id)
                print(f"Downloaded: {filename}")
            except Exception as e:
                print(f"Error downloading {torrent_url}: {str(e)}")

    # 更新处理记录
    if new_entries:
        with open(PROCESSED_FILE, 'a') as f:
            for entry_id in new_entries:
                f.write(f"{entry_id}\n")

if __name__ == "__main__":
    main()