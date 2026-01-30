# ai_analyzer.py
from anthropic import Anthropic
from config import CLAUDE_API_KEY

class AIAnalyzer:
    def __init__(self):
        if not CLAUDE_API_KEY:
            print("경고: Claude API Key가 설정되지 않았습니다.")
            self.client = None
        else:
            self.client = Anthropic(api_key=CLAUDE_API_KEY)
    
    def analyze_amendment(self, law_name, amendment_content, law_type="산업안전보건"):
        """법령 개정 내용 분석"""
        if not self.client:
            return {
                'summary': '(AI 분석 비활성화) 개정 내용을 확인하세요.',
                'impact_analysis': '',
                'tasks': []
            }
        
        prompt = f"""
당신은 {law_type} 전문가입니다. 의왕도시공사 안전감사팀을 위해 법령 개정 내용을 분석해주세요.

**법령명**: {law_name}

**개정 내용**:
{amendment_content}

다음 형식으로 분석해주세요:

1. **주요 변경사항 요약** (3-5줄로 핵심만)
2. **공사 업무에 미치는 영향** (구체적으로)
3. **필요한 후속 조치** (우선순위별로)
   - 매뉴얼/절차서 수정 필요 사항
   - 직원 교육 필요 사항
   - ISO 문서 개정 필요 사항
   - 시설물 점검 항목 변경 사항

간결하고 실무적으로 작성해주세요.
"""
        
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            
            # 응답 파싱
            return self._parse_analysis(response_text)
            
        except Exception as e:
            print(f"AI 분석 오류: {e}")
            return {
                'summary': f'분석 오류: {str(e)}',
                'impact_analysis': '',
                'tasks': []
            }
    
    def _parse_analysis(self, response_text):
        """AI 응답 파싱"""
        lines = response_text.split('\n')
        
        summary = []
        impact = []
        tasks = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if '주요 변경사항' in line or '요약' in line:
                current_section = 'summary'
            elif '영향' in line:
                current_section = 'impact'
            elif '후속 조치' in line or '조치' in line:
                current_section = 'tasks'
            else:
                if current_section == 'summary':
                    summary.append(line)
                elif current_section == 'impact':
                    impact.append(line)
                elif current_section == 'tasks':
                    if line.startswith('-') or line.startswith('•'):
                        tasks.append({
                            'title': line.lstrip('-•').strip(),
                            'type': self._detect_task_type(line)
                        })
        
        return {
            'summary': '\n'.join(summary),
            'impact_analysis': '\n'.join(impact),
            'tasks': tasks
        }
    
    def _detect_task_type(self, task_text):
        """업무 유형 자동 감지"""
        if '매뉴얼' in task_text or '절차서' in task_text:
            return 'manual'
        elif '교육' in task_text or '훈련' in task_text:
            return 'training'
        elif 'ISO' in task_text or '문서' in task_text:
            return 'document'
        elif '점검' in task_text or '확인' in task_text:
            return 'inspection'
        else:
            return 'other'
