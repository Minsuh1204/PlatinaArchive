# 🎼 PLATiNA :: ARCHIVE 클라이언트

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub release](https://img.shields.io/github/v/release/YOUR_USERNAME/YOUR_REPO?include_prereleases)](https://github.com/YOUR_USERNAME/YOUR_REPO/releases)

PLATiNA :: ARCHIVE 클라이언트는 리듬 게임 **PLATiNA :: LAB**의 플레이 스크린샷을 분석하여 점수 기록을 자동 추출하고 관리하는 **비공식 팬메이드** 데스크톱 애플리케이션입니다.

---

## ✨ 주요 기능

* **클립보드 분석:** $\text{Alt} + \text{PrtSc}$ (스크린샷) 후 앱 내 단축키를 통해 클립보드의 이미지를 즉시 로드하고 분석합니다.
* **고속 곡 매칭:** 이미지 해싱 알고리즘 (**pHash**)을 사용하여 앨범 커버 이미지와 데이터베이스를 비교, 플레이한 곡을 즉시 식별합니다.
* **정밀 데이터 추출:** **Tesseract OCR** 및 색상 분석을 통해 다음 데이터를 정확하게 추출합니다.
    * 판정율 (Judge Rate) 및 최종 랭크
    * 스코어 및 노트 판정별 카운트 (PH/P/G/D/M)
    * 라인 수, 난이도, 레벨
    * P.A.T.C.H. 값 (계산 및 OCR)

---

## ⚠️ 라이선스 및 고지 사항
본 애플리케이션은 하이엔드게임즈의 PLATiNA :: LAB 게임을 기반으로 제작된 비공식 팬메이드 툴이며, 어떠한 상업적 이익도 추구하지 않습니다.
* Tesseract OCR: 본 앱은 Apache License 2.0 하에 배포되는 Tesseract OCR 엔진을 사용합니다.
