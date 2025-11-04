"""
WhatsApp Chat Analyzer

This script parses an exported WhatsApp chat `.txt` file, filters messages by date range,
identifies repeated messages, and highlights the most active sender (spammer) in that period.

Features:
- Parses chat lines into structured DataFrame
- Filters messages by date range
- Detects repeated/spammed messages
- Identifies top spammer by message count

Usage:
Run the script with optional CLI arguments:
    python chat_analyzer.py --chat "path/to/chat.txt" --start "YYYY-MM-DD" --end "YYYY-MM-DD"

Default values:
- Chat file path: CHAT_FILE (hardcoded fallback)
- Date range: START_DATE to END_DATE (hardcoded fallback)

Note:
Ensure the exported chat file uses the default WhatsApp format (date, time, sender, message).
"""

import pandas as pd  # pyright: ignore[reportMissingModuleSource]
import re
import argparse
from datetime import datetime
from collections import Counter
import os

# Default fallback values
DEFAULT_CHAT_FILE = "whatsapp_chats/WhatsApp Chat with GNDU TECH CLUB.txt"
DEFAULT_START_DATE = "2025-10-01"
DEFAULT_END_DATE = "2025-11-04"

def parse_chat(chat_file: str) -> pd.DataFrame:
    """Parse WhatsApp exported chat file into a structured dataframe."""
    with open(chat_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    data = []
    chat_pattern = r"^(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2})\s?([apAP][mM]?) - (.*?): (.*)"

    for line in lines:
        match = re.match(chat_pattern, line)
        if match:
            date_str, time_str, am_pm, sender, message = match.groups()
            timestamp = f"{date_str} {time_str} {am_pm}".strip()
            try:
                date_obj = datetime.strptime(timestamp, "%d/%m/%y %I:%M %p")
            except:
                try:
                    date_obj = datetime.strptime(timestamp, "%d/%m/%Y %I:%M %p")
                except:
                    continue
            data.append([date_obj, sender, message])

    df = pd.DataFrame(data, columns=["datetime", "sender", "message"])
    return df

def filter_by_date(df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
    """Filter messages between date range."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    return df[(df["datetime"] >= start) & (df["datetime"] <= end)]

def find_repeated_messages(df: pd.DataFrame, threshold: int = 2) -> pd.Series:
    """Find repeated/spammed messages."""
    msg_counts = df["message"].value_counts()
    repeated = msg_counts[msg_counts > threshold]
    return repeated

def top_spammer(df: pd.DataFrame) -> tuple[str, int]:
    """Find who sent the most repeated messages."""
    sender_counts = df["sender"].value_counts()
    return sender_counts.idxmax(), sender_counts.max()

def main():
    parser = argparse.ArgumentParser(description="WhatsApp Chat Analyzer")
    parser.add_argument("--chat", type=str, default=DEFAULT_CHAT_FILE, help="Path to exported WhatsApp chat file")
    parser.add_argument("--start", type=str, default=DEFAULT_START_DATE, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, default=DEFAULT_END_DATE, help="End date (YYYY-MM-DD)")
    parser.add_argument("--threshold", type=int, default=2, help="Repetition threshold for spam detection")
    args = parser.parse_args()

    if not os.path.exists(args.chat):
        print(f"[ERROR] Chat file not found: {args.chat}")
        return

    print("[INFO] Loading chat...")
    df = parse_chat(args.chat)
    df = filter_by_date(df, args.start, args.end)

    print(f"\n[INFO] Messages from {args.start} to {args.end}: {len(df)} total")

    repeated = find_repeated_messages(df, threshold=args.threshold)
    if not repeated.empty:
        print("\n[REPEAT] Repeated messages:")
        for msg, count in repeated.items():
            safe_msg = msg[:40].encode("ascii", "ignore").decode("ascii")
            print(f"   - {safe_msg}... ({count} times)")
    else:
        print("\n[OK] No repeated messages found!")

    spammer, count = top_spammer(df)
    print(f"\n[ALERT] Top spammer: {spammer} ({count} messages)")

if __name__ == "__main__":
    main()