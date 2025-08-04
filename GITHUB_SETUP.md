# GitHub 설정 및 업로드 가이드

## 1. GitHub 저장소 생성
1. [GitHub.com](https://github.com)에 로그인
2. 우측 상단 "+" 버튼 → "New repository"
3. 저장소 이름: `goremi-cost-calculator`
4. Description: "고래미 수산가공식품 원가계산 시스템"
5. Public 또는 Private 선택
6. "Create repository" 클릭

## 2. 로컬 저장소를 GitHub에 연결
GitHub에서 저장소를 생성한 후, 다음 명령어를 실행하세요:

```bash
# 원격 저장소 추가 (YOUR_USERNAME을 실제 GitHub 사용자명으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/goremi-cost-calculator.git

# 메인 브랜치를 main으로 설정
git branch -M main

# GitHub에 푸시
git push -u origin main
```

## 3. 실시간 편집 방법

### 코드 편집
- **GitHub 웹 편집기**: GitHub에서 직접 파일을 편집할 수 있습니다
- **VS Code**: GitHub 저장소를 클론하여 로컬에서 편집
- **협업**: 여러 사람이 동시에 작업하고 Pull Request로 변경사항 병합

### 애플리케이션 업데이트
- **Streamlit Cloud**: GitHub 저장소를 연결하여 자동 배포
- **로컬 개발**: 코드 변경 시 `streamlit run cost_calculator_with_sheets.py`로 즉시 확인

## 4. 보안 주의사항
- Google Service Account 키 파일(*.json)은 .gitignore에 포함되어 업로드되지 않습니다
- 실제 운영 시에는 환경변수나 GitHub Secrets를 사용하세요

## 5. 협업 워크플로우
1. 새로운 기능 개발 시 브랜치 생성: `git checkout -b feature/new-feature`
2. 변경사항 커밋: `git commit -m "새 기능 추가"`
3. GitHub에 푸시: `git push origin feature/new-feature`
4. Pull Request 생성하여 코드 리뷰 후 병합

## 6. 자동 배포 설정 (선택사항)
GitHub Actions를 사용하여 코드 변경 시 자동으로 Streamlit 앱을 배포할 수 있습니다. 