# 법령 개정 모니터링 시스템

의왕도시공사 안전감사팀용 법령 개정 자동 모니터링 시스템입니다.

## 📋 기능

- ✅ 법령 자동 모니터링 (법제처 API 연동)
- ✅ 개정 내용 AI 분석 (Claude API)
- ✅ 후속 업무 자동 생성
- ✅ 웹 대시보드 제공

## 🚀 설치 방법

### 1. Python 설치
Python 3.8 이상이 필요합니다.

### 2. 필요한 패키지 설치

```bash
cd C:\Users\kokor\Desktop\law_monitoring
pip install -r requirements.txt
```

### 3. Claude API Key 설정 (선택사항)

AI 분석 기능을 사용하려면 환경변수에 Claude API Key를 설정하세요:

**Windows PowerShell:**
```powershell
$env:CLAUDE_API_KEY = "your-api-key-here"
```

**Windows CMD:**
```cmd
set CLAUDE_API_KEY=your-api-key-here
```

## 📊 사용 방법

### 1. 모니터링 실행

```bash
python monitor.py
```

이 명령어를 실행하면:
- Supabase의 law_master 테이블에서 활성화된 법령을 조회
- 법제처 API로 최신 개정 여부 확인
- 개정 발견 시 AI 분석 후 Supabase에 저장
- 후속 업무 자동 생성

### 2. 웹 대시보드 사용

**방법 1: 간단한 로컬 서버 (Python)**

```bash
cd dashboard
python -m http.server 8000
```

브라우저에서 `http://localhost:8000` 접속

**방법 2: VS Code Live Server**

- VS Code에서 `dashboard/index.html` 열기
- 우클릭 → "Open with Live Server"

**방법 3: 직접 파일 열기**

`dashboard/index.html` 파일을 더블클릭하여 브라우저에서 직접 열기

### 대시보드 기능

1. **개정 현황 탭**
   - 최근 법령 개정 목록 확인
   - AI 요약본 확인
   - 상세 내용 보기
   - 검토 완료 표시

2. **법령 관리 탭**
   - 모니터링할 법령 추가/관리
   - 법령별 활성화/비활성화
   - 담당자 지정

3. **후속 업무 탭**
   - 개정에 따른 후속 업무 확인
   - 업무 상태 관리 (대기중/진행중/완료)
   - 담당자 배정

4. **모니터링 로그 탭**
   - 시스템 실행 이력 확인
   - 오류 발생 확인

## 📅 자동화 설정

### Windows 작업 스케줄러

1. 작업 스케줄러 실행
2. "기본 작업 만들기" 클릭
3. 설정:
   - 이름: "법령 모니터링"
   - 트리거: 매일 오전 9시
   - 작업: 프로그램 시작
   - 프로그램: `python`
   - 인수: `C:\Users\kokor\Desktop\law_monitoring\monitor.py`
   - 시작 위치: `C:\Users\kokor\Desktop\law_monitoring`

### GitHub Actions (무료 자동화)

프로젝트를 GitHub에 업로드하고 Actions로 매일 자동 실행 가능합니다.

## 🔧 Render.com 배포 (무료)

### 1. GitHub에 업로드

```bash
cd C:\Users\kokor\Desktop\law_monitoring
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/law-monitoring.git
git push -u origin main
```

### 2. Render.com 설정

1. https://render.com 가입
2. "New +" → "Web Service" 선택
3. GitHub 저장소 연결
4. 설정:
   - Name: law-monitoring
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python monitor.py`
   - Plan: Free

5. Environment Variables 추가:
   - `CLAUDE_API_KEY`: (Claude API 키)

6. Cron Job 설정:
   - "New +" → "Cron Job" 선택
   - Schedule: `0 9 * * *` (매일 오전 9시)
   - Command: `python monitor.py`

## 📁 파일 구조

```
law_monitoring/
├── config.py           # 설정 파일
├── law_api.py          # 법제처 API 연동
├── ai_analyzer.py      # Claude AI 분석
├── monitor.py          # 메인 모니터링 스크립트
├── requirements.txt    # 필요한 패키지
├── README.md          # 이 파일
└── dashboard/
    ├── index.html     # 웹 대시보드
    ├── style.css      # 스타일
    └── app.js         # JavaScript
```

## 🔐 보안 주의사항

- `config.py`에 API 키가 포함되어 있으므로 GitHub에 업로드 시 주의
- `.gitignore` 파일을 만들어 `config.py` 제외 권장
- 환경변수 사용 권장

## ❓ 문제 해결

### 패키지 설치 오류
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### Supabase 연결 오류
- config.py의 URL과 API Key 확인
- Supabase 테이블이 올바르게 생성되었는지 확인

### 법제처 API 오류
- OC 값이 올바른지 확인
- 인터넷 연결 확인

## 📞 지원

문제 발생 시:
1. 오류 메시지 확인
2. monitoring_logs 테이블에서 로그 확인
3. Python 버전 및 패키지 버전 확인

---

**의왕도시공사 안전감사팀**
2025년 1월
