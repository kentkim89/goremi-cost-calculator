import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

def create_google_sheets_template(credentials_file, spreadsheet_name="고래미 원가계산 시스템"):
    """구글 시트 템플릿 생성"""
    
    # 인증
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    
    credentials = Credentials.from_service_account_file(credentials_file, scopes=scope)
    client = gspread.authorize(credentials)
    
    # 새 스프레드시트 생성
    spreadsheet = client.create(spreadsheet_name)
    
    # 워크시트 생성 및 데이터 설정
    worksheets = {
        '제품목록': [
            ['제품ID', '제품명', '카테고리', '제품무게', '단위', '설명', '등록일'],
            ['P001', '가니미소400g', '수산가공품', 400, '개', '대게내장을 이용한 조미료', '2024-01-01'],
            ['P002', '게장소스200g', '조미료', 200, '개', '게장용 소스', '2024-01-01'],
            ['P003', '해산물조미료300g', '조미료', 300, '개', '해산물 조미료', '2024-01-01']
        ],
        
        '부자재목록': [
            ['부자재ID', '부자재명', '카테고리', '단위', '단가', '개당무게', '기본배합비율', '공급업체', '설명', '등록일'],
            ['M001', '대게내장[붉은대게자숙장]', '원료', 'kg', 5300, 1.0, 92.5, '수산업체A', '대게 내장 원료', '2024-01-01'],
            ['M002', '소스1[미림]', '원료', 'kg', 2500, 1.0, 3.0, '조미료업체B', '미림 소스', '2024-01-01'],
            ['M003', '설탕', '원료', 'kg', 1110, 1.0, 1.0, '설탕업체C', '백설탕', '2024-01-01'],
            ['M004', 'L-글루탐산나트륨(향미증진제)', '원료', 'kg', 2300, 1.0, 0.5, '화학업체D', '향미증진제', '2024-01-01'],
            ['M005', '혼합제제[떡-플로 케이 : 타피오카전분]', '원료', 'kg', 2500, 1.0, 1.5, '전분업체E', '타피오카 전분', '2024-01-01'],
            ['M006', '소스2[게 액기스]', '원료', 'kg', 7000, 1.0, 1.5, '액기스업체F', '게 액기스', '2024-01-01'],
            ['M007', '파우치', '포장재료', '개', 197, 0.4, 0, '포장업체G', '제품 포장용 파우치', '2024-01-01'],
            ['M008', '종이박스', '포장재료', '개', 410, 4.8, 0, '포장업체H', '제품 포장용 종이박스', '2024-01-01'],
            ['M009', '라벨', '포장재료', '개', 50, 0.01, 0, '인쇄업체I', '제품 라벨', '2024-01-01'],
            ['M010', '소금', '조미료', 'kg', 800, 1.0, 0.5, '염업체J', '정제염', '2024-01-01'],
            ['M011', '후추', '조미료', 'kg', 15000, 1.0, 0.1, '향신료업체K', '후추 가루', '2024-01-01'],
            ['M012', '마늘', '조미료', 'kg', 3000, 1.0, 0.3, '농산물업체L', '다진 마늘', '2024-01-01']
        ],
        
        '원가계산기록': [
            ['계산ID', '제품ID', '제품명', '생산수량', '기준투입량', '총원료비', '총포장비', '총노무비', '총제조경비', '총제조원가', '이윤률', '예상판매가', '도매가격', '계산일시'],
            ['CALC001', 'P001', '가니미소400g', 2703, 1000, 5559568, 643518, 775000, 510947, 7489033, 30, 9735743, 18497911, '2024-01-01 10:00:00']
        ],
        
        '원료비상세': [
            ['계산ID', '원료ID', '원료명', '배합비율', '투입량', '단가', '계산금액'],
            ['CALC001', 'M001', '대게내장[붉은대게자숙장]', 92.5, 925, 5300, 4902500],
            ['CALC001', 'M002', '소스1[미림]', 3.0, 30, 2500, 75000],
            ['CALC001', 'M003', '설탕', 1.0, 10, 1110, 11100],
            ['CALC001', 'M004', 'L-글루탐산나트륨(향미증진제)', 0.5, 5, 2300, 11500],
            ['CALC001', 'M005', '혼합제제[떡-플로 케이 : 타피오카전분]', 1.5, 15, 2500, 37500],
            ['CALC001', 'M006', '소스2[게 액기스]', 1.5, 15, 7000, 105000']
        ],
        
        '포장비상세': [
            ['계산ID', '포장재료ID', '포장재료명', '단가', '수량', '개당무게', '총비용', '총무게'],
            ['CALC001', 'M007', '파우치', 197, 2703, 0.4, 532432, 1081.2],
            ['CALC001', 'M008', '종이박스', 410, 2703, 4.8, 1108230, 12974.4]
        ],
        
        '노무비상세': [
            ['계산ID', '구분', '시급', '근무시간', '근로자수', '일일생산량비율', '계산금액'],
            ['CALC001', '직접인건비', 12500, 8, 22, 25, 550000],
            ['CALC001', '간접인건비', 13500, 8, 6, 25, 162000],
            ['CALC001', '일용직', 10500, 8, 3, 25, 63000']
        ],
        
        '제조경비상세': [
            ['계산ID', '구분', '기준금액', '비율', '계산금액'],
            ['CALC001', '기타제조경비', 1200000, 25, 300000],
            ['CALC001', '복리후생비', 775000, 15, 116250],
            ['CALC001', '감가상각비', 1000000000, 0.0003, 94697]
        ],
        
        '경영실적': [
            ['계산ID', '매출액', '매출원가', '매출총이익', '판관비', '영업외비용', '법인세', '당기순이익', '매출총이익률', '순이익률'],
            ['CALC001', 18497911, 7489033, 11008878, 1705000, 137000, 2401246, 6763632, 59.5, 36.6]
        ]
    }
    
    # 각 워크시트에 데이터 입력
    for worksheet_name, data in worksheets.items():
        try:
            # 기존 워크시트 삭제 (있는 경우)
            try:
                worksheet = spreadsheet.worksheet(worksheet_name)
                spreadsheet.del_worksheet(worksheet)
            except:
                pass
            
            # 새 워크시트 생성
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=100, cols=20)
            
            # 데이터 입력
            worksheet.update('A1', data)
            
            print(f"✅ {worksheet_name} 워크시트 생성 완료")
            
        except Exception as e:
            print(f"❌ {worksheet_name} 워크시트 생성 실패: {str(e)}")
    
    # 스프레드시트 공유 설정 (서비스 계정 이메일로)
    service_account_email = credentials.service_account_email
    spreadsheet.share(service_account_email, perm_type='writer', role='writer')
    
    print(f"\n🎉 구글 시트 템플릿 생성 완료!")
    print(f"📊 스프레드시트 URL: {spreadsheet.url}")
    print(f"🆔 스프레드시트 ID: {spreadsheet.id}")
    print(f"📧 서비스 계정 이메일: {service_account_email}")
    
    return spreadsheet.id

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("사용법: python create_google_sheets_template.py <credentials_file>")
        print("예시: python create_google_sheets_template.py service-account-key.json")
        sys.exit(1)
    
    credentials_file = sys.argv[1]
    
    try:
        spreadsheet_id = create_google_sheets_template(credentials_file)
        print(f"\n✅ 템플릿 생성 성공! 스프레드시트 ID: {spreadsheet_id}")
    except Exception as e:
        print(f"❌ 템플릿 생성 실패: {str(e)}")
        sys.exit(1) 