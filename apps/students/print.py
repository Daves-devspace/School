import os
from django.http import HttpResponse
from django.shortcuts import render
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
import openpyxl
from openpyxl.styles import Font, Alignment

from School import settings
from apps.management.models import Institution
from apps.students.models import Student

def get_filtered_students(request):
    """Filters students based on query parameters from the request."""
    students = Student.objects.all()

    # Get filter parameters
    grade = request.GET.get("grade")
    section = request.GET.get("section")
    gender = request.GET.get("gender")
    status = request.GET.get("status")

    # Apply filters if values exist
    if grade:
        students = students.filter(grade__name=grade)
    if section:
        students = students.filter(section=section)
    if gender:
        students = students.filter(gender=gender)
    if status:
        students = students.filter(status=status)

    return students

def export_students_pdf(request):
    """Generates a PDF for the filtered students list."""
    institution = Institution.objects.first()
    students = get_filtered_students(request)  # Use filtered students

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="students_list.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y_position = height - 50

    # Add institution details
    if institution:
        if institution.logo:
            logo_path = os.path.join(settings.MEDIA_ROOT, institution.logo.name)
            if os.path.exists(logo_path):
                p.drawImage(ImageReader(logo_path), 40, y_position - 40, width=60, height=60)

        p.setFont("Helvetica-Bold", 14)
        p.drawString(120, y_position, institution.name)
        p.setFont("Helvetica", 10)
        p.drawString(120, y_position - 15, f"Email: {institution.email_address}")
        p.drawString(120, y_position - 30, f"Phone: {institution.mobile_number}")
        p.drawString(120, y_position - 45, f"Address: {institution.address}")

    y_position -= 80

    # Table Headers
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y_position, "No.")
    p.drawString(100, y_position, "Admission No")
    p.drawString(200, y_position, "Name")
    p.drawString(400, y_position, "Grade")
    p.drawString(500, y_position, "Status")
    y_position -= 20

    # Populate students
    p.setFont("Helvetica", 10)
    count = 1
    for student in students:
        if y_position < 50:
            p.showPage()
            y_position = height - 50

        p.drawString(50, y_position, str(count))
        p.drawString(100, y_position, student.admission_number)
        p.drawString(200, y_position, f"{student.first_name} {student.last_name}")
        p.drawString(400, y_position, student.grade.name if student.grade else "N/A")
        p.drawString(500, y_position, student.status)

        y_position -= 20
        count += 1

    p.showPage()
    p.save()
    return response

def export_students_excel(request):
    """Generates an Excel file for the filtered students list."""
    students = get_filtered_students(request)  # Use filtered students

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Students List"

    headers = ["No.", "Admission No", "First Name", "Last Name", "Gender", "Date of Birth", "Grade", "Status", "Joining Date", "Sponsored"]
    ws.append(headers)

    # Style headers
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    # Populate students
    for index, student in enumerate(students, start=1):
        ws.append([
            index,
            student.admission_number,
            student.first_name,
            student.last_name,
            student.gender,
            student.date_of_birth.strftime("%Y-%m-%d"),
            student.grade.name if student.grade else "N/A",
            student.status,
            student.joining_date.strftime("%Y-%m-%d"),
            "Yes" if student.sponsored else "No"
        ])

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="students_list.xlsx"'
    wb.save(response)
    return response

def print_students(request):
    """Renders the print template with the filtered students list."""
    students = get_filtered_students(request)
    institution = Institution.objects.first()

    context = {
        "students": students,
        "institution": institution
    }
    return render(request, "students/query_students.html", context)
