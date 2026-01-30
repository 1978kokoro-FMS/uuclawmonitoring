# law_api.py
import requests
from datetime import datetime
from config import LAW_API_BASE_URL, LAW_API_OC

class LawAPI:
    def __init__(self):
        self.base_url = LAW_API_BASE_URL
        self.oc = LAW_API_OC
    
    def search_law(self, law_name):
        """법령 검색"""
        url = f"{self.base_url}/lawSearch.do"
        params = {
            "OC": self.oc,
            "target": "law",
            "type": "XML",
            "query": law_name
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return self._parse_search_result(response.text)
        except Exception as e:
            print(f"법령 검색 오류: {e}")
            return None
    
    def get_law_info(self, law_id):
        """법령 상세 정보 조회"""
        url = f"{self.base_url}/lawService.do"
        params = {
            "OC": self.oc,
            "target": "law",
            "type": "XML",
            "ID": law_id
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return self._parse_law_info(response.text)
        except Exception as e:
            print(f"법령 정보 조회 오류: {e}")
            return None
    
    def get_amendment_history(self, law_id):
        """법령 개정 연혁 조회"""
        url = f"{self.base_url}/lawRevisionService.do"
        params = {
            "OC": self.oc,
            "target": "law",
            "type": "XML",
            "ID": law_id
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return self._parse_amendment_history(response.text)
        except Exception as e:
            print(f"개정 연혁 조회 오류: {e}")
            return None
    
    def _parse_search_result(self, xml_text):
        """검색 결과 파싱"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(xml_text, 'html.parser')
        laws = []
        
        for law in soup.find_all('law'):
            law_id_tag = law.find('법령id') or law.find('법령ID')
            law_name_tag = law.find('법령명한글')
            law_type_tag = law.find('법령구분명')
            enf_date_tag = law.find('시행일자')
            amend_date_tag = law.find('공포일자')
            
            laws.append({
                'law_id': law_id_tag.text.strip() if law_id_tag else None,
                'law_name': law_name_tag.text.strip() if law_name_tag else None,
                'law_type': law_type_tag.text.strip() if law_type_tag else None,
                'enf_date': enf_date_tag.text.strip() if enf_date_tag else None,
                'amend_date': amend_date_tag.text.strip() if amend_date_tag else None
            })
        
        return laws
    
    def _parse_law_info(self, xml_text):
        """법령 정보 파싱"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(xml_text, 'html.parser')
        law = soup.find('법령')
        
        if not law:
            return None
        
        law_id_tag = law.find('법령id') or law.find('법령ID')
        law_name_tag = law.find('법령명한글')
        law_type_tag = law.find('법령구분명')
        amend_date_tag = law.find('공포일자')
        enf_date_tag = law.find('시행일자')
        amend_no_tag = law.find('공포번호')
        content_tag = law.find('조문내용')
        
        return {
            'law_id': law_id_tag.text.strip() if law_id_tag else None,
            'law_name': law_name_tag.text.strip() if law_name_tag else None,
            'law_type': law_type_tag.text.strip() if law_type_tag else None,
            'amend_date': amend_date_tag.text.strip() if amend_date_tag else None,
            'enf_date': enf_date_tag.text.strip() if enf_date_tag else None,
            'amend_no': amend_no_tag.text.strip() if amend_no_tag else None,
            'content': content_tag.text.strip() if content_tag else None
        }
    
    def _parse_amendment_history(self, xml_text):
        """개정 연혁 파싱"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(xml_text, 'html.parser')
        amendments = []
        
        for rev in soup.find_all('개정문'):
            amend_date_tag = rev.find('공포일자')
            enf_date_tag = rev.find('시행일자')
            amend_no_tag = rev.find('공포번호')
            amend_type_tag = rev.find('개정구분명')
            content_tag = rev.find('조문내용')
            
            amendments.append({
                'amend_date': amend_date_tag.text.strip() if amend_date_tag else None,
                'enf_date': enf_date_tag.text.strip() if enf_date_tag else None,
                'amend_no': amend_no_tag.text.strip() if amend_no_tag else None,
                'amend_type': amend_type_tag.text.strip() if amend_type_tag else None,
                'content': content_tag.text.strip() if content_tag else None
            })
        
        return amendments