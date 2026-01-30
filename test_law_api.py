# test_law_api.py
# 법제처 API 테스트

from law_api import LawAPI

def test_api():
    print("\n" + "="*60)
    print("법제처 API 연결 테스트")
    print("="*60 + "\n")
    
    api = LawAPI()
    
    # 테스트 1: 법령 검색
    print("1. 산업안전보건법 검색 중...")
    results = api.search_law("산업안전보건법")
    
    if results:
        print(f"   ✅ 검색 성공! {len(results)}개 결과 발견\n")
        
        for i, law in enumerate(results[:3], 1):
            print(f"   [{i}] 법령명: {law.get('law_name', 'N/A')}")
            print(f"       법령ID: {law.get('law_id', 'N/A')}")
            print(f"       법령구분: {law.get('law_type', 'N/A')}")
            print(f"       공포일자: {law.get('amend_date', 'N/A')}")
            print(f"       시행일자: {law.get('enf_date', 'N/A')}")
            print()
        
        # 테스트 2: 첫 번째 법령의 상세 정보
        if results[0].get('law_id'):
            law_id = results[0]['law_id']
            print(f"2. 법령 상세 정보 조회 (ID: {law_id})...")
            
            detail = api.get_law_info(law_id)
            
            if detail:
                print(f"   ✅ 상세 정보 조회 성공!")
                print(f"   법령명: {detail.get('law_name', 'N/A')}")
                print(f"   공포일자: {detail.get('amend_date', 'N/A')}")
                print(f"   시행일자: {detail.get('enf_date', 'N/A')}")
                print(f"   공포번호: {detail.get('amend_no', 'N/A')}")
                
                content = detail.get('content', '')
                if content:
                    print(f"   조문내용: {len(content)}자 (처음 100자: {content[:100]}...)")
                else:
                    print(f"   조문내용: 없음")
                print()
            else:
                print(f"   ⚠️  상세 정보 조회 실패")
                print()
            
            # 테스트 3: 개정 연혁
            print(f"3. 개정 연혁 조회 중...")
            amendments = api.get_amendment_history(law_id)
            
            if amendments:
                print(f"   ✅ 개정 연혁 조회 성공! {len(amendments)}개 발견\n")
                
                print(f"   최근 5개 개정 이력:")
                for i, amend in enumerate(amendments[:5], 1):
                    print(f"   [{i}] 공포일자: {amend.get('amend_date', 'N/A')}")
                    print(f"       시행일자: {amend.get('enf_date', 'N/A')}")
                    print(f"       개정구분: {amend.get('amend_type', 'N/A')}")
                    print(f"       공포번호: {amend.get('amend_no', 'N/A')}")
                    print()
                
            else:
                print(f"   ⚠️  개정 연혁 없음")
                print()
    else:
        print(f"   ❌ 검색 실패!")
        print(f"   법제처 API 연결을 확인하세요.")
        print(f"   - OC 값: {api.oc}")
        print(f"   - API URL: {api.base_url}")
    
    print("="*60)
    print("테스트 완료!")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_api()
