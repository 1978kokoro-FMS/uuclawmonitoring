// app.js - 법령 개정 모니터링 시스템

// Supabase 설정
const SUPABASE_URL = 'https://qiwqcylerloqxdqupgbk.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFpd3FjeWxlcmxvcXhkcXVwZ2JrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk0MTQxMzMsImV4cCI6MjA3NDk5MDEzM30.haR8oLJsgp_5r-EisNqxI8ASHrdh87hiAixfMt5TG6U';

// Supabase 클라이언트
let supabaseClient = null;

// 페이지 로드 시 실행
window.addEventListener('DOMContentLoaded', async function() {
    console.log('페이지 로드 시작');
    
    // Supabase 클라이언트 초기화
    try {
        if (typeof window.supabase === 'undefined') {
            throw new Error('Supabase 라이브러리가 로드되지 않았습니다.');
        }
        
        const { createClient } = window.supabase;
        supabaseClient = createClient(SUPABASE_URL, SUPABASE_KEY);
        console.log('Supabase 초기화 성공');
        
    } catch (error) {
        console.error('Supabase 초기화 오류:', error);
        alert('데이터베이스 연결에 실패했습니다. 페이지를 새로고침해주세요.');
        return;
    }
    
    // 탭 전환 이벤트
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(function(tab) {
        tab.addEventListener('click', function() {
            switchTab(tab.dataset.tab);
        });
    });
    
    // 초기 데이터 로드
    loadAmendments();
});

// 탭 전환
function switchTab(tabName) {
    console.log('탭 전환:', tabName);
    
    // 모든 탭 비활성화
    document.querySelectorAll('.tab').forEach(function(tab) {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(function(content) {
        content.classList.remove('active');
    });
    
    // 선택된 탭 활성화
    const selectedTab = document.querySelector('[data-tab="' + tabName + '"]');
    const selectedContent = document.getElementById(tabName + '-tab');
    
    if (selectedTab) selectedTab.classList.add('active');
    if (selectedContent) selectedContent.classList.add('active');
    
    // 데이터 로드
    if (tabName === 'amendments') {
        loadAmendments();
    } else if (tabName === 'laws') {
        loadLaws();
    } else if (tabName === 'tasks') {
        loadTasks();
    } else if (tabName === 'logs') {
        loadLogs();
    }
}

// 개정 현황 로드
async function loadAmendments() {
    console.log('개정 현황 로드 시작');
    const container = document.getElementById('amendments-list');
    
    if (!container) {
        console.error('amendments-list 요소를 찾을 수 없습니다.');
        return;
    }
    
    container.innerHTML = '<p class="loading">로딩 중...</p>';
    
    if (!supabaseClient) {
        container.innerHTML = '<p class="loading" style="color: red;">데이터베이스 연결 오류</p>';
        return;
    }
    
    try {
        const reviewFilter = document.getElementById('review-filter').value;
        
        let query = supabaseClient
            .from('law_amendments')
            .select('*')
            .order('amendment_date', { ascending: false });
        
        if (reviewFilter !== 'all') {
            query = query.eq('is_reviewed', reviewFilter === 'true');
        }
        
        const { data, error } = await query;
        
        if (error) {
            console.error('Supabase 오류:', error);
            throw error;
        }
        
        console.log('데이터 로드 성공:', data);
        
        if (!data || data.length === 0) {
            container.innerHTML = '<p class="loading">개정 이력이 없습니다.</p>';
            return;
        }
        
        let html = '';
        data.forEach(function(amendment) {
            const badge = amendment.is_reviewed ? 'badge-reviewed' : 'badge-new';
            const badgeText = amendment.is_reviewed ? '검토완료' : '미검토';
            
            html += '<div class="card">';
            html += '<div class="card-header">';
            html += '<div class="card-title">' + (amendment.law_code || '') + '</div>';
            html += '<div class="card-badge ' + badge + '">' + badgeText + '</div>';
            html += '</div>';
            html += '<div class="card-info">';
            html += '<span>📅 개정일: ' + formatDate(amendment.amendment_date) + '</span>';
            html += '<span>🚀 시행일: ' + formatDate(amendment.enforcement_date) + '</span>';
            html += '<span>📄 ' + (amendment.amendment_type || '-') + '</span>';
            html += '</div>';
            
            if (amendment.summary) {
                const shortSummary = amendment.summary.substring(0, 150);
                html += '<div style="margin-top: 15px; padding: 15px; background: #f8f9fa; border-radius: 5px;">';
                html += '<strong>요약:</strong><br>' + shortSummary + '...';
                html += '</div>';
            }
            
            html += '<div class="card-actions">';
            html += '<button class="btn-small btn-view" onclick="viewAmendmentDetail(' + amendment.id + ')">상세보기</button>';
            
            if (!amendment.is_reviewed) {
                html += '<button class="btn-small btn-complete" onclick="markAsReviewed(' + amendment.id + ')">검토완료</button>';
            }
            
            html += '</div>';
            html += '</div>';
        });
        
        container.innerHTML = html;
        
    } catch (error) {
        console.error('오류:', error);
        container.innerHTML = '<p class="loading" style="color: red;">오류: ' + error.message + '</p>';
    }
}

// 법령 관리 로드
async function loadLaws() {
    console.log('법령 관리 로드');
    const container = document.getElementById('laws-list');
    container.innerHTML = '<p class="loading">로딩 중...</p>';
    
    try {
        const { data, error } = await supabaseClient
            .from('law_master')
            .select('*')
            .order('created_at', { ascending: false });
        
        if (error) throw error;
        
        if (!data || data.length === 0) {
            container.innerHTML = '<p class="loading">등록된 법령이 없습니다.</p>';
            return;
        }
        
        let html = '';
        data.forEach(function(law) {
            const badge = law.is_active ? 'badge-active' : 'badge-inactive';
            const badgeText = law.is_active ? '모니터링중' : '비활성';
            
            html += '<div class="card">';
            html += '<div class="card-header">';
            html += '<div class="card-title">' + law.law_name + '</div>';
            html += '<div class="card-badge ' + badge + '">' + badgeText + '</div>';
            html += '</div>';
            html += '<div class="card-info">';
            html += '<span>📋 ' + (law.law_type || '-') + '</span>';
            html += '<span>👤 담당: ' + (law.manager || '-') + '</span>';
            html += '<span>🏢 ' + (law.department || '-') + '</span>';
            html += '</div>';
            
            if (law.last_check_date) {
                html += '<div style="margin-top: 10px; color: #6c757d; font-size: 0.9em;">';
                html += '마지막 확인: ' + formatDateTime(law.last_check_date);
                html += '</div>';
            }
            
            html += '<div class="card-actions">';
            html += '<button class="btn-small btn-toggle" onclick="toggleLawActive(' + law.id + ', ' + !law.is_active + ')">';
            html += law.is_active ? '비활성화' : '활성화';
            html += '</button>';
            html += '</div>';
            html += '</div>';
        });
        
        container.innerHTML = html;
        
    } catch (error) {
        console.error('오류:', error);
        container.innerHTML = '<p class="loading" style="color: red;">오류: ' + error.message + '</p>';
    }
}

// 후속 업무 로드
async function loadTasks() {
    console.log('후속 업무 로드');
    const container = document.getElementById('tasks-list');
    container.innerHTML = '<p class="loading">로딩 중...</p>';
    
    try {
        const statusFilter = document.getElementById('status-filter').value;
        
        let query = supabaseClient
            .from('follow_up_tasks')
            .select('*')
            .order('created_at', { ascending: false });
        
        if (statusFilter !== 'all') {
            query = query.eq('status', statusFilter);
        }
        
        const { data, error } = await query;
        
        if (error) throw error;
        
        if (!data || data.length === 0) {
            container.innerHTML = '<p class="loading">후속 업무가 없습니다.</p>';
            return;
        }
        
        let html = '';
        data.forEach(function(task) {
            html += '<div class="card">';
            html += '<div class="card-header">';
            html += '<div class="card-title">' + task.task_title + '</div>';
            html += '<div class="card-badge badge-' + task.status + '">' + getStatusText(task.status) + '</div>';
            html += '</div>';
            html += '<div class="card-info">';
            html += '<span>📂 ' + task.task_type + '</span>';
            html += '<span>👤 ' + task.assignee + '</span>';
            html += '<span>📅 기한: ' + formatDate(task.due_date) + '</span>';
            html += '<span>⚡ ' + getPriorityText(task.priority) + '</span>';
            html += '</div>';
            
            if (task.task_description) {
                html += '<div style="margin-top: 10px; color: #495057;">' + task.task_description + '</div>';
            }
            
            html += '<div class="card-actions">';
            
            if (task.status === 'pending') {
                html += '<button class="btn-small btn-edit" onclick="updateTaskStatus(' + task.id + ', \'in_progress\')">진행중으로</button>';
                html += '<button class="btn-small btn-complete" onclick="updateTaskStatus(' + task.id + ', \'completed\')">완료</button>';
            } else if (task.status === 'in_progress') {
                html += '<button class="btn-small btn-complete" onclick="updateTaskStatus(' + task.id + ', \'completed\')">완료</button>';
            }
            
            html += '</div>';
            html += '</div>';
        });
        
        container.innerHTML = html;
        
    } catch (error) {
        console.error('오류:', error);
        container.innerHTML = '<p class="loading" style="color: red;">오류: ' + error.message + '</p>';
    }
}

// 모니터링 로그 로드
async function loadLogs() {
    console.log('모니터링 로그 로드');
    const container = document.getElementById('logs-list');
    container.innerHTML = '<p class="loading">로딩 중...</p>';
    
    try {
        const { data, error } = await supabaseClient
            .from('monitoring_logs')
            .select('*')
            .order('check_date', { ascending: false })
            .limit(50);
        
        if (error) throw error;
        
        if (!data || data.length === 0) {
            container.innerHTML = '<p class="loading">로그가 없습니다.</p>';
            return;
        }
        
        let html = '';
        data.forEach(function(log) {
            const badge = log.status === 'success' ? 'badge-reviewed' : 'badge-new';
            const badgeText = log.status === 'success' ? '성공' : '오류';
            
            html += '<div class="card">';
            html += '<div class="card-header">';
            html += '<div class="card-title">' + (log.law_code === 'ALL' ? '전체 모니터링' : log.law_code) + '</div>';
            html += '<div class="card-badge ' + badge + '">' + badgeText + '</div>';
            html += '</div>';
            html += '<div class="card-info">';
            html += '<span>🕐 ' + formatDateTime(log.check_date) + '</span>';
            html += '<span>' + (log.changes_detected ? '✅ 변경사항 발견' : '⏺️ 변경사항 없음') + '</span>';
            
            if (log.execution_time) {
                html += '<span>⏱️ ' + log.execution_time + '초</span>';
            }
            
            html += '</div>';
            
            if (log.error_message) {
                html += '<div style="margin-top: 10px; padding: 10px; background: #fff3cd; border-radius: 5px; color: #856404;">';
                html += '오류: ' + log.error_message;
                html += '</div>';
            }
            
            html += '</div>';
        });
        
        container.innerHTML = html;
        
    } catch (error) {
        console.error('오류:', error);
        container.innerHTML = '<p class="loading" style="color: red;">오류: ' + error.message + '</p>';
    }
}

// 유틸리티 함수들
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('ko-KR');
}

function formatDateTime(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('ko-KR');
}

function getStatusText(status) {
    const map = {
        'pending': '대기중',
        'in_progress': '진행중',
        'completed': '완료'
    };
    return map[status] || status;
}

function getPriorityText(priority) {
    const map = {
        'high': '높음',
        'medium': '보통',
        'low': '낮음'
    };
    return map[priority] || priority;
}

// 검토 완료 표시
async function markAsReviewed(id) {
    if (!confirm('검토 완료로 표시하시겠습니까?')) return;
    
    try {
        const { error } = await supabaseClient
            .from('law_amendments')
            .update({ 
                is_reviewed: true,
                reviewer: '지영',
                review_date: new Date().toISOString()
            })
            .eq('id', id);
        
        if (error) throw error;
        
        alert('검토 완료로 표시되었습니다.');
        loadAmendments();
        
    } catch (error) {
        alert('오류: ' + error.message);
    }
}

// 법령 활성화/비활성화
async function toggleLawActive(id, isActive) {
    try {
        const { error } = await supabaseClient
            .from('law_master')
            .update({ is_active: isActive })
            .eq('id', id);
        
        if (error) throw error;
        
        alert(isActive ? '모니터링이 활성화되었습니다.' : '모니터링이 비활성화되었습니다.');
        loadLaws();
        
    } catch (error) {
        alert('오류: ' + error.message);
    }
}

// 업무 상태 업데이트
async function updateTaskStatus(id, status) {
    try {
        const updateData = { status: status };
        
        if (status === 'completed') {
            updateData.completed_date = new Date().toISOString();
        }
        
        const { error } = await supabaseClient
            .from('follow_up_tasks')
            .update(updateData)
            .eq('id', id);
        
        if (error) throw error;
        
        alert('업무 상태가 변경되었습니다.');
        loadTasks();
        
    } catch (error) {
        alert('오류: ' + error.message);
    }
}

// 모달 관련 함수들
function showAddLawModal() {
    document.getElementById('add-law-modal').classList.add('show');
}

function closeAddLawModal() {
    document.getElementById('add-law-modal').classList.remove('show');
    document.getElementById('add-law-form').reset();
}

async function addLaw(event) {
    event.preventDefault();
    
    const lawName = document.getElementById('law-name').value;
    const lawType = document.getElementById('law-type').value;
    const department = document.getElementById('department').value;
    const manager = document.getElementById('manager').value;
    
    try {
        const { error } = await supabaseClient
            .from('law_master')
            .insert({
                law_code: lawName,
                law_name: lawName,
                law_type: lawType,
                department: department,
                manager: manager,
                is_active: true
            });
        
        if (error) throw error;
        
        alert('법령이 추가되었습니다.');
        closeAddLawModal();
        loadLaws();
        
    } catch (error) {
        alert('오류: ' + error.message);
    }
}

function viewAmendmentDetail(id) {
    alert('상세보기 기능은 개발 중입니다.');
}

function closeAmendmentDetail() {
    document.getElementById('amendment-detail-modal').classList.remove('show');
}
