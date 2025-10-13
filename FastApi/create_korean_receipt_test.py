#!/usr/bin/env python3
"""
고해상도 한글 영수증 테스트 이미지 생성
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_korean_receipt():
    # 고해상도 이미지 생성 (A4 사이즈, 300 DPI)
    width, height = 2480, 3508  # A4 at 300 DPI
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)

    # 폰트 설정 시도 (시스템에 있는 한글 폰트 찾기)
    fonts_to_try = [
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    ]

    font_large = None
    font_medium = None
    font_small = None

    for font_path in fonts_to_try:
        if os.path.exists(font_path):
            try:
                font_large = ImageFont.truetype(font_path, 80)
                font_medium = ImageFont.truetype(font_path, 60)
                font_small = ImageFont.truetype(font_path, 40)
                break
            except:
                continue

    # 폰트가 없으면 기본 폰트 사용
    if not font_large:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 영수증 텍스트 (한글)
    texts = [
        ("이마트 성수점", font_large, 200),
        ("사업자등록번호: 123-45-67890", font_medium, 300),
        ("주소: 서울시 성동구 성수동", font_medium, 360),
        ("전화: 02-1234-5678", font_medium, 420),
        ("", font_medium, 480),
        ("구매내역", font_large, 540),
        ("────────────────────", font_medium, 600),
        ("바나나 1kg              3,500원", font_medium, 660),
        ("사과 2kg               7,000원", font_medium, 720),
        ("우유 1L                2,800원", font_medium, 780),
        ("김치 500g              4,200원", font_medium, 840),
        ("계란 10개              3,000원", font_medium, 900),
        ("────────────────────", font_medium, 960),
        ("소계                  20,500원", font_medium, 1020),
        ("부가세                 2,050원", font_medium, 1080),
        ("총계                  22,550원", font_large, 1140),
        ("", font_medium, 1200),
        ("결제방법: 신용카드", font_medium, 1260),
        ("승인번호: 12345678", font_medium, 1320),
        ("일시: 2024년 3월 15일 14:30", font_medium, 1380),
        ("", font_medium, 1440),
        ("감사합니다", font_large, 1500),
        ("또 방문해 주세요!", font_medium, 1560)
    ]

    # 텍스트 그리기
    for text, font, y in texts:
        if text:  # 빈 문자열이 아닌 경우만
            # 텍스트 중앙 정렬
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            draw.text((x, y), text, fill='black', font=font)

    return image

def main():
    # 테스트 디렉토리 생성
    os.makedirs('demo/korean_test', exist_ok=True)

    # 고해상도 한글 영수증 생성
    receipt = create_korean_receipt()
    receipt.save('demo/korean_test/korean_receipt_hd.png', quality=95, dpi=(300, 300))

    print("✅ 고해상도 한글 영수증 테스트 이미지가 생성되었습니다:")
    print("   demo/korean_test/korean_receipt_hd.png")

if __name__ == "__main__":
    main()