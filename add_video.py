import os
import json
import yt_dlp

# --- 配置 ---
JSON_FILE = 'videos.json'
SUB_DIR = 'subs'
COOKIE_FILE = 'cookies.txt'  # 确保你之前的 cookies.txt 还在

def load_data():
    if not os.path.exists(JSON_FILE):
        return []
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def process_video(url, custom_title=None):
    os.makedirs(SUB_DIR, exist_ok=True)
    
    # 这一步是为了确定下载字幕的确切文件名
    # 我们强制命名为: 视频ID.vtt
    
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en', 'zh-Hans'],
        # 强制输出路径和文件名
        'outtmpl': f'{SUB_DIR}/%(id)s', 
        'quiet': False,
        'cookiefile': COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
        'postprocessors': [{
            'key': 'FFmpegSubtitlesConvertor',
            'format': 'vtt',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"正在解析: {url} ...")
            info = ydl.extract_info(url, download=True)
            
            if 'entries' in info: info = info['entries'][0]

            video_id = info['id']
            title = custom_title if custom_title else info['title']
            thumbnail = info['thumbnail']
            
            # 处理字幕文件名逻辑
            # yt-dlp 下载后可能是 id.en.vtt 或 id.zh-Hans.vtt
            # 我们需要找到这个文件，并在 JSON 里记录正确的路径
            sub_filename = None
            for f in os.listdir(SUB_DIR):
                if f.startswith(video_id) and f.endswith('.vtt'):
                    sub_filename = f
                    break
            
            # 如果没找到字幕，说明可能没下载成功，但视频还是要加
            sub_path = f"subs/{sub_filename}" if sub_filename else ""

            new_video = {
                "id": video_id,
                "title": title,
                "thumbnail": thumbnail,
                "sub_url": sub_path,
                "timestamp": info.get('upload_date', '')
            }
            return new_video

    except Exception as e:
        print(f"出错啦: {e}")
        return None

if __name__ == '__main__':
    print("=== HoopsHub 本地管理器 ===")
    url = input("请输入 YouTube 链接: ").strip()
    if url:
        custom_title = input("请输入自定义标题 (回车使用原标题): ").strip()
        
        videos = load_data()
        
        # 查重
        # 先临时提取ID可能会比较麻烦，这里简化处理，解析完再比对
        video_data = process_video(url, custom_title)
        
        if video_data:
            # 检查 ID 是否已存在
            if any(v['id'] == video_data['id'] for v in videos):
                print(">>> 警告：该视频已存在，已更新信息。")
                # 更新旧数据
                for i, v in enumerate(videos):
                    if v['id'] == video_data['id']:
                        videos[i] = video_data
            else:
                # 插入到最前面（新视频在顶端）
                videos.insert(0, video_data)
                print(">>> 成功添加新视频！")
            
            save_data(videos)
            print(f"当前共有 {len(videos)} 个视频。请记得推送到 GitHub。")