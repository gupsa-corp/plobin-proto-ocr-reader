#!/usr/bin/env python3
"""
테스트용 이미지 생성 스크립트
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_test_receipt():
    """테스트용 영수증 이미지 생성"""
    # 이미지 크기
    width, height = 400, 600

    # 배경색 (흰색)
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # 폰트 설정 (기본 폰트 사용)
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    y_pos = 30

    # 매장명
    draw.text((width//2 - 80, y_pos), "TEST CAFE", fill='black', font=font_large)
    y_pos += 40

    # 주소
    draw.text((50, y_pos), "Seoul Gangnam-gu", fill='black', font=font_small)
    y_pos += 25

    # 전화번호
    draw.text((50, y_pos), "Tel: 02-1234-5678", fill='black', font=font_small)
    y_pos += 40

    # 구분선
    draw.line([(30, y_pos), (width-30, y_pos)], fill='black', width=1)
    y_pos += 30

    # 메뉴 항목들
    menu_items = [
        ("Americano", "4,500"),
        ("Cafe Latte", "5,000"),
        ("Croissant", "3,500"),
        ("Cheesecake", "6,000")
    ]

    for item, price in menu_items:
        draw.text((50, y_pos), item, fill='black', font=font_medium)
        draw.text((width-120, y_pos), price, fill='black', font=font_medium)
        y_pos += 30

    # 구분선
    y_pos += 10
    draw.line([(30, y_pos), (width-30, y_pos)], fill='black', width=1)
    y_pos += 30

    # 합계
    draw.text((50, y_pos), "Total", fill='black', font=font_large)
    draw.text((width-150, y_pos), "19,000 Won", fill='black', font=font_large)
    y_pos += 40

    # 결제 정보
    draw.text((50, y_pos), "Payment: Card", fill='black', font=font_medium)
    y_pos += 30

    # 날짜
    draw.text((50, y_pos), "2025-10-10 14:30", fill='black', font=font_small)

    return img

def create_test_invoice():
    """테스트용 송장 이미지 생성"""
    width, height = 500, 700
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    y_pos = 30

    # 제목
    draw.text((width//2 - 50, y_pos), "INVOICE", fill='black', font=font_large)
    y_pos += 50

    # 송장 번호
    draw.text((50, y_pos), "Invoice #: INV-2025-001", fill='black', font=font_medium)
    y_pos += 30

    # 날짜
    draw.text((50, y_pos), "Date: 2025-10-10", fill='black', font=font_medium)
    y_pos += 50

    # 발송자 정보
    draw.text((50, y_pos), "From:", fill='black', font=font_medium)
    y_pos += 25
    draw.text((70, y_pos), "ABC Company Ltd.", fill='black', font=font_small)
    y_pos += 20
    draw.text((70, y_pos), "123 Business St.", fill='black', font=font_small)
    y_pos += 20
    draw.text((70, y_pos), "Seoul, Korea", fill='black', font=font_small)
    y_pos += 40

    # 수신자 정보
    draw.text((50, y_pos), "To:", fill='black', font=font_medium)
    y_pos += 25
    draw.text((70, y_pos), "XYZ Corporation", fill='black', font=font_small)
    y_pos += 20
    draw.text((70, y_pos), "456 Client Ave.", fill='black', font=font_small)
    y_pos += 20
    draw.text((70, y_pos), "Busan, Korea", fill='black', font=font_small)
    y_pos += 50

    # 항목 헤더
    draw.line([(30, y_pos), (width-30, y_pos)], fill='black', width=1)
    y_pos += 10
    draw.text((50, y_pos), "Description", fill='black', font=font_medium)
    draw.text((250, y_pos), "Qty", fill='black', font=font_medium)
    draw.text((300, y_pos), "Price", fill='black', font=font_medium)
    draw.text((380, y_pos), "Amount", fill='black', font=font_medium)
    y_pos += 25
    draw.line([(30, y_pos), (width-30, y_pos)], fill='black', width=1)
    y_pos += 20

    # 항목들
    items = [
        ("Web Development", "1", "$5,000", "$5,000"),
        ("Design Services", "1", "$2,000", "$2,000"),
        ("Maintenance", "12", "$300", "$3,600")
    ]

    for desc, qty, price, amount in items:
        draw.text((50, y_pos), desc, fill='black', font=font_small)
        draw.text((250, y_pos), qty, fill='black', font=font_small)
        draw.text((300, y_pos), price, fill='black', font=font_small)
        draw.text((380, y_pos), amount, fill='black', font=font_small)
        y_pos += 25

    # 합계
    y_pos += 20
    draw.line([(250, y_pos), (width-30, y_pos)], fill='black', width=1)
    y_pos += 20
    draw.text((300, y_pos), "Total: $10,600", fill='black', font=font_medium)

    return img

if __name__ == "__main__":
    # demo 디렉토리 생성
    os.makedirs("demo/images", exist_ok=True)

    # 테스트 이미지 생성
    receipt = create_test_receipt()
    receipt.save("demo/images/test_receipt.png")
    print("✅ 테스트 영수증 이미지 생성: demo/images/test_receipt.png")

    invoice = create_test_invoice()
    invoice.save("demo/images/test_invoice.png")
    print("✅ 테스트 송장 이미지 생성: demo/images/test_invoice.png")

    print("\n이제 다음 명령어로 테스트할 수 있습니다:")
    print("curl -X POST -F 'file=@demo/images/test_receipt.png' http://localhost:6003/process-request")