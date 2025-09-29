#!/usr/bin/env python3
"""
Demo PDF 파일 생성기
다양한 타입의 PDF 샘플들을 생성합니다.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
import os
from datetime import datetime


def create_invoice_pdf():
    """인보이스 PDF 생성"""
    filename = "demo/invoices/sample_invoice.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()

    # 제목 스타일
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # center
    )

    story = []

    # 헤더
    story.append(Paragraph("INVOICE", title_style))
    story.append(Spacer(1, 20))

    # 회사 정보
    company_info = [
        ["From:", "ABC Company Ltd."],
        ["", "123 Business Street"],
        ["", "Seoul, Korea 12345"],
        ["", "Tel: (02) 123-4567"],
        ["", "Email: info@abc.com"]
    ]

    client_info = [
        ["To:", "Client Company"],
        ["", "456 Client Avenue"],
        ["", "Busan, Korea 54321"],
        ["", ""]
    ]

    # 정보 테이블
    info_table = Table([
        [Table(company_info, colWidths=[0.8*inch, 2*inch]),
         Table(client_info, colWidths=[0.5*inch, 2*inch])]
    ], colWidths=[3*inch, 3*inch])

    story.append(info_table)
    story.append(Spacer(1, 30))

    # 인보이스 상세
    details = [
        ["Invoice #:", "INV-2024-001"],
        ["Date:", datetime.now().strftime("%Y-%m-%d")],
        ["Due Date:", "2024-04-15"]
    ]

    details_table = Table(details, colWidths=[1.5*inch, 2*inch])
    details_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
    ]))

    story.append(details_table)
    story.append(Spacer(1, 30))

    # 아이템 테이블
    items_data = [
        ["Description", "Quantity", "Unit Price", "Amount"],
        ["Web Development Services", "40", "$100.00", "$4,000.00"],
        ["Design Consultation", "10", "$150.00", "$1,500.00"],
        ["Domain & Hosting", "1", "$200.00", "$200.00"],
        ["", "", "Subtotal:", "$5,700.00"],
        ["", "", "Tax (10%):", "$570.00"],
        ["", "", "Total:", "$6,270.00"]
    ]

    items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1*inch, 1*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-4), colors.beige),
        ('GRID', (0,0), (-1,-4), 1, colors.black),
        ('FONTNAME', (2,-3), (-1,-1), 'Helvetica-Bold'),
        ('BACKGROUND', (2,-1), (-1,-1), colors.lightgrey),
    ]))

    story.append(items_table)
    story.append(Spacer(1, 30))

    # 결제 조건
    story.append(Paragraph("Payment Terms:", styles['Heading3']))
    story.append(Paragraph("Payment is due within 30 days of invoice date. Late payments may be subject to fees.", styles['Normal']))

    doc.build(story)
    return filename


def create_technical_manual_pdf():
    """기술 매뉴얼 PDF 생성"""
    filename = "demo/manuals/technical_manual.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()

    story = []

    # 제목 페이지
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=28,
        spaceAfter=50,
        alignment=1
    )

    story.append(Paragraph("Technical Manual", title_style))
    story.append(Paragraph("Software Installation Guide", styles['Heading2']))
    story.append(Spacer(1, 100))
    story.append(Paragraph("Version 2.1", styles['Normal']))
    story.append(Paragraph(f"Updated: {datetime.now().strftime('%B %Y')}", styles['Normal']))
    story.append(PageBreak())

    # 목차
    story.append(Paragraph("Table of Contents", styles['Heading1']))
    story.append(Spacer(1, 20))

    toc_data = [
        ["1. Introduction", "3"],
        ["2. System Requirements", "4"],
        ["3. Installation Steps", "5"],
        ["4. Configuration", "7"],
        ["5. Troubleshooting", "9"],
        ["6. Support", "11"]
    ]

    toc_table = Table(toc_data, colWidths=[4*inch, 1*inch])
    toc_table.setStyle(TableStyle([
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('LEFTPADDING', (0,0), (0,-1), 0),
        ('RIGHTPADDING', (1,0), (1,-1), 0),
    ]))

    story.append(toc_table)
    story.append(PageBreak())

    # 내용
    story.append(Paragraph("1. Introduction", styles['Heading1']))
    story.append(Paragraph(
        "This manual provides comprehensive instructions for installing and configuring "
        "our software system. Please read all sections carefully before beginning the installation process.",
        styles['Normal']
    ))
    story.append(Spacer(1, 20))

    story.append(Paragraph("2. System Requirements", styles['Heading1']))
    req_data = [
        ["Component", "Minimum", "Recommended"],
        ["Operating System", "Windows 10", "Windows 11"],
        ["RAM", "4 GB", "8 GB"],
        ["Storage", "2 GB", "5 GB"],
        ["Network", "Broadband", "High-speed"]
    ]

    req_table = Table(req_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
    req_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,1), (-1,-1), colors.lightblue),
    ]))

    story.append(req_table)
    story.append(Spacer(1, 20))

    story.append(Paragraph("3. Installation Steps", styles['Heading1']))
    steps = [
        "1. Download the installer from our official website",
        "2. Run the installer as administrator",
        "3. Follow the installation wizard",
        "4. Accept the license agreement",
        "5. Choose installation directory",
        "6. Complete the installation"
    ]

    for step in steps:
        story.append(Paragraph(step, styles['Normal']))
        story.append(Spacer(1, 10))

    doc.build(story)
    return filename


def create_business_report_pdf():
    """비즈니스 리포트 PDF 생성"""
    filename = "demo/reports/quarterly_report.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()

    story = []

    # 제목
    story.append(Paragraph("Quarterly Business Report", styles['Title']))
    story.append(Paragraph("Q1 2024 Performance Analysis", styles['Heading2']))
    story.append(Spacer(1, 30))

    # Executive Summary
    story.append(Paragraph("Executive Summary", styles['Heading1']))
    story.append(Paragraph(
        "This report presents our company's performance for the first quarter of 2024. "
        "We achieved significant growth in revenue and expanded our market presence. "
        "Key highlights include a 25% increase in sales, successful product launches, "
        "and improved customer satisfaction ratings.",
        styles['Normal']
    ))
    story.append(Spacer(1, 20))

    # 재무 데이터
    story.append(Paragraph("Financial Performance", styles['Heading1']))

    financial_data = [
        ["Metric", "Q1 2024", "Q1 2023", "Change"],
        ["Revenue", "$2.5M", "$2.0M", "+25%"],
        ["Gross Profit", "$1.5M", "$1.2M", "+25%"],
        ["Operating Expenses", "$800K", "$750K", "+6.7%"],
        ["Net Income", "$700K", "$450K", "+55.6%"]
    ]

    financial_table = Table(financial_data, colWidths=[2*inch, 1.2*inch, 1.2*inch, 1*inch])
    financial_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,1), (-1,-1), colors.lightblue),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
    ]))

    story.append(financial_table)
    story.append(Spacer(1, 20))

    # 시장 분석
    story.append(Paragraph("Market Analysis", styles['Heading1']))
    story.append(Paragraph(
        "Our market share increased from 15% to 18% during Q1. "
        "The competitive landscape remains challenging, but our innovative "
        "product offerings and customer-centric approach have positioned "
        "us well for continued growth.",
        styles['Normal']
    ))

    doc.build(story)
    return filename


def create_form_pdf():
    """양식 PDF 생성"""
    filename = "demo/forms/application_form.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()

    story = []

    # 헤더
    story.append(Paragraph("Job Application Form", styles['Title']))
    story.append(Spacer(1, 30))

    # 개인정보 섹션
    story.append(Paragraph("Personal Information", styles['Heading2']))
    story.append(Spacer(1, 10))

    personal_fields = [
        ["Full Name:", "_" * 50],
        ["Email:", "_" * 50],
        ["Phone:", "_" * 30],
        ["Address:", "_" * 50],
        ["", "_" * 50],
        ["Date of Birth:", "_" * 20]
    ]

    personal_table = Table(personal_fields, colWidths=[1.5*inch, 4*inch])
    personal_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
    ]))

    story.append(personal_table)
    story.append(Spacer(1, 30))

    # 경험 섹션
    story.append(Paragraph("Work Experience", styles['Heading2']))
    story.append(Spacer(1, 10))

    exp_fields = [
        ["Position Applied For:", "_" * 40],
        ["Previous Job Title:", "_" * 40],
        ["Company Name:", "_" * 40],
        ["Years of Experience:", "_" * 20],
        ["Skills:", "_" * 50],
        ["", "_" * 50]
    ]

    exp_table = Table(exp_fields, colWidths=[2*inch, 3.5*inch])
    exp_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
    ]))

    story.append(exp_table)
    story.append(Spacer(1, 30))

    # 서명
    story.append(Paragraph("Declaration", styles['Heading2']))
    story.append(Paragraph(
        "I declare that the information provided above is true and complete to the best of my knowledge.",
        styles['Normal']
    ))
    story.append(Spacer(1, 30))

    signature_data = [
        ["Signature:", "_" * 30, "Date:", "_" * 20]
    ]

    signature_table = Table(signature_data, colWidths=[1*inch, 2.5*inch, 0.8*inch, 1.5*inch])
    story.append(signature_table)

    doc.build(story)
    return filename


def create_presentation_pdf():
    """프레젠테이션 PDF 생성"""
    filename = "demo/presentations/company_overview.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()

    # 커스텀 스타일
    slide_title = ParagraphStyle(
        'SlideTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1,
        textColor=colors.darkblue
    )

    story = []

    # 슬라이드 1: 제목
    story.append(Paragraph("Company Overview", slide_title))
    story.append(Paragraph("Innovation Through Technology", styles['Heading2']))
    story.append(Spacer(1, 100))
    story.append(Paragraph("TechCorp Solutions", styles['Heading3']))
    story.append(Paragraph(datetime.now().strftime("%B %Y"), styles['Normal']))
    story.append(PageBreak())

    # 슬라이드 2: 회사 소개
    story.append(Paragraph("About TechCorp", slide_title))
    story.append(Spacer(1, 20))

    about_points = [
        "• Founded in 2015",
        "• Leading technology solutions provider",
        "• 500+ employees worldwide",
        "• Offices in Seoul, Tokyo, and San Francisco",
        "• Serving 1000+ clients globally"
    ]

    for point in about_points:
        story.append(Paragraph(point, styles['Normal']))
        story.append(Spacer(1, 10))

    story.append(PageBreak())

    # 슬라이드 3: 서비스
    story.append(Paragraph("Our Services", slide_title))
    story.append(Spacer(1, 20))

    services_data = [
        ["Service", "Description"],
        ["Cloud Solutions", "Scalable cloud infrastructure and migration services"],
        ["AI Development", "Custom AI and machine learning solutions"],
        ["Mobile Apps", "Cross-platform mobile application development"],
        ["Consulting", "Technology strategy and digital transformation"]
    ]

    services_table = Table(services_data, colWidths=[2*inch, 4*inch])
    services_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,1), (-1,-1), colors.lightblue),
    ]))

    story.append(services_table)
    story.append(PageBreak())

    # 슬라이드 4: 연락처
    story.append(Paragraph("Contact Us", slide_title))
    story.append(Spacer(1, 30))

    contact_info = [
        "📧 Email: contact@techcorp.com",
        "📞 Phone: +82-2-1234-5678",
        "🌐 Website: www.techcorp.com",
        "📍 Address: 123 Tech Street, Seoul, Korea"
    ]

    for info in contact_info:
        story.append(Paragraph(info, styles['Heading3']))
        story.append(Spacer(1, 15))

    doc.build(story)
    return filename


def create_legal_document_pdf():
    """법적 문서 PDF 생성"""
    filename = "demo/legal/software_license.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()

    story = []

    # 제목
    story.append(Paragraph("SOFTWARE LICENSE AGREEMENT", styles['Title']))
    story.append(Spacer(1, 30))

    # 서문
    story.append(Paragraph(
        "This Software License Agreement (\"Agreement\") is entered into between "
        "TechCorp Solutions (\"Licensor\") and the end user (\"Licensee\").",
        styles['Normal']
    ))
    story.append(Spacer(1, 20))

    # 조항들
    sections = [
        {
            "title": "1. GRANT OF LICENSE",
            "content": "Subject to the terms of this Agreement, Licensor grants to Licensee a non-exclusive, non-transferable license to use the software for internal business purposes only."
        },
        {
            "title": "2. RESTRICTIONS",
            "content": "Licensee shall not: (a) reverse engineer, decompile, or disassemble the software; (b) distribute, rent, lease, or sublicense the software; (c) remove any proprietary notices."
        },
        {
            "title": "3. TERM AND TERMINATION",
            "content": "This Agreement is effective until terminated. Licensor may terminate this Agreement immediately upon notice if Licensee breaches any term of this Agreement."
        },
        {
            "title": "4. DISCLAIMER OF WARRANTIES",
            "content": "THE SOFTWARE IS PROVIDED \"AS IS\" WITHOUT WARRANTY OF ANY KIND. LICENSOR DISCLAIMS ALL WARRANTIES, EXPRESS OR IMPLIED."
        },
        {
            "title": "5. LIMITATION OF LIABILITY",
            "content": "IN NO EVENT SHALL LICENSOR BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OF THE SOFTWARE."
        }
    ]

    for section in sections:
        story.append(Paragraph(section["title"], styles['Heading2']))
        story.append(Paragraph(section["content"], styles['Normal']))
        story.append(Spacer(1, 20))

    # 서명 섹션
    story.append(Spacer(1, 50))
    story.append(Paragraph("AGREEMENT ACCEPTANCE", styles['Heading2']))
    story.append(Spacer(1, 20))

    signature_data = [
        ["LICENSOR:", "", "LICENSEE:", ""],
        ["", "", "", ""],
        ["Signature:", "_" * 20, "Signature:", "_" * 20],
        ["Date:", "_" * 15, "Date:", "_" * 15],
        ["Name:", "_" * 20, "Name:", "_" * 20],
        ["Title:", "_" * 20, "Company:", "_" * 20]
    ]

    sig_table = Table(signature_data, colWidths=[1*inch, 2*inch, 1*inch, 2*inch])
    sig_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,0), 'Helvetica-Bold'),
        ('SPAN', (0,1), (1,1)),
        ('SPAN', (2,1), (3,1)),
    ]))

    story.append(sig_table)

    doc.build(story)
    return filename


def main():
    """모든 데모 PDF 생성"""
    print("🔨 데모 PDF 파일들을 생성 중...")

    # reportlab 설치 확인
    try:
        from reportlab.lib.pagesizes import letter
    except ImportError:
        print("❌ reportlab이 설치되지 않았습니다.")
        print("다음 명령어로 설치하세요: pip install reportlab")
        return

    created_files = []

    try:
        print("📄 인보이스 생성 중...")
        created_files.append(create_invoice_pdf())

        print("📚 기술 매뉴얼 생성 중...")
        created_files.append(create_technical_manual_pdf())

        print("📊 비즈니스 리포트 생성 중...")
        created_files.append(create_business_report_pdf())

        print("📝 지원서 양식 생성 중...")
        created_files.append(create_form_pdf())

        print("🎯 프레젠테이션 생성 중...")
        created_files.append(create_presentation_pdf())

        print("⚖️ 법적 문서 생성 중...")
        created_files.append(create_legal_document_pdf())

        print(f"\n✅ 총 {len(created_files)}개의 PDF 파일이 생성되었습니다:")
        for file in created_files:
            print(f"   📁 {file}")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")


if __name__ == "__main__":
    main()