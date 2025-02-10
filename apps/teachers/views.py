from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.db import transaction
from django.db.models import Q, OuterRef, Count, Subquery
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
from phonenumbers import is_valid_number, parse

from apps.management.models import Profile
from apps.students.models import Grade, GradeSection
from .forms import TeacherForm, TeacherAssignmentForm
# from .forms import TeacherForm
from .models import Teacher, Department, TeacherRole, Role, TeacherAssignment


@login_required
def teachers(request):
    teachers = Teacher.objects.select_related('user', 'user__profile', "assigned_class").all()
    grades = GradeSection.objects.all()

    return render(request, "teachers/teachers.html", {"teachers": teachers, 'grades': grades})


@login_required
def add_teacher(request):
    if request.method == 'POST':
        form = TeacherForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    teacher = form.save(commit=False)

                    if teacher is None:
                        messages.error(request, "Failed to create teacher instance.")
                        return render(request, 'teachers/add-teacher.html', {'form': form})

                    if not teacher.staff_number:
                        teacher.staff_number = Teacher.generate_staff_number()

                    teacher.save()  # Save before assigning ManyToMany fields

                    # Assign ManyToManyField subjects
                    if 'subjects' in request.POST:
                        teacher.subjects.set(request.POST.getlist('subjects'))

                    # Handle password securely
                    if teacher.user and 'password' in request.POST:
                        teacher.user.set_password(request.POST['password'])
                        teacher.user.save()

                    # Add user to "Teacher" group
                    if teacher.user:
                        group, _ = Group.objects.get_or_create(name='Teacher')
                        teacher.user.groups.add(group)

                    messages.success(request, "Teacher added successfully.")
                    return redirect('teachers')
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
        else:
            messages.error(request, "Form validation failed. Please correct the errors below.")
    else:
        form = TeacherForm()

    return render(request, 'teachers/add-teacher.html', {'form': form})


@login_required
def edit_teacher(request, id):
    # Retrieve the teacher instance or return a 404 if not found
    teacher = get_object_or_404(Teacher, pk=id)

    if request.method == 'POST':
        # Populate the form with POST data and the existing instance
        form = TeacherForm(request.POST, instance=teacher)
        if form.is_valid():
            teacher = form.save()

            # Update the teacher's subjects if provided in the request
            subject_ids = request.POST.getlist('subjects')  # 'subjects' is the name of the form field
            teacher.subjects.set(subject_ids)  # Update subjects directly
            teacher.save()

            messages.success(request, "Teacher updated successfully.")
            return redirect('teachers')  # Redirect to the teachers list
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # Prepopulate the form with the existing teacher instance
        form = TeacherForm(instance=teacher)

    return render(request, 'teachers/edit_teacher.html', {'form': form, 'teacher': teacher})


@login_required
def teacher_detail(request, id):
    teacher = get_object_or_404(Teacher, pk=id)
    teachers_subject = teacher.subjects.all()
    return render(request, 'teachers/teacher_detail.html', {'teacher': teacher, 'subjects': teachers_subject})


def teacher_assignments(request, assignment_id=None):
    # If assignment_id is passed, we are editing an existing assignment
    if assignment_id:
        assignment = get_object_or_404(TeacherAssignment, id=assignment_id)
    else:
        assignment = None

    if request.method == 'POST':
        form = TeacherAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            return redirect('teacher_assignments')  # Redirect to the list of assignments
        else:
            # Print the form errors to debug
            print(form.errors)
    else:
        form = TeacherAssignmentForm(instance=assignment)

    # Fetch existing assignments for the list
    assignments = TeacherAssignment.objects.all().order_by('grade_section__grade', 'subject__name')

    return render(request, 'teachers/teacher_assignments.html', {
        'form': form,
        'assignments': assignments
    })


def delete_teacher_assignment(request, assignment_id):
    assignment = get_object_or_404(TeacherAssignment, id=assignment_id)
    assignment.delete()
    return redirect('teacher_assignments')


# def record_marks_view(request, subject_id, term_id):
#     subject = get_object_or_404(Subject, id=subject_id)
#     term = get_object_or_404(Term, id=term_id)
#
#     # Check if the logged-in user is the teacher for this subject
#     if request.user != subject.teacher.user_name:
#         return redirect('unauthorized_page')  # Handle unauthorized access
#
#     students = Student.objects.filter(grade=subject.grade)
#
#     if request.method == 'POST':
#         form = PerformanceForm(request.POST)
#         if form.is_valid():
#             # Save the performance data
#             performance = form.save(commit=False)
#             performance.subject = subject
#             performance.term = term
#             performance.save()
#             return redirect('success_page')  # Redirect to a success page
#     else:
#         form = PerformanceForm()
#
#     context = {
#         'subject': subject,
#         'term': term,
#         'students': students,
#         'form': form,
#     }
#     return render(request, 'teachers/record_marks.html', context)


@login_required
def assign_hod_and_teachers(request, id):
    department = get_object_or_404(Department, pk=id)
    teachers = Teacher.objects.all()

    if request.method == 'POST':
        hod_id = request.POST.get('hod')

        try:
            # Assign the HOD (Head of Department)
            if hod_id:
                hod = get_object_or_404(Teacher, pk=hod_id)
                department.hod = hod
                department.save()
                messages.success(request, f"{hod.staff_number} has been assigned as the HOD.")

            return redirect('teachers_department')  # Redirect to the teachers department list page

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('teachers_department')

    search_query = request.GET.get('search', '')
    if search_query:
        teachers = teachers.filter(Q(full_name__icontains=search_query) | Q(teacher_id__icontains=search_query))

    return render(request, 'teachers/assign_department.html', {
        'department': department,
        'teachers': teachers,
        'search_query': search_query
    })


def assign_teachers_to_department(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    roles = Role.objects.all()
    teachers = Teacher.objects.exclude(teaching_departments=department)  # Exclude teachers already assigned

    if request.method == "POST":
        teacher_id = request.POST.get('teacher')
        role_id = request.POST.get('role')

        teacher = get_object_or_404(Teacher, id=teacher_id)
        role = get_object_or_404(Role, id=role_id)

        # Check if the teacher is already assigned to this department with this role
        if TeacherRole.objects.filter(teacher=teacher, department=department, role=role).exists():
            messages.warning(request,
                             f"{teacher.staff_number} is already assigned to {department.name} as {role.name}.")
        else:
            TeacherRole.objects.create(teacher=teacher, department=department, role=role)
            messages.success(request,
                             f"{teacher.staff_number} has been successfully added to {department.name} as {role.name}.")

        return redirect('assign_teachers_to_department', department_id=department_id)

    context = {
        'department': department,
        'teachers': teachers,
        'roles': roles,
    }
    return render(request, 'teachers/add_departmental_teachers.html', context)


def remove_teacher_from_department(request, department_id, teacher_id):
    # Get the department and teacher objects
    department = get_object_or_404(Department, id=department_id)
    teacher = get_object_or_404(Teacher, id=teacher_id)

    # Remove the teacher from the department
    if teacher in department.teachers.all():  # Assuming a ManyToMany relationship
        department.teachers.remove(teacher)
        messages.success(request, f"{teacher.staff_number} has been removed from the department.")
    else:
        messages.warning(request, f"{teacher.staff_number} is not part of the department.")

    # Redirect back to the department details page or another relevant page
    return redirect('assign_teachers_to_department', department_id=department.id)


@login_required
def assign_grade(request):
    # This view is expected to be used in a modal within the class teachers page.
    teacher = get_object_or_404(Teacher, pk=request.POST.get('teacher_id'))
    grades = GradeSection.objects.all()

    if request.method == 'POST':
        grade_id = request.POST.get('assigned_class')
        confirm_removal = request.POST.get('confirm_removal', 'false') == 'true'

        if grade_id:
            assigned_grade = get_object_or_404(GradeSection, pk=grade_id)
            previous_class = GradeSection.objects.filter(class_teacher=teacher).first()

            if previous_class:
                if previous_class.id == assigned_grade.id:
                    messages.warning(request, "This teacher is already assigned to the selected class.")
                    return redirect('class_teachers')

                # If teacher is already assigned to a different class
                if not confirm_removal:
                    # Render the assignment form again with a confirmation request.
                    messages.warning(request,
                                     f"Teacher {teacher.staff_number} is already assigned to {previous_class}. Please confirm removal of the current assignment.")
                    return render(request, 'teachers/assign_class_teachers.html', {
                        'teacher': teacher,
                        'grades': grades,
                        'confirm_removal_required': True,
                        'previous_class': previous_class
                    })

                # If confirmed, remove teacher from the previous assigned class.
                previous_class.class_teacher = None
                previous_class.save()
                messages.info(request, f"Teacher {teacher.staff_number} has been removed from the previous class.")

            # Assign teacher to the new class.
            assigned_grade.class_teacher = teacher
            assigned_grade.save()
            messages.success(request,
                             f"Teacher {teacher.staff_number} has been successfully assigned to {assigned_grade}.")
            return redirect('class_teachers')

        messages.error(request, "Invalid Grade Selection")
        return redirect('class_teachers')

    # For GET, simply redirect back (this view is mainly for POST).
    return redirect('class_teachers')


@login_required
def class_teachers(request):
    # Subquery to fetch the student count for the GradeSection where the teacher is assigned.
    assigned_class_qs = (
        GradeSection.objects
        .filter(class_teacher=OuterRef('pk'))
        .annotate(num_students=Count('students'))
        .values('num_students')[:1]
    )
    teachers = Teacher.objects.annotate(student_count=Subquery(assigned_class_qs))
    return render(request, "teachers/class_teachers.html", {"teachers": teachers})


# def assign_grade(request, teacher_id):
#     teacher = get_object_or_404(Teacher, id=teacher_id)
#     combined_classes = Section.objects.select_related('grade')  # Combine Grade and Section
#
#     if request.method == "POST":
#         section_id = request.POST.get("assigned_section")
#         grade_id = request.POST.get("assigned_class")
#         if grade_id:
#             selected_grade = get_object_or_404(Grade, id=grade_id)
#             teacher.assigned_class = selected_grade
#         if section_id:
#             selected_section = get_object_or_404(Section, id=section_id)
#             teacher.assigned_class = selected_section.grade  # Assign the grade
#             teacher.section = selected_section  # Assign the section
#             teacher.save()
#
#             # Add success message
#             messages.success(
#                 request,
#                 f"Teacher {teacher.full_name} has been successfully assigned to {selected_section.grade.name} - {selected_section.name}."
#             )
#             return redirect('class_teachers')  # Replace with your actual URL name for redirection
#         else:
#             messages.error(request, "A class with a section must be selected.")
#
#     return render(request, 'teachers/assign_class_teachers.html', {
#         'teacher': teacher,
#         'combined_classes': combined_classes,
#     })


# def assign_grade(request, teacher_id):
#     teacher = get_object_or_404(Teacher, id=teacher_id)
#     grades = Grade.objects.all()
#     sections = None  # Initialize sections as None
#
#     if request.method == "POST":
#         grade_id = request.POST.get("assigned_class")
#         section_id = request.POST.get("section")
#
#         if grade_id and section_id:
#             selected_grade = get_object_or_404(Grade, id=grade_id)
#             selected_section = get_object_or_404(Section, id=section_id)
#
#             # Assign both grade and section to the teacher
#             teacher.assigned_class = selected_grade
#             teacher.section = selected_section
#             teacher.save()
#
#             # Add success message
#             messages.success(
#                 request,
#                 f"Teacher {teacher.full_name} has been successfully assigned to {selected_grade.name} - {selected_section.name}."
#             )
#
#             # Redirect to a relevant page
#             return redirect('teachers_list')  # Replace with your actual URL name for the teachers list page
#         else:
#             messages.error(request, "Both grade and section must be selected.")
#
#     # If the grade is selected but not submitted, show sections for that grade
#     elif teacher.assigned_class:
#         sections = Section.objects.filter(grade=teacher.assigned_class)
#     else:
#         sections = Section.objects.none()  # No sections initially
#
#     return render(request, 'teachers/assign_class_teachers.html', {
#         'teacher': teacher,
#         'grades': grades,
#         'sections': sections,
#     })


# def assign_grade(request, teacher_id):
#     teacher = get_object_or_404(Teacher, id=teacher_id)
#     grades = Grade.objects.all()
#
#     if request.method == 'POST':
#         grade_id = request.POST.get('assigned_class')
#         section_id = request.POST.get("section")
#
#         asigned_grade = get_object_or_404(Grade, id=grade_id)
#         section = get_object_or_404(Section, id=section_id, asigned_grade=asigned_grade)
#
#         teacher.assigned_class = asigned_grade
#         teacher.assigned_section = section
#         teacher.save()
#
#         messages.success(
#             request,
#             f"{teacher.full_name} has been assigned to {section} in {grade.name}.",
#         )
#         return redirect('class_teachers')  # Replace with your redirect URL
#
#     return render(request, 'teachers/assign_class_teachers.html', {'teacher': teacher, 'grades': grades})


@login_required
def teachers_department(request):
    # Prefetch TeacherRole objects with related teacher and role
    departments = Department.objects.prefetch_related(
        'teacherrole_set__teacher',  # Prefetch teachers through TeacherRole
        'teacherrole_set__role'  # Prefetch roles through TeacherRole
    ).select_related('hod')  # Optionally, select HOD to avoid additional queries
    return render(request, "teachers/teacher_department.html", {'departments': departments})


@login_required
def department_list(request):
    # Prefetch TeacherRole objects with related teacher and role
    departments = Department.objects.prefetch_related(
        'teacherrole_set__teacher',  # Prefetch teachers through TeacherRole
        'teacherrole_set__role'  # Prefetch roles through TeacherRole
    ).select_related('hod')  # Optionally, select HOD to avoid additional queries

    return render(request, 'teachers/departments.html', {'departments': departments})


@login_required
def add_department(request):
    departments = Department.objects.all()

    if request.method == "POST":
        # Handle adding a new department
        department_name = request.POST.get("name")
        department_hod = request.POST.get("hod")
        if department_name:
            department, created = Department.objects.get_or_create(name=department_name)
            if created:
                messages.success(request, "Department added successfully!")
            else:
                messages.warning(request, "This department already exists!")
        else:
            messages.error(request, "Department name cannot be empty!")
        return redirect("departments")

    return render(request, "teachers/add_department.html", {"departments": departments})

# # Get all teachers in a specific department
# department = Department.objects.get(name="Science")
# teachers_in_department = TeacherRole.objects.filter(department=department)
#
# # Get teachers by role
# deans = TeacherRole.objects.filter(department=department, role__name="Dean")
# sports_heads = TeacherRole.objects.filter(department=department, role__name="Sports")
#
# # Example: Display all teachers with their roles in a department
# for teacher_role in teachers_in_department:
#     print(f"{teacher_role.teacher.name} - {teacher_role.role.name}")
