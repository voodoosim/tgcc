#!/usr/bin/env python3
# demo_attendance_bot.py
"""Demo script showing attendance bot functionality without Telegram"""

import sys
from pathlib import Path
import os

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from attendance_bot.db import AttendanceDB
from attendance_bot.utils import (
    get_korean_date_string, 
    format_attendance_message,
    format_already_attended_message,
    format_stats_message,
    format_leaderboard_message
)

def demo_attendance_system():
    """Demonstrate the attendance bot system"""
    print("🎮 텔레그램 출석체크 봇 데모")
    print("=" * 50)
    
    # Initialize database
    db_path = "demo_attendance.db"
    db = AttendanceDB(db_path)
    
    # Demo users
    users = [
        ("123456789", "홍길동"),
        ("987654321", "김철수"), 
        ("555666777", "이영희"),
        ("111222333", "박민수"),
        ("444555666", "최지영")
    ]
    
    today = get_korean_date_string()
    print(f"📅 오늘 날짜: {today}\n")
    
    # Simulate first attendance for each user
    print("👥 사용자들의 첫 출석체크:")
    print("-" * 30)
    
    for user_id, nickname in users[:3]:  # First 3 users attend
        success = db.record_attendance(user_id, nickname, today, 100)
        if success:
            stats = db.get_user_stats(user_id)
            message = format_attendance_message(
                stats['nickname'], 
                100, 
                stats['total_points'], 
                stats['total_attendance']
            )
            print(f"사용자: {nickname}")
            print(message)
            print()
    
    # Simulate duplicate attendance attempt
    print("🔄 중복 출석체크 시도:")
    print("-" * 30)
    
    user_id, nickname = users[0]  # First user tries again
    if db.check_attendance_today(user_id, today):
        stats = db.get_user_stats(user_id)
        message = format_already_attended_message(stats['nickname'], stats['total_points'])
        print(f"사용자: {nickname}")
        print(message)
        print()
    
    # Show individual stats
    print("📊 개인 통계 조회:")
    print("-" * 30)
    
    user_id, nickname = users[0]
    stats = db.get_user_stats(user_id)
    if stats:
        message = format_stats_message(stats)
        print(f"사용자: {nickname}")
        print(message)
        print()
    
    # Show leaderboard
    print("🏆 출석 리더보드:")
    print("-" * 30)
    
    top_users = db.get_top_users(10)
    leaderboard_message = format_leaderboard_message(top_users)
    print(leaderboard_message)
    print()
    
    # Simulate multi-day attendance for one user
    print("📈 연속 출석 시뮬레이션 (홍길동):")
    print("-" * 30)
    
    from datetime import datetime, timedelta
    base_date = datetime.now()
    user_id, nickname = users[0]
    
    for i in range(1, 8):  # Simulate 7 days of attendance
        date_str = (base_date - timedelta(days=i)).strftime("%Y-%m-%d")
        db.record_attendance(user_id, nickname, date_str, 100)
    
    # Show updated stats
    stats = db.get_user_stats(user_id)
    if stats:
        print(f"🔥 {nickname}님의 업데이트된 통계:")
        message = format_stats_message(stats)
        print(message)
        print()
        
        # Show recent history
        history = db.get_attendance_history(user_id, 5)
        if history:
            print("📅 최근 출석 기록:")
            for record in history:
                print(f"• {record['date']} (+{record['points']}포인트)")
            print()
    
    # Final leaderboard
    print("🥇 최종 리더보드:")
    print("-" * 30)
    
    top_users = db.get_top_users(10)
    leaderboard_message = format_leaderboard_message(top_users)
    print(leaderboard_message)
    
    # Cleanup
    print("\n🧹 데모 정리 중...")
    os.remove(db_path)
    print("✅ 데모 완료!")

if __name__ == "__main__":
    try:
        demo_attendance_system()
    except KeyboardInterrupt:
        print("\n⛔ 데모가 중단되었습니다.")
    except Exception as e:
        print(f"❌ 데모 중 오류 발생: {e}")