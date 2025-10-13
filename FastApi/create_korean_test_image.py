#!/usr/bin/env python3
"""
한글 OCR 정확도 테스트용 이미지 생성
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_korean_test_image():
    """복잡한 한글 텍스트가 포함된 테스트 이미지 생성"""
    width, height = 600, 800
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # 폰트 설정 시도 (시스템 폰트 사용)
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    y_pos = 30

    # 제목
    draw.text((width//2 - 100, y_pos), "한글 OCR 정확도 테스트", fill='black', font=font_large)
    y_pos += 50

    # 회사 정보
    draw.text((50, y_pos), "주식회사 테스트컴퍼니", fill='black', font=font_medium)
    y_pos += 30

    draw.text((50, y_pos), "대표이사: 김철수", fill='black', font=font_small)
    y_pos += 25

    draw.text((50, y_pos), "주소: 서울특별시 강남구 테헤란로 123", fill='black', font=font_small)
    y_pos += 25

    draw.text((50, y_pos), "전화번호: 02-1234-5678", fill='black', font=font_small)
    y_pos += 40

    # 구분선
    draw.line([(30, y_pos), (width-30, y_pos)], fill='black', width=2)
    y_pos += 30

    # 복잡한 한글 텍스트들
    korean_texts = [
        "영수증 번호: 2025-KR-001234",
        "거래일시: 2025년 10월 10일 15:30",
        "결제방법: 신용카드 (삼성카드)",
        "",
        "상품명                    수량    단가      금액",
        "==========================================",
        "한국전통차 세트             2개    15,000   30,000원",
        "프리미엄 녹차               1개    25,000   25,000원",
        "유기농 꿀                   1개    12,000   12,000원",
        "전통 다과 세트               1개    18,000   18,000원",
        "",
        "==========================================",
        "소계                                     85,000원",
        "부가세 (10%)                              8,500원",
        "총 결제금액                              93,500원",
        "",
        "==========================================",
        "",
        "※ 주의사항:",
        "• 교환/환불은 영수증 지참 시 가능합니다",
        "• 식품류는 개봉 후 교환/환불 불가",
        "• 문의사항: customer@testcompany.co.kr",
        "",
        "감사합니다! 좋은 하루 되세요 :)",
        "",
        "QR코드로 적립하세요: [QR]",
        "포인트 적립률: 구매금액의 2%"
    ]

    # 텍스트 그리기
    for text in korean_texts:
        if text == "":
            y_pos += 15
            continue
        elif "=" in text:
            draw.text((50, y_pos), text, fill='black', font=font_small)
            y_pos += 20
        elif "※" in text or "•" in text:
            draw.text((50, y_pos), text, fill='gray', font=font_small)
            y_pos += 20
        elif "상품명" in text:
            draw.text((50, y_pos), text, fill='black', font=font_medium)
            y_pos += 25
        elif "총 결제금액" in text:
            draw.text((50, y_pos), text, fill='red', font=font_medium)
            y_pos += 25
        else:
            draw.text((50, y_pos), text, fill='black', font=font_small)
            y_pos += 22

    return img

def create_difficult_korean_text():
    """인식하기 어려운 한글 텍스트 이미지 생성"""
    width, height = 500, 400
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    try:
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    y_pos = 30

    # 어려운 한글 텍스트들 (OCR이 자주 틀리는)
    difficult_texts = [
        "어려운 한글 텍스트 인식 테스트",
        "",
        "• 의료진의 진료기록부",
        "• 환자명: 이영희 (李英姬)",
        "• 진료과: 내과 (內科)",
        "• 의사소견: 경미한 위염 증상",
        "",
        "처방전:",
        "➤ 위장약 1일 3회 복용",
        "➤ 진정제 취침 전 1회",
        "➤ 소화제 식후 30분",
        "",
        "※ 특이사항:",
        "- 알레르기 반응 없음",
        "- 혈압: 120/80 mmHg",
        "- 체온: 36.5°C",
        "- 맥박: 72회/분",
        "",
        "다음 진료 예약:",
        "2025년 10월 17일 (목) 오후 2시",
        "",
        "담당의사: 박민수 MD",
        "의료법인 우리병원"
    ]

    for text in difficult_texts:
        if text == "":
            y_pos += 10
            continue
        elif "•" in text or "➤" in text or "-" in text:
            draw.text((30, y_pos), text, fill='darkblue', font=font_small)
            y_pos += 18
        elif "※" in text or "담당의사" in text:
            draw.text((30, y_pos), text, fill='red', font=font_small)
            y_pos += 18
        elif "어려운" in text:
            draw.text((width//2 - 100, y_pos), text, fill='black', font=font_medium)
            y_pos += 30
        else:
            draw.text((30, y_pos), text, fill='black', font=font_small)
            y_pos += 18

    return img

if __name__ == "__main__":
    # demo 디렉토리 생성
    os.makedirs("demo/korean_test", exist_ok=True)

    # 한글 테스트 이미지 생성
    korean_receipt = create_korean_test_image()
    korean_receipt.save("demo/korean_test/korean_receipt_complex.png")
    print("✅ 복잡한 한글 영수증 이미지 생성: demo/korean_test/korean_receipt_complex.png")

    difficult_text = create_difficult_korean_text()
    difficult_text.save("demo/korean_test/korean_medical_record.png")
    print("✅ 어려운 한글 의료기록 이미지 생성: demo/korean_test/korean_medical_record.png")

    print("\n한글 OCR 정확도 테스트를 위한 이미지가 생성되었습니다!")
    print("다음 명령어로 테스트하세요:")
    print("curl -X POST -F 'file=@demo/korean_test/korean_receipt_complex.png' http://localhost:6003/process-request")
    print("curl -X POST -F 'file=@demo/korean_test/korean_medical_record.png' http://localhost:6003/process-request")