# 법령 모니터링 시스템 설치 가이드

## ⚠️ 설치 중 오류 발생 시 이 가이드를 따라하세요!

### 1단계: pip 업그레이드

```powershell
python -m pip install --upgrade pip
```

### 2단계: 패키지 하나씩 설치

오류가 발생하면 한 번에 설치하지 말고 하나씩 설치하세요:

```powershell
pip install supabase
pip install requests
pip install python-dateutil
pip install beautifulsoup4
pip install anthropic
```

### 3단계: lxml 설치 (선택사항)

lxml이 설치되지 않으면 다음 중 하나를 시도하세요:

**방법 1: Prebuilt wheel 설치**
```powershell
pip install lxml --only-binary :all:
```

**방법 2: lxml 건너뛰기**
lxml은 선택사항입니다. 없어도 기본 기능은 작동합니다.

### 4단계: 연결 테스트

```powershell
cd C:\Users\kokor\Desktop\law_monitoring
python test_connection.py
```

### 5단계: 대시보드 수정

`dashboard/index.html` 파일을 열고, `<head>` 태그 안에 다음 줄을 추가:

```html
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
```

위치: `<title>` 태그 다음, `<link rel="stylesheet">` 앞

---

## 💡 빠른 해결 방법

위 방법이 복잡하다면, 다음 명령어 하나로 해결:

```powershell
pip install supabase requests python-dateutil beautifulsoup4 anthropic
```

lxml은 건너뛰어도 괜찮습니다!

---

## ✅ 설치 확인

다음 명령어로 설치된 패키지 확인:

```powershell
pip list | findstr "supabase requests beautifulsoup4 anthropic"
```

모두 표시되면 성공! 🎉
