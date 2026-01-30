# monitor.py
from supabase import create_client
from datetime import datetime, timedelta
from law_api import LawAPI
from ai_analyzer import AIAnalyzer
from config import SUPABASE_URL, SUPABASE_KEY
import time

class LawMonitor:
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.law_api = LawAPI()
        self.ai_analyzer = AIAnalyzer()
    
    def check_all_laws(self):
        """모든 활성 법령 확인"""
        print(f"\n{'='*50}")
        print(f"법령 모니터링 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}\n")
        
        start_time = time.time()
        
        try:
            # 활성화된 법령 목록 조회
            result = self.supabase.table('law_master')\
                .select('*')\
                .eq('is_active', True)\
                .execute()
            
            laws = result.data
            
            if not laws:
                print("모니터링할 법령이 없습니다.")
                return
            
            print(f"총 {len(laws)}개 법령 확인 중...\n")
            
            changes_found = 0
            
            for law in laws:
                print(f"📋 {law['law_name']} 확인 중...")
                
                try:
                    has_changes = self.check_law(law)
                    if has_changes:
                        changes_found += 1
                        print(f"  ✅ 변경사항 발견!")
                    else:
                        print(f"  ⏺️  변경사항 없음")
                    
                    # 마지막 확인일 업데이트
                    self.supabase.table('law_master')\
                        .update({'last_check_date': datetime.now().isoformat()})\
                        .eq('id', law['id'])\
                        .execute()
                    
                except Exception as e:
                    print(f"  ❌ 오류: {e}")
                    self._log_error(law['law_code'], str(e))
                
                print()
            
            execution_time = int(time.time() - start_time)
            
            # 모니터링 로그 기록
            self.supabase.table('monitoring_logs').insert({
                'check_date': datetime.now().isoformat(),
                'law_code': 'ALL',
                'status': 'success',
                'changes_detected': changes_found > 0,
                'execution_time': execution_time
            }).execute()
            
            print(f"{'='*50}")
            print(f"모니터링 완료: 총 {changes_found}건의 변경사항 발견")
            print(f"실행 시간: {execution_time}초")
            print(f"{'='*50}\n")
            
        except Exception as e:
            print(f"모니터링 오류: {e}")
            self._log_error('ALL', str(e))
    
    def check_law(self, law_data):
        """개별 법령 확인"""
        law_code = law_data['law_code']
        law_name = law_data['law_name']
        last_amendment = law_data.get('last_amendment_date')
        
        # 법령 검색
        search_results = self.law_api.search_law(law_name)
        
        if not search_results:
            print(f"  ⚠️  법령 검색 결과 없음")
            return False
        
        # 첫 번째 결과 사용
        law_info = search_results[0]
        current_amend_date = law_info.get('amend_date')
        
        if not current_amend_date:
            return False
        
        # 날짜 비교
        current_date = self._parse_date(current_amend_date)
        
        if last_amendment:
            last_date = self._parse_date(last_amendment)
            if current_date <= last_date:
                return False  # 변경사항 없음
        
        # 새로운 개정 발견!
        print(f"  🆕 새 개정 발견: {current_amend_date}")
        
        # 상세 정보 조회
        law_id = law_info.get('law_id')
        if law_id:
            detail_info = self.law_api.get_law_info(law_id)
            if detail_info:
                self._save_amendment(law_data, detail_info)
        
        # 최종 개정일 업데이트
        self.supabase.table('law_master')\
            .update({'last_amendment_date': current_date.date().isoformat()})\
            .eq('law_code', law_code)\
            .execute()
        
        return True
    
    def _save_amendment(self, law_data, amendment_info):
        """개정 정보 저장 및 분석"""
        law_code = law_data['law_code']
        
        # 원문 내용
        content = amendment_info.get('content', '')
        
        # AI 분석
        print(f"  🤖 AI 분석 중...")
        analysis = self.ai_analyzer.analyze_amendment(
            law_data['law_name'],
            content[:5000]  # 최대 5000자까지만
        )
        
        # 개정 이력 저장
        amendment_data = {
            'law_code': law_code,
            'amendment_date': self._parse_date(amendment_info.get('amend_date')).date().isoformat(),
            'enforcement_date': self._parse_date(amendment_info.get('enf_date')).date().isoformat() if amendment_info.get('enf_date') else None,
            'amendment_no': amendment_info.get('amend_no'),
            'amendment_type': amendment_info.get('law_type'),
            'original_text': content,
            'summary': analysis['summary'],
            'impact_analysis': analysis['impact_analysis'],
            'is_reviewed': False
        }
        
        result = self.supabase.table('law_amendments').insert(amendment_data).execute()
        
        if result.data:
            amendment_id = result.data[0]['id']
            
            # 후속 업무 생성
            self._create_follow_up_tasks(amendment_id, analysis['tasks'], law_data)
    
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
        
        for task in tasks[:5]:  # 최대 5개까지
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
            
            self.supabase.table('follow_up_tasks').insert(task_data).execute()
    
    def _parse_date(self, date_str):
        """날짜 문자열 파싱"""
        if not date_str:
            return datetime.now()
        
        # YYYYMMDD 형식
        date_str = date_str.replace('-', '').replace('.', '').replace('/', '')
        
        try:
            return datetime.strptime(date_str[:8], '%Y%m%d')
        except:
            return datetime.now()
    
    def _log_error(self, law_code, error_message):
        """오류 로그 기록"""
        self.supabase.table('monitoring_logs').insert({
            'check_date': datetime.now().isoformat(),
            'law_code': law_code,
            'status': 'error',
            'changes_detected': False,
            'error_message': error_message
        }).execute()

def main():
    """메인 실행"""
    monitor = LawMonitor()
    monitor.check_all_laws()

if __name__ == "__main__":
    main()
