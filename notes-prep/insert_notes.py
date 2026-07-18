#!/usr/bin/env python3
"""Insert all notes into TiDB Cloud database."""

import os
import sys
import mysql.connector

NOTES_DIR = r'E:\Claudecode\personal-site\notes-prep'

# Database config
DB_CONFIG = {
    'host': 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '28bKJwXcdrmiau1.root',
    'password': 'UEB4Z0TNixwRvvzH',
    'database': 'personal_site',
    'ssl_ca': None,
    'ssl_verify_cert': True,
}

# Course definitions
COURSE_MAP = {
    'DB': ('数据库原理', '期末复习'),
    'OS': ('操作系统', '期末复习'),
    'PROB': ('概率论与数理统计', '期末复习'),
    'POL': ('习近平新时代中国特色社会主义思想概论', '期末复习'),
}

def get_title_tag(filename):
    """Extract course prefix and title from filename."""
    # filename: OS-01-引论.md -> prefix=OS, title=OS-01 引论
    prefix = filename[:4]  # e.g., "OS-0", "DB-0"
    prefix2 = filename[:3]  # e.g., "OS-", "DB-"

    # Clean up
    if '-' in filename and filename.count('-') >= 2:
        parts = filename.replace('.md', '').split('-', 2)
        course_prefix = parts[0]
        num = parts[1]
        name = parts[2] if len(parts) > 2 else ''
        title = f"{course_prefix}-{num} {name}"
        return course_prefix, title

    return None, filename.replace('.md', '').replace('-', ' ')

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--dry-run':
        dry_run = True
        print("=== DRY RUN MODE ===\n")
    else:
        dry_run = False
        print("=== INSERTING NOTES TO TiDB ===\n")

    try:
        if not dry_run:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            print("Connected to TiDB Cloud.\n")
    except Exception as e:
        print(f"Connection failed: {e}")
        print("Use --dry-run to preview without inserting.")
        sys.exit(1)

    files = sorted([f for f in os.listdir(NOTES_DIR) if f.endswith('.md') and '-' in f])

    for fn in files:
        path = os.path.join(NOTES_DIR, fn)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        prefix, title = get_title_tag(fn)
        course_name = COURSE_MAP.get(prefix, (None, None))[0]
        tag = COURSE_MAP.get(prefix, (None, None))[1]

        if not course_name:
            print(f"  ⚠ Skipping {fn}: unknown course prefix '{prefix}'")
            continue

        tags_json = f'["{course_name}", "{tag}"]'

        if dry_run:
            print(f"  [{course_name}] {title}")
            print(f"    Content: {len(content)} chars")
            print(f"    Tags: {tags_json}")
            continue

        try:
            sql = "INSERT INTO notes (title, content, course, tags) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (title, content, course_name, tags_json))
            conn.commit()
            note_id = cursor.lastrowid
            print(f"  ✓ [{course_name}] {title} -> id={note_id}")
        except Exception as e:
            print(f"  ✗ [{course_name}] {title}: {e}")

    if not dry_run:
        cursor.close()
        conn.close()
        print("\nAll notes inserted!")
    else:
        print(f"\n{len(files)} notes ready for insertion.")
        print("Run without --dry-run to actually insert.")

if __name__ == '__main__':
    main()
