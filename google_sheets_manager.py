import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import streamlit as st
import json
import os

class GoogleSheetsManager:
    def __init__(self):
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        self.credentials = None
        self.client = None
        self.spreadsheet = None
        
    def authenticate(self, credentials_file):
        """구글 서비스 계정 인증"""
        try:
            self.credentials = Credentials.from_service_account_file(
                credentials_file, scopes=self.scope
            )
            self.client = gspread.authorize(self.credentials)
            return True
        except Exception as e:
            st.error(f"인증 오류: {str(e)}")
            return False
    
    def open_spreadsheet(self, spreadsheet_id):
        """스프레드시트 열기"""
        try:
            self.spreadsheet = self.client.open_by_key(spreadsheet_id)
            return True
        except Exception as e:
            st.error(f"스프레드시트 열기 오류: {str(e)}")
            return False
    
    def get_worksheet(self, worksheet_name):
        """워크시트 가져오기"""
        try:
            return self.spreadsheet.worksheet(worksheet_name)
        except Exception as e:
            st.error(f"워크시트 가져오기 오류: {str(e)}")
            return None
    
    def read_data(self, worksheet_name):
        """데이터 읽기"""
        worksheet = self.get_worksheet(worksheet_name)
        if worksheet:
            try:
                data = worksheet.get_all_records()
                return pd.DataFrame(data)
            except Exception as e:
                st.error(f"데이터 읽기 오류: {str(e)}")
                return pd.DataFrame()
        return pd.DataFrame()
    
    def write_data(self, worksheet_name, data):
        """데이터 쓰기"""
        worksheet = self.get_worksheet(worksheet_name)
        if worksheet:
            try:
                # 기존 데이터 삭제
                worksheet.clear()
                
                # 헤더 추가
                if not data.empty:
                    headers = data.columns.tolist()
                    worksheet.append_row(headers)
                    
                    # 데이터 추가
                    for _, row in data.iterrows():
                        worksheet.append_row(row.tolist())
                
                return True
            except Exception as e:
                st.error(f"데이터 쓰기 오류: {str(e)}")
                return False
        return False
    
    def append_data(self, worksheet_name, data):
        """데이터 추가"""
        worksheet = self.get_worksheet(worksheet_name)
        if worksheet:
            try:
                for _, row in data.iterrows():
                    worksheet.append_row(row.tolist())
                return True
            except Exception as e:
                st.error(f"데이터 추가 오류: {str(e)}")
                return False
        return False
    
    def update_row(self, worksheet_name, row_index, data):
        """행 업데이트"""
        worksheet = self.get_worksheet(worksheet_name)
        if worksheet:
            try:
                worksheet.update(f'A{row_index+2}', data.tolist())
                return True
            except Exception as e:
                st.error(f"행 업데이트 오류: {str(e)}")
                return False
        return False
    
    def delete_row(self, worksheet_name, row_index):
        """행 삭제"""
        worksheet = self.get_worksheet(worksheet_name)
        if worksheet:
            try:
                worksheet.delete_rows(row_index + 2)  # +2 because of 1-based indexing and header
                return True
            except Exception as e:
                st.error(f"행 삭제 오류: {str(e)}")
                return False
        return False

class ProductManager:
    def __init__(self, sheets_manager):
        self.sheets_manager = sheets_manager
        
    def get_products(self):
        """제품 목록 가져오기"""
        return self.sheets_manager.read_data('제품목록')
    
    def add_product(self, product_data):
        """제품 추가"""
        df = pd.DataFrame([product_data])
        return self.sheets_manager.append_data('제품목록', df)
    
    def update_product(self, product_id, product_data):
        """제품 업데이트"""
        products_df = self.get_products()
        if not products_df.empty:
            # 제품 ID로 행 찾기
            row_index = products_df[products_df['제품ID'] == product_id].index
            if len(row_index) > 0:
                df = pd.DataFrame([product_data])
                return self.sheets_manager.update_row('제품목록', row_index[0], df.iloc[0])
        return False
    
    def delete_product(self, product_id):
        """제품 삭제"""
        products_df = self.get_products()
        if not products_df.empty:
            row_index = products_df[products_df['제품ID'] == product_id].index
            if len(row_index) > 0:
                return self.sheets_manager.delete_row('제품목록', row_index[0])
        return False

class MaterialManager:
    def __init__(self, sheets_manager):
        self.sheets_manager = sheets_manager
        
    def get_materials(self):
        """부자재 목록 가져오기"""
        return self.sheets_manager.read_data('부자재목록')
    
    def add_material(self, material_data):
        """부자재 추가"""
        df = pd.DataFrame([material_data])
        return self.sheets_manager.append_data('부자재목록', df)
    
    def update_material(self, material_id, material_data):
        """부자재 업데이트"""
        materials_df = self.get_materials()
        if not materials_df.empty:
            row_index = materials_df[materials_df['부자재ID'] == material_id].index
            if len(row_index) > 0:
                df = pd.DataFrame([material_data])
                return self.sheets_manager.update_row('부자재목록', row_index[0], df.iloc[0])
        return False
    
    def delete_material(self, material_id):
        """부자재 삭제"""
        materials_df = self.get_materials()
        if not materials_df.empty:
            row_index = materials_df[materials_df['부자재ID'] == material_id].index
            if len(row_index) > 0:
                return self.sheets_manager.delete_row('부자재목록', row_index[0])
        return False

class CostCalculationManager:
    def __init__(self, sheets_manager):
        self.sheets_manager = sheets_manager
        
    def get_calculations(self):
        """원가계산 기록 가져오기"""
        return self.sheets_manager.read_data('원가계산기록')
    
    def add_calculation(self, calculation_data):
        """원가계산 기록 추가"""
        df = pd.DataFrame([calculation_data])
        return self.sheets_manager.append_data('원가계산기록', df)
    
    def get_calculation_by_id(self, calculation_id):
        """특정 원가계산 기록 가져오기"""
        calculations_df = self.get_calculations()
        if not calculations_df.empty:
            return calculations_df[calculations_df['계산ID'] == calculation_id]
        return pd.DataFrame() 