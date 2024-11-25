from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle
from datetime import datetime
from .db import get_student_at_risk, get_students_graduating_on_time, get_students_without_prediction  # Adjust to your actual function to fetch data from the DB

def generate_pdf():
    # Create a BytesIO object to hold the PDF in memory
    pdf_buffer = BytesIO()

    # Create a PDF document in memory
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter  # Letter page size in points

    # Fetch current date and time
    report_generated_at = datetime.now().strftime("%B %d, %Y %I:%M:%S %p")

    # Function to add a footer
    def add_footer():
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.gray)
        footer_text = f"Report Generated On: {report_generated_at}"
        footer_width = c.stringWidth(footer_text, "Helvetica", 9)
        c.drawString((width - footer_width) / 2, 15, footer_text)  # 15 points from the bottom

    # Add logo (provide the path to your logo image file)
    logo_path = "website/static/images/PLP.png"
    try:
        c.drawImage(logo_path, 30, height - 100, width=100, height=80, mask='auto')
    except Exception as e:
        print(f"Error loading image: {e}")

    # Add school name and address
    school_name = "PAMANTASAN NG LUNGSOD NG PASIG"
    c.setFont("Helvetica-Bold", 12)
    school_name_width = c.stringWidth(school_name, "Helvetica-Bold", 12)
    c.drawString((width - school_name_width) / 2, height - 50, school_name)

    address = "ALCALDE JOSE ST. KAPASIGAN PASIG CITY"
    c.setFont("Helvetica", 10)
    address_width = c.stringWidth(address, "Helvetica", 10)
    c.drawString((width - address_width) / 2, height - 65, address)

    program = "COLLEGE OF COMPUTER STUDIES"
    c.setFont("Helvetica", 10)
    program_width = c.stringWidth(program, "Helvetica", 10)
    c.drawString((width - program_width) / 2, height - 80, program)

    logo_path_two = "website/static/images/CSS.png"
    try:
        c.drawImage(logo_path_two, 475, height - 100, width=100, height=80, mask='auto')
    except Exception as e:
        print(f"Error loading image: {e}")

    # Draw a line to separate the header section
    c.setStrokeColor(colors.gray)
    c.setLineWidth(0.5)
    c.line(50, height - 105, width - 50, height - 105)

    # Page content margins
    left_margin = 30
    top_margin = 150
    current_y_position = height - top_margin

    # Function to add a new page
    def add_new_page():
        nonlocal current_y_position
        add_footer()  # Add footer before ending the page
        c.showPage()  # Create a new page
        current_y_position = height - 50  # Reset Y position for the new page

    # Function to draw a table
    def draw_table(title, headers, data_rows, col_widths):
        nonlocal current_y_position
        # Check if there's enough space; if not, create a new page
        table = Table([headers] + data_rows, colWidths=col_widths)
        table.wrapOn(c, width - 2 * left_margin, current_y_position)
        if current_y_position - table._height < 50:  # Adjust threshold as needed
            add_new_page()

        # Draw the title
        c.setFont("Helvetica-Bold", 16)
        title_width = c.stringWidth(title, "Helvetica-Bold", 16)
        c.drawString((width - title_width) / 2, current_y_position, title)
        current_y_position -= 20  # Space below title

        # Draw the table
        table_style = TableStyle([
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 0), (0.0745, 0.482, 0.208)),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
        ])
        table.setStyle(table_style)
        table.drawOn(c, left_margin, current_y_position - table._height)
        current_y_position -= table._height + 30  # Space below table

    # Draw the first table: Students At Risk
    students_at_risk = get_student_at_risk()
    data_students_at_risk = [
        [str(student["id"]), student["name"], str(student["percentage"]), student["factor"], student["intervention"]]
        for student in students_at_risk
    ]
    draw_table(
        title="STUDENTS AT RISK",
        headers=["STUDID", "STUDENT NAME", "PERCENTAGE", "FACTORS", "INTERVENTION"],
        data_rows=data_students_at_risk,
        col_widths=[0.8 * inch, 2.3 * inch, 1.05 * inch, 2.3 * inch, 1 * inch]
    )

    # Draw the second table: Students Graduating on Time
    students_graduating_on_time = get_students_graduating_on_time()
    data_graduating_on_time = [
        [str(student["id"]), student["name"], str(student["percentage"])]
        for student in students_graduating_on_time
    ]
    draw_table(
        title="STUDENTS GRADUATING ON TIME",
        headers=["STUDID", "STUDENT NAME", "PERCENTAGE"],
        data_rows=data_graduating_on_time,
        col_widths=[1.45 * inch, 3 * inch, 3 * inch]
    )

    # Draw the third table: Students Without Prediction
    students_without = get_students_without_prediction()
    data_students_without = [
        [str(student["id"]), student["name"]]
        for student in students_without
    ]
    draw_table(
        title="STUDENTS WITHOUT PREDICTIONS",
        headers=["STUDID", "STUDENT NAME"],
        data_rows=data_students_without,
        col_widths=[1.45 * inch, 6 * inch]
    )

    # Add footer on the last page
    add_footer()

    # Save the PDF to the in-memory buffer
    c.save()
    pdf_buffer.seek(0)

    return pdf_buffer
