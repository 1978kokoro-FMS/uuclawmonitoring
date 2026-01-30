# debug_law_api.py
# 법제처 API 상세 디버깅

import requests
from config import LAW_API_BASE_URL, LAW_API_OC

print("\n" + "="*60)
print("법제처 API 상세 디버깅")
print("="*60 + "\n")

# API 설정 출력
print("📋 API 설정:")
print(f"   OC 값: {LAW_API_OC}")
print(f"   Base URL: {LAW_API_BASE_URL}\n")

# 실제 API 호출
url = f"{LAW_API_BASE_URL}/lawSearch.do"
params = {
    "OC": LAW_API_OC,
    "target": "law",
    "type": "XML",
    "query": "산업안전보건법"
}

print(f"🌐 요청 URL: {url}")
print(f"📤 파라미터: {params}\n")

try:
    print("🔄 API 요청 중...")
    response = requests.get(url, params=params, timeout=30)
    
    print(f"📥 응답 상태: {response.status_code}")
    print(f"📥 응답 크기: {len(response.text)} bytes\n")
    
    if response.status_code == 200:
        print("✅ API 응답 성공!\n")
        
        # 응답 내용 출력 (처음 1000자)
        print("="*60)
        print("응답 내용 (처음 1000자):")
        print("="*60)
        print(response.text[:1000])
        print("="*60 + "\n")
        
        # XML 파싱 시도
        from bs4 import BeautifulSoup
        
        print("🔍 XML 파싱 시도...\n")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 에러 메시지 확인
        error_code = soup.find('errCode')
        error_msg = soup.find('errMsg')
        
        if error_code and error_code.text != '0':
            print(f"❌ API 오류:")
            print(f"   오류 코드: {error_code.text}")
            print(f"   오류 메시지: {error_msg.text if error_msg else 'N/A'}")
        else:
            # 법령 결과 파싱
            laws = soup.find_all('law')
            
            if laws:
                print(f"✅ {len(laws)}개 법령 발견!\n")
                
                for i, law in enumerate(laws[:3], 1):
                    print(f"[{i}] 법령 정보:")
                    
                    # 모든 하위 태그 출력
                    for tag in law.find_all():
                        if tag.text and tag.name:
                            print(f"    {tag.name}: {tag.text[:100]}")
                    print()
            else:
                print("⚠️  law 태그를 찾을 수 없습니다.")
                print("    전체 태그 목록:")
                for tag in soup.find_all()[:10]:
                    print(f"    - {tag.name}: {tag.text[:50] if tag.text else ''}")
    else:
        print(f"❌ API 응답 실패!")
        print(f"   상태 코드: {response.status_code}")
        print(f"   응답 내용: {response.text[:500]}")
        
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("디버깅 완료!")
print("="*60 + "\n")
