#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量下载 IMSDb 电影剧本
从 movie_list.txt 读取 URL，提取纯文本并保存到 data/raw_scripts/
"""

import os
import re
import time
import urllib.request
import urllib.error

# 剧本 URL 映射（movie_list.txt 中提取）
SCRIPTS = {
    "The_Shawshank_Redemption.txt": "http://imsdb.com/scripts/Shawshank-Redemption,-The.html",
    "Forrest_Gump.txt": "http://imsdb.com/scripts/Forrest-Gump.html",
    "Titanic.txt": "http://imsdb.com/scripts/Titanic.html",
    "American_Beauty.txt": "http://imsdb.com/scripts/American-Beauty.html",
    "Pulp_Fiction.txt": "http://imsdb.com/scripts/Pulp-Fiction.html",
    "Memento.txt": "http://imsdb.com/scripts/Memento.html",
    "Fight_Club.txt": "http://imsdb.com/scripts/Fight-Club.html",
    "Saving_Private_Ryan.txt": "http://imsdb.com/scripts/Saving-Private-Ryan.html",
    "Inception.txt": "http://imsdb.com/scripts/Inception.html",
    "The_Matrix.txt": "http://imsdb.com/scripts/Matrix,-The.html",
    "Toy_Story.txt": "http://imsdb.com/scripts/Toy-Story.html",
    "Good_Will_Hunting.txt": "http://imsdb.com/scripts/Good-Will-Hunting.html",
}


def extract_script(html_text):
    """从 HTML 中提取剧本正文"""
    # 找到 <pre> 标签内的内容（第二个 pre 块才是真正的剧本）
    parts = html_text.split('<pre>')
    if len(parts) < 2:
        return None

    # 取最后一个 pre 块的内容
    script_part = parts[-1]
    end_idx = script_part.find('</pre>')
    if end_idx != -1:
        script_part = script_part[:end_idx]

    # 去除 HTML 标签（保留 <b> 只是为了标记，这里去掉）
    script_text = re.sub(r'<[^>]+>', '', script_part)

    # 去除 script 标签残留
    script_text = re.sub(r'if \(window!= top\)[\s\S]*?location\.href', '', script_text)

    # 解码 HTML 实体
    script_text = script_text.replace('&nbsp;', ' ')
    script_text = script_text.replace('&amp;', '&')
    script_text = script_text.replace('&lt;', '<')
    script_text = script_text.replace('&gt;', '>')
    script_text = script_text.replace('&quot;', '"')
    script_text = script_text.replace('&#39;', "'")

    # 清理多余空行
    script_text = re.sub(r'\r\n', '\n', script_text)
    script_text = re.sub(r'\n{4,}', '\n\n\n', script_text)

    return script_text.strip()


def download_script(url, filename, output_dir):
    """下载单个剧本并保存"""
    filepath = os.path.join(output_dir, filename)
    print(f"\n{'='*60}")
    print(f">> 下载: {filename}")
    print(f"   URL: {url}")

    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/120.0.0.0 Safari/537.36'
            }
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('iso-8859-1', errors='replace')
    except Exception as e:
        print(f"   !! 下载失败: {e}")
        return False

    script_text = extract_script(html)
    if not script_text or len(script_text) < 500:
        print(f"   !! 提取失败（内容过短: {len(script_text) if script_text else 0} 字符）")
        return False

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(script_text)

    line_count = script_text.count('\n')
    word_count = len(script_text.split())
    print(f"   OK 保存成功: {len(script_text)} 字, {line_count} 行, ~{word_count} 词")
    return True


def main():
    # 输出目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.abspath(os.path.join(script_dir, '..', 'data', 'raw_scripts'))
    os.makedirs(output_dir, exist_ok=True)

    print("IMSDb 电影剧本批量下载工具")
    print(f"   输出目录: {output_dir}")
    print(f"   共 {len(SCRIPTS)} 部电影\n")

    success = 0
    fail = 0

    for filename, url in SCRIPTS.items():
        if download_script(url, filename, output_dir):
            success += 1
        else:
            fail += 1
        time.sleep(1)  # 礼貌间隔，避免被 ban

    print(f"\n{'='*60}")
    print(f"下载完成: {success} 成功, {fail} 失败, 共 {len(SCRIPTS)} 部")
    print(f"保存目录: {output_dir}")

    if success > 0:
        print(f"\n下一步：运行 preprocess.py 清洗数据")
        print(f"   python scripts/preprocess.py")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
