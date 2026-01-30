from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime, timedelta
from supabase import create_client, Client
import requests
import xml.etree.ElementTree as ET
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
CORS(app)

# 환경 변수
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')
LAW_API_KEY = os.environ.get('LAW_API_KEY', '')

# Supabase 클라이언트
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase 연결 성공")
    except Exception as e:
        print(f"❌ Supabase 연결 실패: {e}")

# 메인 페이지
@app.route('/')
def index():
    try:
        return send_from_directory('dashboard', 'index.html')
    except:
        return send_from_directory('.', 'index.html')

# 정적 파일 서빙
@app.route('/dashboard/<path:path>')
def send_dashboard(path):
    return send_from_directory('dashboard', path)

@app.route('/<path:path>')
def send_static(path):
    try:
        return send_from_directory('dashboard', path)
    except:
        try:
            return send_from_directory('.', path)
        except:
            return jsonify({'error': 'File not found'}), 404

# 헬스체크
@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'supabase': 'configured' if supabase else 'not configured',
        'api_key': 'configured' if LAW_API_KEY else 'not configured'
    })

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
        
        response = query.order('공포일자', desc=True).limit(50).execute()
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

# API: 수동 개정 체크 (GET과 POST 모두 지원)
@app.route('/api/check-amendments', methods=['GET', 'POST'])
def manual_check_amendments():
    try:
        count = check_law_amendments()
        return jsonify({
            'success': True,
            'message': f'{count}건의 신규 개정사항을 발견했습니다.',
            'count': count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# API: 통계
@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 500
        
        # 모니터링 법령 수
        laws_response = supabase.table('monitored_laws').select('*', count='exact').eq('is_active', True).execute()
        laws_count = laws_response.count if laws_response.count else 0
        
        # 미확인 개정 수
        unread_response = supabase.table('law_amendments').select('*', count='exact').eq('읽음여부', False).execute()
        unread_count = unread_response.count if unread_response.count else 0
        
        # 총 개정 이력
        total_response = supabase.table('law_amendments').select('*', count='exact').execute()
        total_count = total_response.count if total_response.count else 0
        
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
        if not supabase:
            print("❌ Supabase가 설정되지 않았습니다.")
            return 0
            
        if not LAW_API_KEY:
            print("❌ LAW_API_KEY가 설정되지 않았습니다.")
            return 0
        
        print("🔍 법령 개정사항 체크 시작...")
        
        # 모니터링 대상 법령 목록 조회
        laws_response = supabase.table('monitored_laws').select('*').eq('is_active', True).execute()
        monitored_laws = laws_response.data
        
        if not monitored_laws:
            print("⚠️ 모니터링 대상 법령이 없습니다.")
            return 0
        
        print(f"📋 모니터링 대상 법령: {len(monitored_laws)}개")
        
        new_amendments_count = 0
        
        # 각 법령에 대해 API 호출
        for law in monitored_laws:
            law_name = law['law_name']
            print(f"  🔎 {law_name} 확인 중...")
            
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
                    # XML 파싱 (실제 응답 구조에 맞게 조정 필요)
                    try:
                        root = ET.fromstring(response.content)
                        
                        # 예시: 실제 XML 구조에 맞게 수정 필요
                        for item in root.findall('.//law'):
                            promulgate_date = item.findtext('공포일자', '')
                            enforce_date = item.findtext('시행일자', '')
                            revision_type = item.findtext('개정유형', '')
                            
                            if promulgate_date:
                                # 최근 30일 이내 개정사항만
                                try:
                                    pub_date = datetime.strptime(promulgate_date, '%Y%m%d')
                                    if (datetime.now() - pub_date).days > 30:
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
                                        '시행일자': enforce_date if enforce_date else None,
                                        '개정유형': revision_type if revision_type else '일부개정',
                                        '내용요약': f'{law_name} {revision_type if revision_type else "개정"}',
                                        '읽음여부': False,
                                        '알림발송여부': False
                                    }
                                    
                                    supabase.table('law_amendments').insert(amendment_data).execute()
                                    new_amendments_count += 1
                                    print(f"    ✅ 새 개정사항 발견: {promulgate_date}")
                    except ET.ParseError as e:
                        print(f"    ⚠️ XML 파싱 오류: {e}")
                else:
                    print(f"    ⚠️ API 응답 오류: {response.status_code}")
                
            except Exception as e:
                print(f"    ❌ API 호출 실패: {str(e)}")
                continue
        
        print(f"✅ 체크 완료: 총 {new_amendments_count}건의 신규 개정사항 발견")
        return new_amendments_count
        
    except Exception as e:
        print(f"❌ 개정사항 체크 중 오류: {str(e)}")
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

if __name__ == '__main__':
    # 스케줄러 시작
    try:
        if not scheduler.running:
            scheduler.start()
            print("✅ 스케줄러 시작됨 (매일 오전 9시)")
    except Exception as e:
        print(f"⚠️ 스케줄러 시작 실패: {e}")
    
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Flask 서버 시작: 포트 {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
