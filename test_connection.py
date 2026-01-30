# test_connection.py
# 연결 테스트용 스크립트

from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

print("="*50)
print("Supabase 연결 테스트")
print("="*50)

try:
    # Supabase 연결
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase 연결 성공!")
    
    # law_master 테이블 조회
    result = supabase.table('law_master').select('*').execute()
    
    if result.data:
        print(f"\n📋 등록된 법령: {len(result.data)}개")
        for law in result.data:
            print(f"  - {law['law_name']} ({law['law_type']})")
    else:
        print("\n⚠️  등록된 법령이 없습니다.")
        print("   대시보드에서 법령을 추가해주세요.")
    
    print("\n" + "="*50)
    print("테스트 완료!")
    print("="*50)
    
except Exception as e:
    print(f"\n❌ 오류 발생: {e}")
    print("\n다음 사항을 확인하세요:")
    print("  1. config.py의 SUPABASE_URL과 SUPABASE_KEY가 올바른지")
    print("  2. 인터넷 연결이 되어있는지")
    print("  3. Supabase 테이블이 생성되었는지")
