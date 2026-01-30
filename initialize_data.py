# initialize_data.py
# 최근 6개월간 법령 개정 이력 수집

from supabase import create_client
from datetime import datetime, timedelta
from law_api import LawAPI
from ai_analyzer import AIAnalyzer
from config import SUPABASE_URL, SUPABASE_KEY

class DataInitializer:
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.law_api = LawAPI()
        self.ai_analyzer = AIAnalyzer()
    
    def collect_recent_amendments(self, months=6):
        """최근 N개월간의 개정 이력 수집"""
        print(f"\n{'='*60}")
        print(f"최근 {months}개월간 법령 개정 이력 수집")
        print(f"{'='*60}\n")
        
        # 활성화된 법령 목록 조회
        result = self.supabase.table('law_master')\
            .select('*')\
            .eq('is_active', True)\
            .execute()
        
        laws = result.data
        
        if not laws:
            print("모니터링할 법령이 없습니다.")
            print("대시보드에서 법령을 추가해주세요.")
            return
        
        # 날짜 범위 계산
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30 * months)
        
        print(f"📅 수집 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}\n")
        
        total_amendments = 0
        
        for law in laws:
            print(f"\n📋 {law['law_name']} 처리 중...")
            
            try:
                # 법령 검색
                search_results = self.law_api.search_law(law['law_name'])
                
                if not search_results:
                    print(f"  ⚠️  검색 결과 없음")
                    continue
                
                law_id = search_results[0].get('law_id')
                
                if not law_id:
                    print(f"  ⚠️  법령 ID 없음")
                    continue
                
                # 개정 연혁 조회
                print(f"  🔍 개정 연혁 조회 중...")
                amendments = self.law_api.get_amendment_history(law_id)
                
                if not amendments:
                    print(f"  ⚠️  개정 연혁 없음")
                    continue
                
                # 최근 6개월 데이터만 필터링
                recent_amendments = []
                for amend in amendments:
                    if amend.get('amend_date'):
                        amend_date = self._parse_date(amend['amend_date'])
                        if start_date <= amend_date <= end_date:
                            recent_amendments.append(amend)
                
                print(f"  📊 총 {len(amendments)}개 중 최근 6개월: {len(recent_amendments)}개")
                
                # 개정 이력 저장
                saved_count = 0
                for amend in recent_amendments:
                    try:
                        # 중복 체크
                        amend_date = self._parse_date(amend['amend_date']).date().isoformat()
                        
                        existing = self.supabase.table('law_amendments')\
                            .select('id')\
                            .eq('law_code', law['law_code'])\
                            .eq('amendment_date', amend_date)\
                            .execute()
                        
                        if existing.data:
                            continue  # 이미 존재하면 건너뛰기
                        
                        # AI 분석 (내용이 있는 경우만)
                        content = amend.get('content', '')
                        if content and len(content) > 100:
                            print(f"    🤖 AI 분석 중...")
                            analysis = self.ai_analyzer.analyze_amendment(
                                law['law_name'],
                                content[:5000]
                            )
                        else:
                            analysis = {
                                'summary': '개정 내용 요약 없음',
                                'impact_analysis': '',
                                'tasks': []
                            }
                        
                        # 개정 이력 저장
                        amendment_data = {
                            'law_code': law['law_code'],
                            'amendment_date': amend_date,
                            'enforcement_date': self._parse_date(amend.get('enf_date')).date().isoformat() if amend.get('enf_date') else None,
                            'amendment_no': amend.get('amend_no'),
                            'amendment_type': amend.get('amend_type'),
                            'original_text': content,
                            'summary': analysis['summary'],
                            'impact_analysis': analysis['impact_analysis'],
                            'is_reviewed': False
                        }
                        
                        insert_result = self.supabase.table('law_amendments').insert(amendment_data).execute()
                        
                        if insert_result.data:
                            saved_count += 1
                            amendment_id = insert_result.data[0]['id']
                            
                            # 후속 업무 생성
                            self._create_follow_up_tasks(amendment_id, analysis['tasks'], law)
                        
                    except Exception as e:
                        print(f"    ⚠️  개정 이력 저장 오류: {e}")
                        continue
                
                print(f"  ✅ {saved_count}개 개정 이력 저장 완료")
                total_amendments += saved_count
                
                # 최종 개정일 업데이트
                if recent_amendments:
                    latest = max(recent_amendments, key=lambda x: self._parse_date(x.get('amend_date', '')))
                    latest_date = self._parse_date(latest['amend_date']).date().isoformat()
                    
                    self.supabase.table('law_master')\
                        .update({'last_amendment_date': latest_date})\
                        .eq('id', law['id'])\
                        .execute()
                
            except Exception as e:
                print(f"  ❌ 오류: {e}")
                continue
        
        print(f"\n{'='*60}")
        print(f"수집 완료: 총 {total_amendments}개 개정 이력 저장")
        print(f"{'='*60}\n")
    
    def _create_follow_up_tasks(self, amendment_id, tasks, law_data):
        """후속 업무 생성"""
        if not tasks:
            return
        
        manager = law_data.get('manager', '담당자')
        
        task_type_map = {
            'manual': '매뉴얼수정',
            'training': '교육',
            'document': '문서개정',
            'inspection': '점검',
            'other': '기타'
        }
        
        for task in tasks[:5]:
            task_data = {
                'amendment_id': amendment_id,
                'task_type': task_type_map.get(task['type'], '기타'),
                'task_title': task['title'][:200],
                'task_description': task['title'],
                'priority': 'high',
                'assignee': manager,
                'due_date': (datetime.now() + timedelta(days=30)).date().isoformat(),
                'status': 'pending'
            }
            
            try:
                self.supabase.table('follow_up_tasks').insert(task_data).execute()
            except:
                pass
    
    def _parse_date(self, date_str):
        """날짜 문자열 파싱"""
        if not date_str:
            return datetime.now()
        
        date_str = date_str.replace('-', '').replace('.', '').replace('/', '')
        
        try:
            return datetime.strptime(date_str[:8], '%Y%m%d')
        except:
            return datetime.now()

def main():
    print("\n" + "="*60)
    print("법령 개정 이력 초기 데이터 수집")
    print("="*60)
    
    initializer = DataInitializer()
    
    # 최근 6개월 데이터 수집
    initializer.collect_recent_amendments(months=6)
    
    print("\n초기 데이터 수집이 완료되었습니다!")
    print("웹 대시보드를 새로고침하여 결과를 확인하세요.\n")

if __name__ == "__main__":
    main()
