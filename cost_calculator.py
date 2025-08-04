import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os

class CostCalculator:
    def __init__(self):
        self.raw_materials = []
        self.packaging_materials = []
        self.labor_costs = {}
        self.manufacturing_overhead = {}
        
    def calculate_raw_material_cost(self, materials_data):
        """원료비 계산"""
        total_cost = 0
        total_weight = 0
        
        for material in materials_data:
            if material['name'] and material['ratio'] > 0 and material['unit_price'] > 0:
                # 배합비율에 따른 투입량 계산
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
        
        # 개당 원가 계산
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
        
        # 도매가 계산 (예상판매가의 약 1.9배)
        wholesale_price = estimated_selling_price * 1.9
        
        # 경영실적 계산
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
        page_title="고래미 원가계산 프로그램",
        page_icon="🐟",
        layout="wide"
    )
    
    st.title("🐟 고래미 원가계산 프로그램")
    st.markdown("---")
    
    # 사이드바 - 기본 설정
    with st.sidebar:
        st.header("📋 기본 설정")
        
        product_name = st.text_input("제품명", value="가니미소400g")
        production_quantity = st.number_input("생산수량 (개)", min_value=1, value=2703)
        base_quantity = st.number_input("기준 투입량 (kg)", min_value=0.1, value=1000.0, step=0.1)
        
        st.markdown("---")
        st.header("💰 이윤 설정")
        profit_margin = st.slider("이윤률 (%)", min_value=0, max_value=100, value=30)
        
        st.markdown("---")
        st.header("📊 경영비용")
        selling_expenses = st.number_input("판관비 (원)", value=1705000)
        non_operating_expenses = st.number_input("영업외비용 (원)", value=137000)
        tax_rate = st.slider("법인세율 (%)", min_value=0, max_value=50, value=22)
    
    # 메인 탭
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📦 원료비", "📦 포장비", "👥 노무비", "🏭 제조경비", 
        "💰 원가계산", "📈 경영실적"
    ])
    
    calculator = CostCalculator()
    
    # 탭 1: 원료비 계산
    with tab1:
        st.header("📦 원료비 계산")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("원료 입력")
            
            # 원료 데이터 입력
            raw_materials_data = []
            
            # 기본 원료들
            default_materials = [
                {"name": "대게내장[붉은대게자숙장]", "ratio": 92.5, "unit_price": 5300},
                {"name": "소스1[미림]", "ratio": 3.0, "unit_price": 2500},
                {"name": "설탕", "ratio": 1.0, "unit_price": 1110},
                {"name": "L-글루탐산나트륨(향미증진제)", "ratio": 0.5, "unit_price": 2300},
                {"name": "혼합제제[떡-플로 케이 : 타피오카전분]", "ratio": 1.5, "unit_price": 2500},
                {"name": "소스2[게 액기스]", "ratio": 1.5, "unit_price": 7000}
            ]
            
            for i, default_material in enumerate(default_materials):
                with st.expander(f"원료 {i+1}: {default_material['name']}", expanded=True):
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        name = st.text_input(f"원료명 {i+1}", value=default_material['name'], key=f"raw_name_{i}")
                    with col_b:
                        ratio = st.number_input(f"배합비율 (%) {i+1}", value=default_material['ratio'], key=f"raw_ratio_{i}")
                    with col_c:
                        unit_price = st.number_input(f"단가 (원/kg) {i+1}", value=default_material['unit_price'], key=f"raw_price_{i}")
                    
                    raw_materials_data.append({
                        'name': name,
                        'ratio': ratio,
                        'unit_price': unit_price,
                        'base_quantity': base_quantity
                    })
            
            # 추가 원료 입력
            additional_count = st.number_input("추가 원료 개수", min_value=0, value=0)
            
            for i in range(additional_count):
                with st.expander(f"추가 원료 {i+1}", expanded=True):
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        name = st.text_input(f"원료명 추가{i+1}", key=f"add_name_{i}")
                    with col_b:
                        ratio = st.number_input(f"배합비율 (%) 추가{i+1}", value=0.0, key=f"add_ratio_{i}")
                    with col_c:
                        unit_price = st.number_input(f"단가 (원/kg) 추가{i+1}", value=0, key=f"add_price_{i}")
                    
                    raw_materials_data.append({
                        'name': name,
                        'ratio': ratio,
                        'unit_price': unit_price,
                        'base_quantity': base_quantity
                    })
        
        with col2:
            st.subheader("원료비 계산 결과")
            
            raw_material_result = calculator.calculate_raw_material_cost(raw_materials_data)
            
            # 결과 표시
            st.metric("총 원료비", f"{raw_material_result['total_cost']:,.0f}원")
            st.metric("총 투입량", f"{raw_material_result['total_weight']:.2f}kg")
            st.metric("평균 단가", f"{raw_material_result['avg_unit_price']:,.0f}원/kg")
            
            # 원료별 상세 내역
            st.subheader("원료별 상세 내역")
            df_raw = pd.DataFrame(raw_material_result['materials'])
            if not df_raw.empty:
                df_raw['투입량(kg)'] = df_raw['input_quantity'].round(2)
                df_raw['계산(원)'] = df_raw['cost'].round(0)
                display_df = df_raw[['name', 'ratio', '투입량(kg)', 'unit_price', '계산(원)']].copy()
                display_df.columns = ['원료명', '배합비율(%)', '투입량(kg)', '단가(원/kg)', '계산(원)']
                st.dataframe(display_df, use_container_width=True)
    
    # 탭 2: 포장비 계산
    with tab2:
        st.header("📦 포장비 계산")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("포장재료 입력")
            
            packaging_data = []
            
            # 기본 포장재료
            default_packaging = [
                {"name": "파우치", "unit_price": 197, "quantity": 2703, "weight_per_unit": 0.40},
                {"name": "종이박스", "unit_price": 410, "quantity": 2703, "weight_per_unit": 4.80}
            ]
            
            for i, default_item in enumerate(default_packaging):
                with st.expander(f"포장재료 {i+1}: {default_item['name']}", expanded=True):
                    col_a, col_b, col_c, col_d = st.columns(4)
                    
                    with col_a:
                        name = st.text_input(f"포장재료명 {i+1}", value=default_item['name'], key=f"pack_name_{i}")
                    with col_b:
                        unit_price = st.number_input(f"단가 (원/개) {i+1}", value=default_item['unit_price'], key=f"pack_price_{i}")
                    with col_c:
                        quantity = st.number_input(f"수량 (개) {i+1}", value=default_item['quantity'], key=f"pack_qty_{i}")
                    with col_d:
                        weight = st.number_input(f"개당 무게 (kg) {i+1}", value=default_item['weight_per_unit'], key=f"pack_weight_{i}")
                    
                    packaging_data.append({
                        'name': name,
                        'unit_price': unit_price,
                        'quantity': quantity,
                        'weight_per_unit': weight
                    })
            
            # 추가 포장재료
            additional_packaging = st.number_input("추가 포장재료 개수", min_value=0, value=0)
            
            for i in range(additional_packaging):
                with st.expander(f"추가 포장재료 {i+1}", expanded=True):
                    col_a, col_b, col_c, col_d = st.columns(4)
                    
                    with col_a:
                        name = st.text_input(f"포장재료명 추가{i+1}", key=f"add_pack_name_{i}")
                    with col_b:
                        unit_price = st.number_input(f"단가 (원/개) 추가{i+1}", value=0, key=f"add_pack_price_{i}")
                    with col_c:
                        quantity = st.number_input(f"수량 (개) 추가{i+1}", value=0, key=f"add_pack_qty_{i}")
                    with col_d:
                        weight = st.number_input(f"개당 무게 (kg) 추가{i+1}", value=0.0, key=f"add_pack_weight_{i}")
                    
                    packaging_data.append({
                        'name': name,
                        'unit_price': unit_price,
                        'quantity': quantity,
                        'weight_per_unit': weight
                    })
        
        with col2:
            st.subheader("포장비 계산 결과")
            
            packaging_result = calculator.calculate_packaging_cost(packaging_data)
            
            st.metric("총 포장비", f"{packaging_result['total_cost']:,.0f}원")
            st.metric("총 포장무게", f"{packaging_result['total_weight']:.2f}kg")
            
            # 포장재료별 상세 내역
            st.subheader("포장재료별 상세 내역")
            df_pack = pd.DataFrame(packaging_result['packaging'])
            if not df_pack.empty:
                df_pack['총비용(원)'] = df_pack['total_cost'].round(0)
                df_pack['총무게(kg)'] = df_pack['total_weight'].round(2)
                display_df = df_pack[['name', 'unit_price', 'quantity', 'weight_per_unit', '총비용(원)', '총무게(kg)']].copy()
                display_df.columns = ['포장재료명', '단가(원/개)', '수량(개)', '개당무게(kg)', '총비용(원)', '총무게(kg)']
                st.dataframe(display_df, use_container_width=True)
    
    # 탭 3: 노무비 계산
    with tab3:
        st.header("👥 노무비 계산")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("노무비 입력")
            
            # 직접인건비
            st.subheader("직접인건비")
            col_a, col_b, col_c, col_d = st.columns(4)
            
            with col_a:
                daily_production_ratio = st.number_input("일일생산량 비율 (%)", value=25.0, key="daily_ratio")
            with col_b:
                hourly_wage = st.number_input("시급 (원/시간)", value=12500, key="hourly_wage")
            with col_c:
                work_hours = st.number_input("근무시간 (시간)", value=8, key="work_hours")
            with col_d:
                worker_count = st.number_input("근로자 수 (명)", value=22, key="worker_count")
            
            direct_labor = (daily_production_ratio / 100) * hourly_wage * work_hours * worker_count
            
            # 간접인건비
            st.subheader("간접인건비")
            col_e, col_f, col_g, col_h = st.columns(4)
            
            with col_e:
                indirect_ratio = st.number_input("간접인건비 비율 (%)", value=25.0, key="indirect_ratio")
            with col_f:
                indirect_hourly_wage = st.number_input("간접 시급 (원/시간)", value=13500, key="indirect_hourly")
            with col_g:
                indirect_hours = st.number_input("간접 근무시간 (시간)", value=8, key="indirect_hours")
            with col_h:
                indirect_workers = st.number_input("간접 근로자 수 (명)", value=6, key="indirect_workers")
            
            indirect_labor = (indirect_ratio / 100) * indirect_hourly_wage * indirect_hours * indirect_workers
            
            # 일용직
            st.subheader("일용직")
            col_i, col_j, col_k, col_l = st.columns(4)
            
            with col_i:
                temp_ratio = st.number_input("일용직 비율 (%)", value=25.0, key="temp_ratio")
            with col_j:
                temp_hourly_wage = st.number_input("일용직 시급 (원/시간)", value=10500, key="temp_hourly")
            with col_k:
                temp_hours = st.number_input("일용직 근무시간 (시간)", value=8, key="temp_hours")
            with col_l:
                temp_workers = st.number_input("일용직 근로자 수 (명)", value=3, key="temp_workers")
            
            temporary_labor = (temp_ratio / 100) * temp_hourly_wage * temp_hours * temp_workers
        
        with col2:
            st.subheader("노무비 계산 결과")
            
            labor_data = {
                'direct_labor': direct_labor,
                'indirect_labor': indirect_labor,
                'temporary_labor': temporary_labor
            }
            
            labor_result = calculator.calculate_labor_cost(labor_data)
            
            st.metric("직접인건비", f"{labor_result['direct_labor']:,.0f}원")
            st.metric("간접인건비", f"{labor_result['indirect_labor']:,.0f}원")
            st.metric("일용직", f"{labor_result['temporary_labor']:,.0f}원")
            st.metric("총 노무비", f"{labor_result['total_labor_cost']:,.0f}원")
            
            # 노무비 차트
            fig = go.Figure(data=[
                go.Pie(labels=['직접인건비', '간접인건비', '일용직'], 
                      values=[labor_result['direct_labor'], labor_result['indirect_labor'], labor_result['temporary_labor']],
                      hole=0.3)
            ])
            fig.update_layout(title="노무비 구성")
            st.plotly_chart(fig, use_container_width=True)
    
    # 탭 4: 제조경비 계산
    with tab4:
        st.header("🏭 제조경비 계산")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("제조경비 입력")
            
            # 기타제조경비
            st.subheader("기타제조경비")
            col_a, col_b = st.columns(2)
            
            with col_a:
                daily_production_ratio_overhead = st.number_input("일일생산량 비율 (%)", value=25.0, key="overhead_ratio")
            with col_b:
                base_overhead = st.number_input("기준 제조경비 (원)", value=1200000, key="base_overhead")
            
            other_expenses = (daily_production_ratio_overhead / 100) * base_overhead
            
            # 복리후생비 (노무비의 15%)
            welfare_ratio = st.slider("복리후생비 비율 (노무비 대비 %)", min_value=0, max_value=50, value=15, key="welfare_ratio")
            welfare_expenses = labor_result['total_labor_cost'] * (welfare_ratio / 100)
            
            # 감가상각비
            st.subheader("감가상각비")
            col_c, col_d, col_e = st.columns(3)
            
            with col_c:
                asset_value = st.number_input("자산가치 (원)", value=1000000000, key="asset_value")
            with col_d:
                useful_life = st.number_input("사용연한 (년)", value=10, key="useful_life")
            with col_e:
                production_days = st.number_input("생산일수 (일)", value=22, key="production_days")
            
            monthly_depreciation = asset_value / (useful_life * 12)
            daily_depreciation = monthly_depreciation / 30
            depreciation = daily_depreciation * production_days
        
        with col2:
            st.subheader("제조경비 계산 결과")
            
            overhead_data = {
                'other_expenses': other_expenses,
                'welfare_expenses': welfare_expenses,
                'depreciation': depreciation
            }
            
            overhead_result = calculator.calculate_manufacturing_overhead(overhead_data)
            
            st.metric("기타제조경비", f"{overhead_result['other_expenses']:,.0f}원")
            st.metric("복리후생비", f"{overhead_result['welfare_expenses']:,.0f}원")
            st.metric("감가상각비", f"{overhead_result['depreciation']:,.0f}원")
            st.metric("총 제조경비", f"{overhead_result['total_overhead']:,.0f}원")
            
            # 제조경비 차트
            fig = go.Figure(data=[
                go.Pie(labels=['기타제조경비', '복리후생비', '감가상각비'], 
                      values=[overhead_result['other_expenses'], overhead_result['welfare_expenses'], overhead_result['depreciation']],
                      hole=0.3)
            ])
            fig.update_layout(title="제조경비 구성")
            st.plotly_chart(fig, use_container_width=True)
    
    # 탭 5: 원가계산
    with tab5:
        st.header("💰 원가계산")
        
        # 전체 원가 계산
        total_cost_result = calculator.calculate_total_cost(
            raw_material_result, packaging_result, labor_result, overhead_result, production_quantity
        )
        
        # 이윤 및 가격 계산
        pricing_result = calculator.calculate_profit_and_pricing(
            total_cost_result, profit_margin, selling_expenses, non_operating_expenses, tax_rate
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("원가 구성")
            
            # 원가 구성 차트
            cost_data = {
                '원료비': raw_material_result['total_cost'],
                '포장비': packaging_result['total_cost'],
                '노무비': labor_result['total_labor_cost'],
                '제조경비': overhead_result['total_overhead']
            }
            
            fig = px.pie(values=list(cost_data.values()), names=list(cost_data.keys()), 
                        title="원가 구성")
            st.plotly_chart(fig, use_container_width=True)
            
            # 개당 원가
            st.subheader("개당 원가")
            st.metric("재료원가", f"{total_cost_result['unit_material_cost']:,.0f}원")
            st.metric("노무비", f"{total_cost_result['unit_labor_cost']:,.0f}원")
            st.metric("제조경비", f"{total_cost_result['unit_overhead_cost']:,.0f}원")
            st.metric("제조원가", f"{total_cost_result['unit_manufacturing_cost']:,.0f}원")
        
        with col2:
            st.subheader("가격 설정")
            
            st.metric("제조원가", f"{total_cost_result['total_manufacturing_cost']:,.0f}원")
            st.metric("이윤", f"{pricing_result['profit_amount']:,.0f}원")
            st.metric("예상판매가", f"{pricing_result['estimated_selling_price']:,.0f}원")
            st.metric("도매가격", f"{pricing_result['wholesale_price']:,.0f}원")
            
            # 가격 구성 차트
            price_data = {
                '제조원가': total_cost_result['total_manufacturing_cost'],
                '이윤': pricing_result['profit_amount']
            }
            
            fig = px.pie(values=list(price_data.values()), names=list(price_data.keys()), 
                        title="가격 구성")
            st.plotly_chart(fig, use_container_width=True)
        
        # 상세 원가 내역
        st.subheader("상세 원가 내역")
        
        cost_summary = pd.DataFrame({
            '구분': ['원료비', '포장비', '소계', '노무비', '제조경비', '소계', '제조원가', '이윤', '예상판매가'],
            '금액(원)': [
                raw_material_result['total_cost'],
                packaging_result['total_cost'],
                raw_material_result['total_cost'] + packaging_result['total_cost'],
                labor_result['total_labor_cost'],
                overhead_result['total_overhead'],
                labor_result['total_labor_cost'] + overhead_result['total_overhead'],
                total_cost_result['total_manufacturing_cost'],
                pricing_result['profit_amount'],
                pricing_result['estimated_selling_price']
            ],
            '개당(원)': [
                raw_material_result['total_cost'] / production_quantity if production_quantity > 0 else 0,
                packaging_result['total_cost'] / production_quantity if production_quantity > 0 else 0,
                (raw_material_result['total_cost'] + packaging_result['total_cost']) / production_quantity if production_quantity > 0 else 0,
                labor_result['total_labor_cost'] / production_quantity if production_quantity > 0 else 0,
                overhead_result['total_overhead'] / production_quantity if production_quantity > 0 else 0,
                (labor_result['total_labor_cost'] + overhead_result['total_overhead']) / production_quantity if production_quantity > 0 else 0,
                total_cost_result['unit_manufacturing_cost'],
                pricing_result['profit_amount'] / production_quantity if production_quantity > 0 else 0,
                pricing_result['estimated_selling_price'] / production_quantity if production_quantity > 0 else 0
            ]
        })
        
        cost_summary['금액(원)'] = cost_summary['금액(원)'].round(0)
        cost_summary['개당(원)'] = cost_summary['개당(원)'].round(0)
        
        st.dataframe(cost_summary, use_container_width=True)
    
    # 탭 6: 경영실적
    with tab6:
        st.header("📈 경영실적 분석")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("수익성 분석")
            
            # 매출 및 이익 분석
            revenue = pricing_result['wholesale_price']
            cost_of_goods_sold = total_cost_result['total_manufacturing_cost']
            gross_profit = pricing_result['gross_profit']
            net_profit = pricing_result['net_profit']
            
            st.metric("매출액", f"{revenue:,.0f}원")
            st.metric("매출원가", f"{cost_of_goods_sold:,.0f}원")
            st.metric("매출총이익", f"{gross_profit:,.0f}원")
            st.metric("판관비", f"{pricing_result['selling_expenses']:,.0f}원")
            st.metric("영업외비용", f"{pricing_result['non_operating_expenses']:,.0f}원")
            st.metric("법인세", f"{pricing_result['corporate_tax']:,.0f}원")
            st.metric("당기순이익", f"{net_profit:,.0f}원")
            
            # 수익성 지표
            gross_margin = (gross_profit / revenue * 100) if revenue > 0 else 0
            net_margin = (net_profit / revenue * 100) if revenue > 0 else 0
            
            st.metric("매출총이익률", f"{gross_margin:.1f}%")
            st.metric("순이익률", f"{net_margin:.1f}%")
        
        with col2:
            st.subheader("수익성 차트")
            
            # 수익성 구성 차트
            profit_data = {
                '매출원가': cost_of_goods_sold,
                '매출총이익': gross_profit
            }
            
            fig = px.pie(values=list(profit_data.values()), names=list(profit_data.keys()), 
                        title="매출 구성")
            st.plotly_chart(fig, use_container_width=True)
            
            # 이익 구성 차트
            income_data = {
                '매출총이익': gross_profit,
                '판관비': -pricing_result['selling_expenses'],
                '영업외비용': -pricing_result['non_operating_expenses'],
                '법인세': -pricing_result['corporate_tax'],
                '당기순이익': net_profit
            }
            
            fig = go.Figure(data=[
                go.Bar(x=list(income_data.keys()), y=list(income_data.values()))
            ])
            fig.update_layout(title="이익 구성", xaxis_title="구분", yaxis_title="금액(원)")
            st.plotly_chart(fig, use_container_width=True)
        
        # 경영실적 요약
        st.subheader("경영실적 요약")
        
        performance_summary = pd.DataFrame({
            '구분': ['매출액', '매출원가', '매출총이익', '판관비', '영업외비용', '법인세', '당기순이익'],
            '금액(원)': [
                revenue,
                cost_of_goods_sold,
                gross_profit,
                pricing_result['selling_expenses'],
                pricing_result['non_operating_expenses'],
                pricing_result['corporate_tax'],
                net_profit
            ],
            '비율(%)': [
                100,
                (cost_of_goods_sold / revenue * 100) if revenue > 0 else 0,
                gross_margin,
                (pricing_result['selling_expenses'] / revenue * 100) if revenue > 0 else 0,
                (pricing_result['non_operating_expenses'] / revenue * 100) if revenue > 0 else 0,
                (pricing_result['corporate_tax'] / revenue * 100) if revenue > 0 else 0,
                net_margin
            ]
        })
        
        performance_summary['금액(원)'] = performance_summary['금액(원)'].round(0)
        performance_summary['비율(%)'] = performance_summary['비율(%)'].round(1)
        
        st.dataframe(performance_summary, use_container_width=True)
        
        # 결과 저장 버튼
        if st.button("💾 결과 저장"):
            # 결과를 JSON 파일로 저장
            result_data = {
                'product_name': product_name,
                'production_quantity': production_quantity,
                'calculation_date': datetime.now().isoformat(),
                'raw_material_cost': raw_material_result,
                'packaging_cost': packaging_result,
                'labor_cost': labor_result,
                'manufacturing_overhead': overhead_result,
                'total_cost': total_cost_result,
                'pricing': pricing_result
            }
            
            filename = f"cost_calculation_{product_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            
            st.success(f"결과가 {filename} 파일로 저장되었습니다!")

if __name__ == "__main__":
    main() 