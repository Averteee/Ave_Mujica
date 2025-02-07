import feedparser
import os
import requests
from urllib.parse import urlparse

# 从环境变量中获取RSS地址
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
                    response = requests.get(torrent_url)
                    response.raise_for_status()
                    
                    # 从URL提取文件名
                    path = urlparse(torrent_url).path
                    filename = os.path.basename(path) or f"{entry_id}.torrent"
                    
                    # 保存文件
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    
                    # 记录该条目
                    new_entries.append(entry_id)
                    processed.add(entry_id)
                    print(f"Downloaded: {filename}")
                except Exception as e:
                    print(f"Error downloading {torrent_url}: {str(e)}")

    # 更新已处理条目的记录
    if new_entries:
        with open(PROCESSED_FILE, 'a') as f:
            for entry_id in new_entries:
                f.write(f"{entry_id}\n")

if __name__ == "__main__":
    main()
