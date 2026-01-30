# config.py
import os

# Supabase 설정
SUPABASE_URL = "https://qiwqcylerloqxdqupgbk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFpd3FjeWxlcmxvcXhkcXVwZ2JrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk0MTQxMzMsImV4cCI6MjA3NDk5MDEzM30.haR8oLJsgp_5r-EisNqxI8ASHrdh87hiAixfMt5TG6U"

# 법제처 API 설정
LAW_API_OC = "lawmonitor2025"
LAW_API_BASE_URL = "https://www.law.go.kr/DRF"

# Claude API 설정 (나중에 추가)
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")  # 환경변수에서 가져오기

# 모니터링 설정
CHECK_INTERVAL_HOURS = 24  # 24시간마다 체크
