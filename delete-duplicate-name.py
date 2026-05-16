#!/usr/bin/env python3
# delete_duplicate_name.py
"""
Remove duplicate config lines from protocol files (base64 encoded).
Supports both single files (vless.txt) and multi-part files (vless_1.txt, vless_2.txt, ...)
"""

import os
import base64
import time
import re
from typing import List

def decode_base64_file(filepath: str) -> str:
    """Decode file content (base64) to string, skip if invalid."""
    with open(filepath, 'r', encoding='utf-8') as f:
        raw = f.read().strip()
    if not raw:
        return ''
    try:
        return base64.b64decode(raw).decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  ❌ Decode error in {filepath}: {e}")
        return ''

def encode_and_write(filepath: str, lines: List[str]) -> None:
    """Encode lines as base64 and write back."""
    text = '\n'.join(lines)
    encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(encoded)

def deduplicate_file(filepath: str) -> None:
    """Remove duplicate lines from a single file."""
    print(f"\n📄 Processing: {filepath}")
    start = time.perf_counter()
    
    decoded = decode_base64_file(filepath)
    if not decoded:
        print(f"  ⚠️ Empty or unreadable, skipped.")
        return
    
    lines = [line.strip() for line in decoded.splitlines() if line.strip()]
    original_count = len(lines)
    
    if original_count == 0:
        print(f"  ⚠️ No valid lines found.")
        return
    
    unique_lines = list(set(lines))
    duplicates_removed = original_count - len(unique_lines)
    
    if duplicates_removed == 0:
        print(f"  ✅ No duplicates found. ({original_count:,} lines)")
        return
    
    encode_and_write(filepath, unique_lines)
    
    elapsed = time.perf_counter() - start
    print(f"  ✅ Removed {duplicates_removed:,} duplicates. "
          f"Result: {len(unique_lines):,} lines (was {original_count:,}) - {elapsed:.2f}s")

def main():
    print("🚀 Starting duplicate removal...")
    start_total = time.perf_counter()
    processed = 0
    
    # الگوی نام فایل‌های مجاز
    pattern = re.compile(r'^(vless|reality|vmess|trojan|hysteria2|ss|socks|wireguard)(_\d+)?\.txt$')
    
    for entry in os.scandir('.'):
        if entry.is_file() and pattern.match(entry.name):
            deduplicate_file(entry.path)
            processed += 1
    
    elapsed = time.perf_counter() - start_total
    print(f"\n✨ Done. Processed {processed} files in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()