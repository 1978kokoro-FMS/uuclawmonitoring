from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime, timedelta
from supabase import create_client, Client
import requests
import xml.etree.ElementTree as ET
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__, static_folder='dashboard')
CORS(app)

# 환경 변수
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')
LAW_API_KEY = os.environ.get('LAW_API_KEY', '')

# Supabase 클라이언트
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 메인 페이지
@app.route('/')
def index():
    return send_from_directory('dashboard', 'index.html')

# 정적 파일 서빙
@app.route('/<path:path>')
def send_static(path):
    try:
        return send_from_directory('dashboard', path)
    except:
        return send_from_directory('.', path)

# API: 모니터링 법령 목록 조회
@app.route('/api/monitored-laws', methods=['GET'])
def get_monitored_laws():
    try:
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 500
        
        response = supabase.table('monitored_laws').select('*').eq('is_active', True).execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API: 법령 추가
@app.route('/api/monitored-laws', methods=['POST'])
def add_monitored_law():
    try:
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 500
        
        data = request.json
        response = supabase.table('monitored_laws').insert(data).execute()
        return jsonify(response.data), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API: 법령 삭제 (소프트 삭제)
@app.route('/api/monitored-laws/<law_id>', methods=['DELETE'])
def delete_monitored_law(law_id):
    try:
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 500
        
        response = supabase.table('monitored_laws').update({'is_active': False}).eq('id', law_id).execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API: 개정 이력 조회
@app.route('/api/amendments', methods=['GET'])
def get_amendments():
    try:
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 500
        
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        query = supabase.table('law_amendments').select('*')
        if unread_only:
            query = query.eq('읽음여부', False)
        
        response = query.order('공포일자', desc=True).execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API: 개정 상세 조회
@app.route('/api/amendments/<amendment_id>', methods=['GET'])
def get_amendment_detail(amendment_id):
    try:
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 500
        
        response = supabase.table('law_amendments').select('*').eq('id', amendment_id).single().execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API: 읽음 처리
@app.route('/api/amendments/<amendment_id>/mark-read', methods=['POST'])
def mark_amendment_read(amendment_id):
    try:
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 500
        
        response = supabase.table('law_amendments').update({'읽음여부': True}).eq('id', amendment_id).execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API: 수동 개정 체크
@app.route('/api/check-amendments', methods=['POST'])
def manual_check_amendments():
    try:
        count = check_law_amendments()
        return jsonify({'message': f'{count}건의 신규 개정사항을 발견했습니다.', 'count': count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API: 통계
@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 500
        
        # 모니터링 법령 수
        laws_response = supabase.table('monitored_laws').select('*', count='exact').eq('is_active', True).execute()
        laws_count = laws_response.count
        
        # 미확인 개정 수
        unread_response = supabase.table('law_amendments').select('*', count='exact').eq('읽음여부', False).execute()
        unread_count = unread_response.count
        
        # 총 개정 이력
        total_response = supabase.table('law_amendments').select('*', count='exact').execute()
        total_count = total_response.count
        
        return jsonify({
            'monitored_laws': laws_count,
            'unread_amendments': unread_count,
            'total_amendments': total_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 법령 개정 자동 체크 함수
def check_law_amendments():
    """법제처 API를 통해 법령 개정사항 확인"""
    try:
        if not supabase or not LAW_API_KEY:
            print("Supabase 또는 API 키가 설정되지 않았습니다.")
            return 0
        
        # 모니터링 대상 법령 목록 조회
        laws_response = supabase.table('monitored_laws').select('*').eq('is_active', True).execute()
        monitored_laws = laws_response.data
        
        if not monitored_laws:
            print("모니터링 대상 법령이 없습니다.")
            return 0
        
        new_amendments_count = 0
        
        # 각 법령에 대해 API 호출
        for law in monitored_laws:
            law_name = law['law_name']
            
            # 법제처 API 호출
            url = "http://open.law.go.kr/LSO/legInfoApi.do"
            params = {
                'OC': LAW_API_KEY,
                '법령명': law_name,
                'type': 'XML'
            }
            
            try:
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    # XML 파싱
                    root = ET.fromstring(response.content)
                    
                    # 개정 정보 추출 (실제 XML 구조에 맞게 수정 필요)
                    for item in root.findall('.//law'):
                        law_id = item.findtext('법령ID', '')
                        promulgate_date = item.findtext('공포일자', '')
                        enforce_date = item.findtext('시행일자', '')
                        revision_type = item.findtext('개정유형', '')
                        
                        # 최근 7일 이내 개정사항만 확인
                        if promulgate_date:
                            try:
                                pub_date = datetime.strptime(promulgate_date, '%Y%m%d')
                                if (datetime.now() - pub_date).days > 7:
                                    continue
                            except:
                                continue
                        
                        # 중복 체크
                        existing = supabase.table('law_amendments').select('*').eq('law_name', law_name).eq('공포일자', promulgate_date).execute()
                        
                        if not existing.data:
                            # 새 개정사항 추가
                            amendment_data = {
                                'law_name': law_name,
                                '공포일자': promulgate_date,
                                '시행일자': enforce_date,
                                '개정유형': revision_type,
                                '내용요약': f'{law_name} {revision_type}',
                                '읽음여부': False,
                                '알림발송여부': False
                            }
                            
                            supabase.table('law_amendments').insert(amendment_data).execute()
                            new_amendments_count += 1
                            print(f"✅ 새 개정사항 발견: {law_name} ({promulgate_date})")
                
            except Exception as e:
                print(f"❌ {law_name} API 호출 실패: {str(e)}")
                continue
        
        print(f"총 {new_amendments_count}건의 신규 개정사항을 발견했습니다.")
        return new_amendments_count
        
    except Exception as e:
        print(f"개정사항 체크 중 오류: {str(e)}")
        return 0

# 스케줄러 설정
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=check_law_amendments,
    trigger='cron',
    hour=9,
    minute=0,
    id='law_amendment_check'
)

# 헬스체크
@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'supabase': 'configured' if supabase else 'not configured',
        'api_key': 'configured' if LAW_API_KEY else 'not configured'
    })

if __name__ == '__main__':
    # 스케줄러 시작
    if not scheduler.running:
        scheduler.start()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
