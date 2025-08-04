import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os
from google_sheets_manager import GoogleSheetsManager, ProductManager, MaterialManager, CostCalculationManager

class CostCalculatorWithSheets:
    def __init__(self):
        self.sheets_manager = GoogleSheetsManager()
        self.product_manager = None
        self.material_manager = None
        self.calculation_manager = None
        
    def initialize_managers(self):
        """매니저 초기화"""
        if self.sheets_manager.client:
            self.product_manager = ProductManager(self.sheets_manager)
            self.material_manager = MaterialManager(self.sheets_manager)
            self.calculation_manager = CostCalculationManager(self.sheets_manager)
    
    def calculate_raw_material_cost(self, materials_data):
        """원료비 계산"""
        total_cost = 0
        total_weight = 0
        
        for material in materials_data:
            if material['name'] and material['ratio'] > 0 and material['unit_price'] > 0:
                input_quantity = material['ratio'] / 100 * material['base_quantity']
                cost = input_quantity * material['unit_price']
                
                material['input_quantity'] = input_quantity
                material['cost'] = cost
                
                total_cost += cost
                total_weight += input_quantity
            else:
                material['input_quantity'] = 0
                material['cost'] = 0
        
        return {
            'materials': materials_data,
            'total_cost': total_cost,
            'total_weight': total_weight,
            'avg_unit_price': total_cost / total_weight if total_weight > 0 else 0
        }
    
    def calculate_packaging_cost(self, packaging_data):
        """포장비 계산"""
        total_cost = 0
        total_weight = 0
        
        for item in packaging_data:
            if item['name'] and item['unit_price'] > 0 and item['quantity'] > 0:
                cost = item['unit_price'] * item['quantity']
                weight = item['weight_per_unit'] * item['quantity']
                
                item['total_cost'] = cost
                item['total_weight'] = weight
                
                total_cost += cost
                total_weight += weight
            else:
                item['total_cost'] = 0
                item['total_weight'] = 0
        
        return {
            'packaging': packaging_data,
            'total_cost': total_cost,
            'total_weight': total_weight
        }
    
    def calculate_labor_cost(self, labor_data):
        """노무비 계산"""
        direct_labor = labor_data['direct_labor']
        indirect_labor = labor_data['indirect_labor']
        temporary_labor = labor_data['temporary_labor']
        
        total_labor_cost = direct_labor + indirect_labor + temporary_labor
        
        return {
            'direct_labor': direct_labor,
            'indirect_labor': indirect_labor,
            'temporary_labor': temporary_labor,
            'total_labor_cost': total_labor_cost
        }
    
    def calculate_manufacturing_overhead(self, overhead_data):
        """제조경비 계산"""
        other_expenses = overhead_data['other_expenses']
        welfare_expenses = overhead_data['welfare_expenses']
        depreciation = overhead_data['depreciation']
        
        total_overhead = other_expenses + welfare_expenses + depreciation
        
        return {
            'other_expenses': other_expenses,
            'welfare_expenses': welfare_expenses,
            'depreciation': depreciation,
            'total_overhead': total_overhead
        }
    
    def calculate_total_cost(self, raw_material_cost, packaging_cost, labor_cost, overhead_cost, production_quantity):
        """총 제조원가 계산"""
        material_cost = raw_material_cost['total_cost'] + packaging_cost['total_cost']
        total_manufacturing_cost = material_cost + labor_cost['total_labor_cost'] + overhead_cost['total_overhead']
        
        unit_material_cost = material_cost / production_quantity if production_quantity > 0 else 0
        unit_labor_cost = labor_cost['total_labor_cost'] / production_quantity if production_quantity > 0 else 0
        unit_overhead_cost = overhead_cost['total_overhead'] / production_quantity if production_quantity > 0 else 0
        unit_manufacturing_cost = total_manufacturing_cost / production_quantity if production_quantity > 0 else 0
        
        return {
            'material_cost': material_cost,
            'labor_cost': labor_cost['total_labor_cost'],
            'overhead_cost': overhead_cost['total_overhead'],
            'total_manufacturing_cost': total_manufacturing_cost,
            'unit_material_cost': unit_material_cost,
            'unit_labor_cost': unit_labor_cost,
            'unit_overhead_cost': unit_overhead_cost,
            'unit_manufacturing_cost': unit_manufacturing_cost
        }
    
    def calculate_profit_and_pricing(self, total_cost, profit_margin, selling_expenses, non_operating_expenses, tax_rate):
        """이윤 및 가격 계산"""
        profit_amount = total_cost['total_manufacturing_cost'] * (profit_margin / 100)
        estimated_selling_price = total_cost['total_manufacturing_cost'] + profit_amount
        
        wholesale_price = estimated_selling_price * 1.9
        
        gross_profit = wholesale_price - total_cost['total_manufacturing_cost']
        net_profit_before_tax = gross_profit - selling_expenses - non_operating_expenses
        corporate_tax = net_profit_before_tax * (tax_rate / 100)
        net_profit = net_profit_before_tax - corporate_tax
        
        return {
            'profit_amount': profit_amount,
            'estimated_selling_price': estimated_selling_price,
            'wholesale_price': wholesale_price,
            'gross_profit': gross_profit,
            'selling_expenses': selling_expenses,
            'non_operating_expenses': non_operating_expenses,
            'net_profit_before_tax': net_profit_before_tax,
            'corporate_tax': corporate_tax,
            'net_profit': net_profit
        }

def main():
    st.set_page_config(
        page_title="고래미 원가계산 시스템 (구글시트 연동)",
        page_icon="🐟",
        layout="wide"
    )
    
    st.title("🐟 고래미 원가계산 시스템 (구글시트 연동)")
    st.markdown("---")
    
    # 구글 시트 인증
    with st.sidebar:
        st.header("🔐 구글 시트 설정")
        
        # 인증 파일 업로드
        credentials_file = st.file_uploader(
            "구글 서비스 계정 키 파일 업로드", 
            type=['json'],
            help="구글 클라우드 콘솔에서 다운로드한 서비스 계정 키 파일을 업로드하세요."
        )
        
        if credentials_file:
            # 임시 파일로 저장
            with open("temp_credentials.json", "w") as f:
                f.write(credentials_file.getvalue())
            
            # 인증
            calculator = CostCalculatorWithSheets()
            if calculator.sheets_manager.authenticate("temp_credentials.json"):
                st.success("✅ 구글 시트 인증 성공!")
                
                # 스프레드시트 ID 입력
                spreadsheet_id = st.text_input(
                    "스프레드시트 ID",
                    help="구글 시트 URL에서 추출한 ID를 입력하세요. 예: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
                )
                
                if spreadsheet_id:
                    if calculator.sheets_manager.open_spreadsheet(spreadsheet_id):
                        st.success("✅ 스프레드시트 연결 성공!")
                        calculator.initialize_managers()
                        
                        # 메인 탭
                        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                            "📦 원료비", "📦 포장비", "👥 노무비", "🏭 제조경비", 
                            "💰 원가계산", "📈 경영실적", "🗄️ 데이터 관리"
                        ])
                        
                        # 기본 설정
                        st.sidebar.markdown("---")
                        st.sidebar.header("📋 기본 설정")
                        
                        product_name = st.sidebar.text_input("제품명", value="가니미소400g")
                        production_quantity = st.sidebar.number_input("생산수량 (개)", min_value=1, value=2703)
                        base_quantity = st.sidebar.number_input("기준 투입량 (kg)", min_value=0.1, value=1000.0, step=0.1)
                        
                        st.sidebar.markdown("---")
                        st.sidebar.header("💰 이윤 설정")
                        profit_margin = st.sidebar.slider("이윤률 (%)", min_value=0, max_value=100, value=30)
                        
                        st.sidebar.markdown("---")
                        st.sidebar.header("📊 경영비용")
                        selling_expenses = st.sidebar.number_input("판관비 (원)", value=1705000)
                        non_operating_expenses = st.sidebar.number_input("영업외비용 (원)", value=137000)
                        tax_rate = st.sidebar.slider("법인세율 (%)", min_value=0, max_value=50, value=22)
                        
                        # 탭 1: 원료비 계산
                        with tab1:
                            st.header("📦 원료비 계산")
                            
                            # 부자재 목록에서 원료 선택
                            if calculator.material_manager:
                                materials_df = calculator.material_manager.get_materials()
                                
                                if not materials_df.empty:
                                    st.subheader("부자재 목록에서 원료 선택")
                                    
                                    # 원료 카테고리 필터링
                                    raw_materials = materials_df[materials_df['카테고리'] == '원료']
                                    
                                    if not raw_materials.empty:
                                        selected_materials = st.multiselect(
                                            "원료 선택",
                                            options=raw_materials['부자재명'].tolist(),
                                            default=raw_materials['부자재명'].tolist()[:6]
                                        )
                                        
                                        raw_materials_data = []
                                        
                                        for material_name in selected_materials:
                                            material_info = raw_materials[raw_materials['부자재명'] == material_name].iloc[0]
                                            
                                            with st.expander(f"원료: {material_name}", expanded=True):
                                                col_a, col_b, col_c = st.columns(3)
                                                
                                                with col_a:
                                                    name = st.text_input(f"원료명", value=material_name, key=f"raw_name_{material_name}")
                                                with col_b:
                                                    ratio = st.number_input(f"배합비율 (%)", value=float(material_info.get('기본배합비율', 1.0)), key=f"raw_ratio_{material_name}")
                                                with col_c:
                                                    unit_price = st.number_input(f"단가 (원/kg)", value=float(material_info.get('단가', 0)), key=f"raw_price_{material_name}")
                                                
                                                raw_materials_data.append({
                                                    'name': name,
                                                    'ratio': ratio,
                                                    'unit_price': unit_price,
                                                    'base_quantity': base_quantity
                                                })
                                        
                                        # 계산 결과 표시
                                        if raw_materials_data:
                                            raw_material_result = calculator.calculate_raw_material_cost(raw_materials_data)
                                            
                                            col1, col2 = st.columns(2)
                                            
                                            with col1:
                                                st.metric("총 원료비", f"{raw_material_result['total_cost']:,.0f}원")
                                                st.metric("총 투입량", f"{raw_material_result['total_weight']:.2f}kg")
                                                st.metric("평균 단가", f"{raw_material_result['avg_unit_price']:,.0f}원/kg")
                                            
                                            with col2:
                                                # 원료별 상세 내역
                                                df_raw = pd.DataFrame(raw_material_result['materials'])
                                                if not df_raw.empty:
                                                    df_raw['투입량(kg)'] = df_raw['input_quantity'].round(2)
                                                    df_raw['계산(원)'] = df_raw['cost'].round(0)
                                                    display_df = df_raw[['name', 'ratio', '투입량(kg)', 'unit_price', '계산(원)']].copy()
                                                    display_df.columns = ['원료명', '배합비율(%)', '투입량(kg)', '단가(원/kg)', '계산(원)']
                                                    st.dataframe(display_df, use_container_width=True)
                                    else:
                                        st.warning("부자재 목록에 원료 카테고리가 없습니다.")
                                else:
                                    st.warning("부자재 목록을 불러올 수 없습니다.")
                        
                        # 탭 2: 포장비 계산
                        with tab2:
                            st.header("📦 포장비 계산")
                            
                            if calculator.material_manager:
                                materials_df = calculator.material_manager.get_materials()
                                
                                if not materials_df.empty:
                                    st.subheader("부자재 목록에서 포장재료 선택")
                                    
                                    # 포장재료 카테고리 필터링
                                    packaging_materials = materials_df[materials_df['카테고리'] == '포장재료']
                                    
                                    if not packaging_materials.empty:
                                        selected_packaging = st.multiselect(
                                            "포장재료 선택",
                                            options=packaging_materials['부자재명'].tolist(),
                                            default=packaging_materials['부자재명'].tolist()[:2]
                                        )
                                        
                                        packaging_data = []
                                        
                                        for material_name in selected_packaging:
                                            material_info = packaging_materials[packaging_materials['부자재명'] == material_name].iloc[0]
                                            
                                            with st.expander(f"포장재료: {material_name}", expanded=True):
                                                col_a, col_b, col_c, col_d = st.columns(4)
                                                
                                                with col_a:
                                                    name = st.text_input(f"포장재료명", value=material_name, key=f"pack_name_{material_name}")
                                                with col_b:
                                                    unit_price = st.number_input(f"단가 (원/개)", value=float(material_info.get('단가', 0)), key=f"pack_price_{material_name}")
                                                with col_c:
                                                    quantity = st.number_input(f"수량 (개)", value=production_quantity, key=f"pack_qty_{material_name}")
                                                with col_d:
                                                    weight = st.number_input(f"개당 무게 (kg)", value=float(material_info.get('개당무게', 0.1)), key=f"pack_weight_{material_name}")
                                                
                                                packaging_data.append({
                                                    'name': name,
                                                    'unit_price': unit_price,
                                                    'quantity': quantity,
                                                    'weight_per_unit': weight
                                                })
                                        
                                        # 계산 결과 표시
                                        if packaging_data:
                                            packaging_result = calculator.calculate_packaging_cost(packaging_data)
                                            
                                            col1, col2 = st.columns(2)
                                            
                                            with col1:
                                                st.metric("총 포장비", f"{packaging_result['total_cost']:,.0f}원")
                                                st.metric("총 포장무게", f"{packaging_result['total_weight']:.2f}kg")
                                            
                                            with col2:
                                                # 포장재료별 상세 내역
                                                df_pack = pd.DataFrame(packaging_result['packaging'])
                                                if not df_pack.empty:
                                                    df_pack['총비용(원)'] = df_pack['total_cost'].round(0)
                                                    df_pack['총무게(kg)'] = df_pack['total_weight'].round(2)
                                                    display_df = df_pack[['name', 'unit_price', 'quantity', 'weight_per_unit', '총비용(원)', '총무게(kg)']].copy()
                                                    display_df.columns = ['포장재료명', '단가(원/개)', '수량(개)', '개당무게(kg)', '총비용(원)', '총무게(kg)']
                                                    st.dataframe(display_df, use_container_width=True)
                                    else:
                                        st.warning("부자재 목록에 포장재료 카테고리가 없습니다.")
                        
                        # 탭 3-6: 기존 계산 로직 (간단히 표시)
                        with tab3:
                            st.header("👥 노무비 계산")
                            st.info("노무비 계산 기능은 기존과 동일합니다.")
                        
                        with tab4:
                            st.header("🏭 제조경비 계산")
                            st.info("제조경비 계산 기능은 기존과 동일합니다.")
                        
                        with tab5:
                            st.header("💰 원가계산")
                            st.info("원가계산 기능은 기존과 동일합니다.")
                        
                        with tab6:
                            st.header("📈 경영실적")
                            st.info("경영실적 분석 기능은 기존과 동일합니다.")
                        
                        # 탭 7: 데이터 관리
                        with tab7:
                            st.header("🗄️ 데이터 관리")
                            
                            sub_tab1, sub_tab2, sub_tab3 = st.tabs(["제품 관리", "부자재 관리", "계산 기록"])
                            
                            with sub_tab1:
                                st.subheader("제품 관리")
                                
                                if calculator.product_manager:
                                    products_df = calculator.product_manager.get_products()
                                    
                                    if not products_df.empty:
                                        st.dataframe(products_df, use_container_width=True)
                                    else:
                                        st.info("등록된 제품이 없습니다.")
                                    
                                    # 새 제품 추가
                                    with st.expander("새 제품 추가", expanded=False):
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            new_product_id = st.text_input("제품 ID")
                                            new_product_name = st.text_input("제품명")
                                            new_product_category = st.selectbox("카테고리", ["수산가공품", "조미료", "기타"])
                                        
                                        with col2:
                                            new_product_weight = st.number_input("제품 무게 (g)", min_value=0.1)
                                            new_product_unit = st.text_input("단위", value="개")
                                            new_product_description = st.text_area("설명")
                                        
                                        if st.button("제품 추가"):
                                            if new_product_id and new_product_name:
                                                product_data = {
                                                    '제품ID': new_product_id,
                                                    '제품명': new_product_name,
                                                    '카테고리': new_product_category,
                                                    '제품무게': new_product_weight,
                                                    '단위': new_product_unit,
                                                    '설명': new_product_description,
                                                    '등록일': datetime.now().strftime('%Y-%m-%d')
                                                }
                                                
                                                if calculator.product_manager.add_product(product_data):
                                                    st.success("제품이 추가되었습니다!")
                                                    st.rerun()
                                                else:
                                                    st.error("제품 추가에 실패했습니다.")
                                            else:
                                                st.warning("제품 ID와 제품명을 입력해주세요.")
                            
                            with sub_tab2:
                                st.subheader("부자재 관리")
                                
                                if calculator.material_manager:
                                    materials_df = calculator.material_manager.get_materials()
                                    
                                    if not materials_df.empty:
                                        st.dataframe(materials_df, use_container_width=True)
                                    else:
                                        st.info("등록된 부자재가 없습니다.")
                                    
                                    # 새 부자재 추가
                                    with st.expander("새 부자재 추가", expanded=False):
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            new_material_id = st.text_input("부자재 ID")
                                            new_material_name = st.text_input("부자재명")
                                            new_material_category = st.selectbox("카테고리", ["원료", "포장재료", "조미료", "기타"])
                                            new_material_unit = st.text_input("단위", value="kg")
                                        
                                        with col2:
                                            new_material_price = st.number_input("단가 (원)", min_value=0)
                                            new_material_weight = st.number_input("개당 무게 (kg)", min_value=0.0, value=1.0)
                                            new_material_supplier = st.text_input("공급업체")
                                            new_material_description = st.text_area("설명")
                                        
                                        if st.button("부자재 추가"):
                                            if new_material_id and new_material_name:
                                                material_data = {
                                                    '부자재ID': new_material_id,
                                                    '부자재명': new_material_name,
                                                    '카테고리': new_material_category,
                                                    '단위': new_material_unit,
                                                    '단가': new_material_price,
                                                    '개당무게': new_material_weight,
                                                    '공급업체': new_material_supplier,
                                                    '설명': new_material_description,
                                                    '등록일': datetime.now().strftime('%Y-%m-%d')
                                                }
                                                
                                                if calculator.material_manager.add_material(material_data):
                                                    st.success("부자재가 추가되었습니다!")
                                                    st.rerun()
                                                else:
                                                    st.error("부자재 추가에 실패했습니다.")
                                            else:
                                                st.warning("부자재 ID와 부자재명을 입력해주세요.")
                            
                            with sub_tab3:
                                st.subheader("계산 기록")
                                
                                if calculator.calculation_manager:
                                    calculations_df = calculator.calculation_manager.get_calculations()
                                    
                                    if not calculations_df.empty:
                                        st.dataframe(calculations_df, use_container_width=True)
                                    else:
                                        st.info("계산 기록이 없습니다.")
                    else:
                        st.error("스프레드시트 연결에 실패했습니다.")
                else:
                    st.warning("스프레드시트 ID를 입력해주세요.")
            else:
                st.error("구글 시트 인증에 실패했습니다.")
        else:
            st.info("구글 서비스 계정 키 파일을 업로드해주세요.")
            
            st.markdown("### 🔧 구글 시트 설정 방법")
            st.markdown("""
            1. **구글 클라우드 콘솔에서 프로젝트 생성**
            2. **Google Sheets API 활성화**
            3. **서비스 계정 생성 및 키 다운로드**
            4. **구글 시트에 서비스 계정 이메일 공유**
            5. **다운로드한 JSON 키 파일 업로드**
            """)

if __name__ == "__main__":
    main() 