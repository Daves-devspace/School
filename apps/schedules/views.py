from collections import defaultdict

from django.core.serializers.json import DjangoJSONEncoder
from django.db import IntegrityError, transaction
from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import TeacherAssignment, TimetableSlot, TimeSlot, Room, Subject
import random
import logging

from .serializers import TeacherAssignmentSerializer
from ..students.models import GradeSection


def rule_based_schedule():
    teacher_assignments = TeacherAssignment.objects.all()
    timetable = []

    for assignment in teacher_assignments:
        teacher = assignment.teacher
        subject = assignment.subject
        grade_section = assignment.grade_section

        # Find available time slots for the teacher
        available_time_slots = TimeSlot.objects.exclude(
            id__in=[t.time_slot.id for t in timetable if t.teacher_assignment.teacher == teacher]
        )

        for time_slot in available_time_slots:
            # Assign the first available non-special room
            room = Room.objects.filter(is_special=False).exclude(
                id__in=[t.room.id for t in timetable if t.time_slot == time_slot]
            ).first()

            if room:
                # Add the slot to the timetable
                timetable.append(TimetableSlot(
                    teacher_assignment=assignment,
                    room=room,
                    day_of_week="Monday",  # Update dynamically based on scheduling logic
                    time_slot=time_slot
                ))
                break

    return timetable


def fitness_function(timetable):
    conflicts = 0
    for slot in timetable:
        # Check for room conflicts
        if TimetableSlot.objects.filter(room=slot.room, time_slot=slot.time_slot).exists():
            conflicts += 1

        # Check for teacher conflicts
        if TimetableSlot.objects.filter(teacher_assignment__teacher=slot.teacher_assignment.teacher,
                                         time_slot=slot.time_slot).exists():
            conflicts += 1

    return -conflicts  # Lower conflicts = better fitness


def generate_initial_population(pop_size):
    population = [rule_based_schedule() for _ in range(pop_size)]
    return population


def select_parents(population):
    return random.sample(population, 2)  # Select two random parents


def crossover(parent1, parent2):
    crossover_point = random.randint(0, len(parent1) - 1)
    return parent1[:crossover_point] + parent2[crossover_point:]


def mutate(timetable):
    mutation_point = random.randint(0, len(timetable) - 1)
    swap_point = random.randint(0, len(timetable) - 1)
    timetable[mutation_point], timetable[swap_point] = timetable[swap_point], timetable[mutation_point]
    return timetable


def genetic_algorithm(pop_size=10, generations=50):
    population = generate_initial_population(pop_size)

    for _ in range(generations):
        population = sorted(population, key=fitness_function, reverse=True)
        new_population = population[:2]  # Elitism: Keep top 2

        while len(new_population) < pop_size:
            parent1, parent2 = select_parents(population)
            child = crossover(parent1, parent2)
            new_population.append(mutate(child))

        population = new_population

    return sorted(population, key=fitness_function, reverse=True)[0]


# def generate_timetable_for_all(request):
#     if request.method == "GET":
#         # Fetch all grade sections and print them
#         grade_sections = GradeSection.objects.all().order_by('grade_id', 'id').distinct('grade_id')
#         print(f"Grade Sections: {grade_sections}")
#
#         all_timetables = []
#
#         for grade_section in grade_sections:
#             # Fetch teacher assignments for the current grade section
#             teacher_assignments = TeacherAssignment.objects.filter(grade_section=grade_section)
#             print(f"Teacher Assignments for {grade_section}: {teacher_assignments}")
#
#             if not teacher_assignments.exists():
#                 print(f"No teacher assignments found for {grade_section}. Skipping...")
#                 continue
#
#             # Fetch timetable slots for the current grade section
#             timetable_slots = TimetableSlot.objects.filter(
#                 teacher_assignment__in=teacher_assignments
#             ).select_related(
#                 'teacher_assignment__teacher',
#                 'teacher_assignment__subject',
#                 'room',
#                 'time_slot'
#             )
#             print(f"Timetable Slots for {grade_section}: {timetable_slots}")
#
#             if timetable_slots.exists():
#                 slots_data = []
#                 for slot in timetable_slots:
#                     print(
#                         f"Processing TimetableSlot: Day: {slot.day_of_week}, "
#                         f"Start: {slot.time_slot.start_time}, End: {slot.time_slot.end_time}, "
#                         f"Teacher: {slot.teacher_assignment.teacher.full_name}, "
#                         f"Subject: {slot.teacher_assignment.subject.name}, "
#                         f"Room: {slot.room.room_name}"
#                     )
#                     slots_data.append({
#                         "day_of_week": slot.day_of_week,
#                         "start_time": slot.time_slot.start_time.strftime("%H:%M"),
#                         "end_time": slot.time_slot.end_time.strftime("%H:%M"),
#                         "teacher": slot.teacher_assignment.teacher.full_name,
#                         "subject": slot.teacher_assignment.subject.name,
#                         "room": slot.room.room_name,
#                     })
#
#                 all_timetables.append({
#                     "grade_section": {
#                         "id": grade_section.id,
#                         "name": str(grade_section),
#                     },
#                     "timetable_slots": slots_data,
#                 })
#             else:
#                 print(f"No timetable slots found for {grade_section}.")
#
#         # Print the final generated timetables
#         print(f"All Timetables: {all_timetables}")
#
#         # Return the JSON response
#         return JsonResponse({"timetables": all_timetables}, safe=False)
#
#     print("Invalid request method. Only GET is allowed.")
#     return JsonResponse({"error": "Invalid request method"}, status=400)


# def auto_create_timetable_slots(grade_section_id):
#     """
#     This function handles automatic creation of timetable slots for a grade section.
#     """
#     from .models import GradeSection, Subject
#
#     # Fetch the grade section
#     grade_section = get_object_or_404(GradeSection, id=grade_section_id)
#
#     # Example logic to handle subjects
#     subjects = Subject.objects.filter(grade=grade_section.grade)
#
#     for subject in subjects:
#         if subject.requires_special_room:
#             if not subject.special_room:
#                 raise ValueError(f"Subject '{subject.name}' requires a special room, but no special room is assigned.")
#             # Logic for scheduling subjects that require a special room
#             print(f"Scheduling {subject.name} in special room: {subject.special_room.room_name}")
#         else:
#             # Logic for scheduling regular subjects
#             print(f"Scheduling {subject.name} in a standard room.")
#
#     # Return success message
#     return f"Timetable slots successfully generated for Grade Section: {grade_section}."


# def auto_create_timetable_slots(grade_section_id):
#     grade_section = GradeSection.objects.get(id=grade_section_id)
#     teacher_assignments = TeacherAssignment.objects.filter(grade_section=grade_section)
#
#     if not teacher_assignments.exists():
#         return {"error": f"No teacher assignments found for {grade_section}."}
#
#     # Define days and time slots
#     days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
#     time_slots = TimeSlot.objects.all()
#     if not time_slots.exists():
#         return {"error": "No time slots available."}
#
#     created_slots = []
#
#     for day in days:
#         for time_slot, teacher_assignment in zip(time_slots, teacher_assignments):
#             subject = teacher_assignment.subject
#
#             # Determine the room for the subject
#             if subject and subject.is_special:
#                 # Use a special room for special subjects
#                 room = Room.objects.filter(related_subjects=subject).first()
#                 if not room:
#                     return {"error": f"No special room available for {subject.name}."}
#             else:
#                 # Use the GradeSection as the default room
#                 room = grade_section
#
#             # Create or get the TimetableSlot
#             timetable_slot, created = TimetableSlot.objects.get_or_create(
#                 teacher_assignment=teacher_assignment,
#                 room=room,  # Could be a Room or a GradeSection
#                 day_of_week=day,
#                 time_slot=time_slot,
#             )
#             if created:
#                 created_slots.append(timetable_slot)
#
#     return {"success": f"{len(created_slots)} timetable slots created."}


# Function to generate room name based on grade and section
def generate_room_name_from_grade_section(grade, section):
    grade_name = grade.name.strip()
    section_name = section.name.strip()
    return f"{grade_name[0].upper()}{grade.level}{section_name[0].upper()}"





#convert asignments to  list before querying

logger = logging.getLogger(__name__)

# def auto_create_timetable_slots_for_all():
#     try:
#         # Fetch all grade sections and prefetch teacher assignments and subjects
#         grade_sections = GradeSection.objects.prefetch_related(
#             Prefetch('teacher_assignments', queryset=TeacherAssignment.objects.select_related('subject', 'teacher'))
#         )
#         logger.debug(f"Grade Sections: {grade_sections}")
#
#         if not grade_sections.exists():
#             raise ValueError("No grade sections found.")
#
#         days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
#         time_slots = list(TimeSlot.objects.all())  # Convert to a list to allow shuffling
#
#         if not time_slots:
#             raise ValueError("No time slots available.")
#
#         total_deleted_slots = 0
#         created_slots = []
#
#         with transaction.atomic():
#             for grade_section in grade_sections:
#                 logger.debug(f"Processing GradeSection: {grade_section}")
#                 teacher_assignments = list(grade_section.teacher_assignments.all())
#                 if not teacher_assignments:
#                     logger.warning(f"No teacher assignments found for {grade_section}. Skipping...")
#                     continue
#
#                 # Clear existing timetable slots for this grade section
#                 deleted_count, _ = TimetableSlot.objects.filter(
#                     teacher_assignment__in=teacher_assignments
#                 ).delete()
#                 logger.debug(f"Deleted {deleted_count} existing slots for {grade_section}.")
#                 total_deleted_slots += deleted_count
#
#                 # Generate room name for the grade section
#                 grade = grade_section.grade
#                 section = grade_section.section
#                 room_name = generate_room_name_from_grade_section(grade, section)
#                 logger.debug(f"Generated room name: {room_name}")
#
#                 # Get or create the room for this grade section
#                 default_room, room_created = Room.objects.get_or_create(
#                     room_name=room_name, defaults={"is_special": False}
#                 )
#                 logger.debug(f"Room created: {room_created} - Room details: {default_room}")
#
#                 random.shuffle(teacher_assignments)
#                 random.shuffle(time_slots)
#
#                 for day in days:
#                     logger.debug(f"Processing day: {day}")
#                     for time_slot, teacher_assignment in zip(time_slots, teacher_assignments):
#                         subject = teacher_assignment.subject
#                         assigned_room = default_room
#                         if subject and subject.requires_special_room:
#                             special_room = Room.objects.filter(related_subjects=subject).first()
#                             if special_room:
#                                 assigned_room = special_room
#                                 logger.debug(f"Assigned special room: {assigned_room} for subject: {subject.name}")
#                             else:
#                                 logger.warning(f"No special room available for {subject.name}. Using default room.")
#
#                         try:
#                             timetable_slot, created = TimetableSlot.objects.get_or_create(
#                                 teacher_assignment=teacher_assignment,
#                                 room=assigned_room,
#                                 day_of_week=day,
#                                 time_slot=time_slot,
#                             )
#                             if created:
#                                 logger.debug(f"Created TimetableSlot: {timetable_slot}")
#                                 created_slots.append(timetable_slot)
#                         except IntegrityError as e:
#                             logger.error(f"Error creating timetable slot for {grade_section}: {e}")
#                             raise
#
#         return f"Timetable slots refreshed for all grade sections. {total_deleted_slots} slots deleted, {len(created_slots)} new slots created."
#     except Exception as e:
#         logger.error(f"Error generating timetable: {e}")
#         raise










def auto_create_timetable_slots_for_all():
    # Fetch all grade sections and prefetch teacher assignments and subjects
    grade_sections = GradeSection.objects.prefetch_related(
        Prefetch('teacher_assignments', queryset=TeacherAssignment.objects.select_related('subject', 'teacher'))
    )

    if not grade_sections.exists():
        raise ValueError("No grade sections found.")

    # Define days and time slots
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    time_slots = list(TimeSlot.objects.all())  # Convert to a list to allow shuffling

    if not time_slots:
        raise ValueError("No time slots available.")

    total_deleted_slots = 0
    created_slots = []

    with transaction.atomic():
        for grade_section in grade_sections:
            print(f"Processing GradeSection: {grade_section} - Teacher Assignments: {grade_section.teacher_assignments.all()}")
            teacher_assignments = list(grade_section.teacher_assignments.all())  # Convert to list for shuffling
            if not teacher_assignments:
                print(f"No teacher assignments found for {grade_section}. Skipping...")
                continue

            # Clear existing timetable slots for this grade section
            deleted_count, _ = TimetableSlot.objects.filter(
                teacher_assignment__in=teacher_assignments
            ).delete()
            print(f"Deleted {deleted_count} existing slots for {grade_section}.")
            total_deleted_slots += deleted_count

            # Generate room name for the grade section
            grade = grade_section.grade
            section = grade_section.section
            room_name = generate_room_name_from_grade_section(grade, section)
            print(f"Generated room name: {room_name}")

            # Get or create the room for this grade section
            default_room, room_created = Room.objects.get_or_create(
                room_name=room_name, defaults={"is_special": False}
            )
            print(f"Room created: {room_created} - Room details: {default_room}")

            # Shuffle the teacher assignments and time slots to randomize their distribution
            random.shuffle(teacher_assignments)
            random.shuffle(time_slots)

            # Loop through days and shuffled time slots
            for day in days:
                print(f"Processing day: {day}")
                for time_slot, teacher_assignment in zip(time_slots, teacher_assignments):
                    print(f"Processing time_slot: {time_slot} - Teacher Assignment: {teacher_assignment}")
                    subject = teacher_assignment.subject

                    # Determine if a special room is required
                    assigned_room = default_room  # Default to the grade section's room
                    if subject and subject.requires_special_room:
                        special_room = Room.objects.filter(related_subjects=subject).first()
                        if special_room:
                            assigned_room = special_room
                            print(f"Assigned special room: {assigned_room} for subject: {subject.name}")
                        else:
                            print(f"No special room available for {subject.name}. Using default room.")

                    # Create or fetch the timetable slot
                    try:
                        timetable_slot, created = TimetableSlot.objects.get_or_create(
                            teacher_assignment=teacher_assignment,
                            room=assigned_room,
                            day_of_week=day,
                            time_slot=time_slot,
                        )
                        if created:
                            print(f"Created TimetableSlot: {timetable_slot}")
                            created_slots.append(timetable_slot)
                        else:
                            print(f"TimetableSlot already exists for {teacher_assignment.teacher.get_display_name()} on {day} at {time_slot.time_range}")
                    except IntegrityError as e:
                        print(f"Error creating timetable slot for {grade_section} - Teacher Assignment: {teacher_assignment}, Room: {assigned_room}, Day: {day}, Time Slot: {time_slot} - Error: {e}")
                        # Log more detailed error for debugging
                        raise e

    return f"Timetable slots refreshed for all grade sections. {total_deleted_slots} slots deleted, {len(created_slots)} new slots created."


def generate_timetable_view(request):
    if request.method == "POST":
        try:
            # Call your timetable generation logic
            message = auto_create_timetable_slots_for_all()

            # Fetch all timetable slots with related data
            timetable_slots = TimetableSlot.objects.select_related(
                'teacher_assignment__grade_section__grade',
                'teacher_assignment__subject',
                'teacher_assignment__teacher',
                'room',
                'time_slot'
            ).all()

            # Serialize timetable slots into JSON-serializable format
            serialized_slots = []
            for slot in timetable_slots:
                serialized_slots.append({
                    "teacher_assignment": {
                        "grade_section": {
                            "grade": {"name": slot.teacher_assignment.grade_section.grade.name},
                            "section": slot.teacher_assignment.grade_section.section
                        },
                        "subject": {"name": slot.teacher_assignment.subject.name},
                        "teacher": {"display_name": slot.teacher_assignment.teacher.get_display_name()}
                    },
                    "day_of_week": slot.day_of_week,
                    "time_slot": {"time_range": slot.time_slot.time_range},
                    "room": {"room_name": slot.room.room_name}
                })

            # Return response
            return JsonResponse({
                "message": message,
                "timetable_slots": serialized_slots
            }, status=200, encoder=DjangoJSONEncoder)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=400)







def timetable_page_view(request):
    """
    Render the timetable generation page.
    """
    grade_sections = GradeSection.objects.all()
    timetables = TimetableSlot.objects.select_related('teacher_assignment', 'room', 'time_slot', 'teacher_assignment__subject')

    context = {
        'grade_sections': grade_sections,
        'timetables': timetables,
    }
    return render(request, 'Manage/generate_timetable_all.html', context)


def get_filtered_timetable(request):
    # Get all GradeSections
    grade_sections = GradeSection.objects.all()

    # Check if a grade_section_id is provided in the GET request
    grade_section_id = request.GET.get('grade_section_id')

    # If a grade_section_id is selected, fetch the timetable for that grade section
    if grade_section_id:
        grade_section = GradeSection.objects.get(id=grade_section_id)
        timetable_slots = TimetableSlot.objects.filter(
            teacher_assignment__grade_section=grade_section
        ).select_related('teacher_assignment', 'teacher_assignment__teacher', 'time_slot', 'room')

        # Organize timetable by day and time range
        timetable_by_day = defaultdict(lambda: defaultdict(list))
        for slot in timetable_slots:
            timetable_by_day[slot.day_of_week][slot.time_slot.time_range].append(slot)

        # List of days
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

        return render(request, 'Manage/class_timetable.html', {
            'grade_sections': grade_sections,
            'grade_section': grade_section,
            'timetable_by_day': timetable_by_day,
            'days': days,
        })

    return render(request, 'Manage/class_timetable.html', {'grade_sections': grade_sections})

# def generate_timetable_for_all(request):
#     if request.method == "POST":  # Button triggers POST
#         print("POST request received for timetable generation!")
#         grade_sections = GradeSection.objects.all().order_by('grade_id', 'id').distinct('grade_id')
#         all_timetables = []
#         print("Grade Sections:", grade_sections)
#
#
#         for grade_section in grade_sections:
#             teacher_assignments = TeacherAssignment.objects.filter(grade_section=grade_section)
#             if not teacher_assignments.exists():
#                 continue
#             print("Teacher Assignments:", teacher_assignments)
#
#             timetable_slots = TimetableSlot.objects.filter(
#                 teacher_assignment__in=teacher_assignments
#             ).select_related('teacher_assignment__teacher', 'teacher_assignment__subject', 'room', 'time_slot')
#
#             if timetable_slots.exists():
#                 timetable_data = [
#                     {
#                         'day_of_week': slot.day_of_week,
#                         'time_slot': {
#                             'start_time': slot.time_slot.start_time,
#                             'end_time': slot.time_slot.end_time
#                         },
#                         'teacher': slot.teacher_assignment.teacher.full_name,
#                         'subject': slot.teacher_assignment.subject.name,
#                         'room': slot.room.room_name
#                     }
#                     for slot in timetable_slots
#                 ]
#                 all_timetables.append({
#                     'grade_section': grade_section.grade,
#                     'timetable_slots': timetable_data
#                 })
#
#         return render(request, 'Manage/generate_timetable_all.html', {'all_timetables': all_timetables})
#
#     # If GET request, render the page with the button
#     return render(request, 'Manage/generate_timetable_all.html')






def fetch_timetable_by_grade_section(request, grade_section_id):
    grade_section = get_object_or_404(GradeSection, id=grade_section_id)

    timetable_slots = TimetableSlot.objects.filter(
        teacher_assignment__grade_section=grade_section
    ).select_related('teacher_assignment__teacher', 'teacher_assignment__subject', 'room', 'time_slot')

    if not timetable_slots.exists():
        return render(request, 'Manage/error.html', {'message': 'No timetable slots available for this Grade Section'})

    timetable_slots = sorted(timetable_slots, key=lambda x: (x.day_of_week, x.time_slot.start_time))

    return render(request, 'Manage/fetch_timetable.html', {
        'grade_section': grade_section,
        'timetable_slots': timetable_slots
    })




















# from datetime import timezone
#
# from django.shortcuts import render, redirect
# from django.views import View
# from rest_framework import viewsets, generics
# from rest_framework.generics import CreateAPIView
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework.decorators import action, permission_classes, api_view
# from rest_framework import status
#
# from .serializers import (
#     TeacherAssignmentSerializer,
#     CreateTeacherAssignmentSerializer,
#     SubjectSerializer,
#     GradeSectionSerializer, TimetableSerializer, EventSerializer,
# )
# from ..management.forms import TimetableForm
# from ..management.models import Subject, Timetable, Event
# from ..students.models import GradeSection
# from ..teachers.models import TeacherAssignment
#
#
# class SubjectListView(generics.ListAPIView):
#     queryset = Subject.objects.all()
#     serializer_class = SubjectSerializer
#
#
# class GradeSectionListView(generics.ListAPIView):
#     queryset = GradeSection.objects.all()
#     serializer_class = GradeSectionSerializer
#
# class TeacherAssignmentListView(generics.ListAPIView):
#     queryset = TeacherAssignment.objects.all()
#     serializer_class = TeacherAssignmentSerializer
#
#
# #teacher management
# class TeacherAssignmentView(viewsets.ModelViewSet):
#     queryset = TeacherAssignment.objects.all()
#     serializer_class = TeacherAssignmentSerializer
#
#     def create(self, request, *args, **kwargs):
#         serializer = CreateTeacherAssignmentSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     @action(detail=False, methods=['get'])
#     def available_subjects(self, request):
#         subjects = Subject.objects.all()
#         serializer = SubjectSerializer(subjects, many=True)
#         return Response(serializer.data)
#
#     @action(detail=False, methods=['get'])
#     def available_grades_sections(self, request):
#         grade_sections = GradeSection.objects.all()
#         serializer = GradeSectionSerializer(grade_sections, many=True)
#         return Response(serializer.data)
#
# # class TimetableViewSet(viewsets.ModelViewSet):
# #     queryset = Timetable.objects.all()
# #     serializer_class = TimetableSerializer
# #
# #     @action(detail=False, methods=['get'])
# #     def student_schedule(self, request):
# #         student_id = request.query_params.get('student_id')
# #         day = request.query_params.get('day')
# #         timetables = Timetable.objects.filter(grade_section__students__id=student_id, day=day)
# #         serializer = self.get_serializer(timetables, many=True)
# #         return Response(serializer.data)
#
#
# #cbv
#
# @api_view(['POST'])
# # @permission_classes([IsAuthenticated])  # Uncomment if authentication is required
# def create_timetable(request):
#     serializer = TimetableSerializer(data=request.data)
#     if serializer.is_valid():
#         timetable = serializer.save()
#         return Response({
#             "message": "Timetable created successfully",
#             "data": TimetableSerializer(timetable).data
#         }, status=status.HTTP_201_CREATED)
#     return Response({
#         "message": "Error creating timetable",
#         "errors": serializer.errors
#     }, status=status.HTTP_400_BAD_REQUEST)
#
#
# class TimetableCreateView(View):
#     def get(self, request):
#         form = TimetableForm()
#         return render(request, 'schedules/add_timetable.html', {'form': form})
#
#     def post(self, request):
#         form = TimetableForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('class-timetable')  # Redirect after successful submission
#         return render(request, 'schedules/add_timetable.html', {'form': form})
#
#
#
#
#
# # def timetable_create_page(request):
# #     return render(request, 'schedules/add_timetable.html')  # Ensure 'timetable_create.html' is in the correct templates directory
#
#
#
# class EventViewSet(viewsets.ModelViewSet):
#     queryset = Event.objects.all()
#     serializer_class = EventSerializer
#
#     @action(detail=False, methods=['get'])
#     def upcoming_events(self, request):
#         events = Event.objects.filter(date__gte=timezone.now()).order_by('date')
#         serializer = self.get_serializer(events, many=True)
#         return Response(serializer.data)
#
#
#     #timetable generations:
# from django.http import request
# from django.shortcuts import render, redirect
# from . forms import *
# from .models import *
# from django.core.mail import send_mail
# from django.conf import settings
# from django.contrib.auth.decorators import login_required
# from .render import Render
# from django.views.generic import View
#
#
# POPULATION_SIZE = 9
# NUMB_OF_ELITE_SCHEDULES = 1
# TOURNAMENT_SELECTION_SIZE = 3
# MUTATION_RATE = 0.05
#
# class Data:
#     def __init__(self):
#         self._rooms = Room.objects.all()
#         self._meetingTimes = MeetingTime.objects.all()
#         self._instructors = Instructor.objects.all()
#         self._courses = Course.objects.all()
#         self._depts = Department.objects.all()
#
#     def get_rooms(self): return self._rooms
#
#     def get_instructors(self): return self._instructors
#
#     def get_courses(self): return self._courses
#
#     def get_depts(self): return self._depts
#
#     def get_meetingTimes(self): return self._meetingTimes
#
#
# class Schedule:
#     def __init__(self):
#         self._data = data
#         self._classes = []
#         self._numberOfConflicts = 0
#         self._fitness = -1
#         self._classNumb = 0
#         self._isFitnessChanged = True
#
#     def get_classes(self):
#         self._isFitnessChanged = True
#         return self._classes
#
#     def get_numbOfConflicts(self): return self._numberOfConflicts
#
#     def get_fitness(self):
#         if self._isFitnessChanged:
#             self._fitness = self.calculate_fitness()
#             self._isFitnessChanged = False
#         return self._fitness
#
#     def initialize(self):
#         sections = Section.objects.all()
#         for section in sections:
#             dept = section.department
#             n = section.num_class_in_week
#             if n <= len(MeetingTime.objects.all()):
#                 courses = dept.courses.all()
#                 for course in courses:
#                     for i in range(n // len(courses)):
#                         crs_inst = course.instructors.all()
#                         newClass = Class(self._classNumb, dept, section.section_id, course)
#                         self._classNumb += 1
#                         newClass.set_meetingTime(data.get_meetingTimes()[rnd.randrange(0, len(MeetingTime.objects.all()))])
#                         newClass.set_room(data.get_rooms()[rnd.randrange(0, len(data.get_rooms()))])
#                         newClass.set_instructor(crs_inst[rnd.randrange(0, len(crs_inst))])
#                         self._classes.append(newClass)
#             else:
#                 n = len(MeetingTime.objects.all())
#                 courses = dept.courses.all()
#                 for course in courses:
#                     for i in range(n // len(courses)):
#                         crs_inst = course.instructors.all()
#                         newClass = Class(self._classNumb, dept, section.section_id, course)
#                         self._classNumb += 1
#                         newClass.set_meetingTime(data.get_meetingTimes()[rnd.randrange(0, len(MeetingTime.objects.all()))])
#                         newClass.set_room(data.get_rooms()[rnd.randrange(0, len(data.get_rooms()))])
#                         newClass.set_instructor(crs_inst[rnd.randrange(0, len(crs_inst))])
#                         self._classes.append(newClass)
#
#         return self
#
#     def calculate_fitness(self):
#         self._numberOfConflicts = 0
#         classes = self.get_classes()
#         for i in range(len(classes)):
#             if classes[i].room.seating_capacity < int(classes[i].course.max_numb_students):
#                 self._numberOfConflicts += 1
#             for j in range(len(classes)):
#                 if j >= i:
#                     if (classes[i].meeting_time == classes[j].meeting_time) and \
#                             (classes[i].section_id != classes[j].section_id) and (classes[i].section == classes[j].section):
#                         if classes[i].room == classes[j].room:
#                             self._numberOfConflicts += 1
#                         if classes[i].instructor == classes[j].instructor:
#                             self._numberOfConflicts += 1
#         return 1 / (1.0 * self._numberOfConflicts + 1)
#
#
# class Population:
#     def __init__(self, size):
#         self._size = size
#         self._data = data
#         self._schedules = [Schedule().initialize() for i in range(size)]
#
#     def get_schedules(self):
#         return self._schedules
#
#
# class GeneticAlgorithm:
#     def evolve(self, population):
#         return self._mutate_population(self._crossover_population(population))
#
#     def _crossover_population(self, pop):
#         crossover_pop = Population(0)
#         for i in range(NUMB_OF_ELITE_SCHEDULES):
#             crossover_pop.get_schedules().append(pop.get_schedules()[i])
#         i = NUMB_OF_ELITE_SCHEDULES
#         while i < POPULATION_SIZE:
#             schedule1 = self._select_tournament_population(pop).get_schedules()[0]
#             schedule2 = self._select_tournament_population(pop).get_schedules()[0]
#             crossover_pop.get_schedules().append(self._crossover_schedule(schedule1, schedule2))
#             i += 1
#         return crossover_pop
#
#     def _mutate_population(self, population):
#         for i in range(NUMB_OF_ELITE_SCHEDULES, POPULATION_SIZE):
#             self._mutate_schedule(population.get_schedules()[i])
#         return population
#
#     def _crossover_schedule(self, schedule1, schedule2):
#         crossoverSchedule = Schedule().initialize()
#         for i in range(0, len(crossoverSchedule.get_classes())):
#             if rnd.random() > 0.5:
#                 crossoverSchedule.get_classes()[i] = schedule1.get_classes()[i]
#             else:
#                 crossoverSchedule.get_classes()[i] = schedule2.get_classes()[i]
#         return crossoverSchedule
#
#     def _mutate_schedule(self, mutateSchedule):
#         schedule = Schedule().initialize()
#         for i in range(len(mutateSchedule.get_classes())):
#             if MUTATION_RATE > rnd.random():
#                 mutateSchedule.get_classes()[i] = schedule.get_classes()[i]
#         return mutateSchedule
#
#     def _select_tournament_population(self, pop):
#         tournament_pop = Population(0)
#         i = 0
#         while i < TOURNAMENT_SELECTION_SIZE:
#             tournament_pop.get_schedules().append(pop.get_schedules()[rnd.randrange(0, POPULATION_SIZE)])
#             i += 1
#         tournament_pop.get_schedules().sort(key=lambda x: x.get_fitness(), reverse=True)
#         return tournament_pop
#
#
# class Class:
#     def __init__(self, id, dept, section, course):
#         self.section_id = id
#         self.department = dept
#         self.course = course
#         self.instructor = None
#         self.meeting_time = None
#         self.room = None
#         self.section = section
#
#     def get_id(self): return self.section_id
#
#     def get_dept(self): return self.department
#
#     def get_course(self): return self.course
#
#     def get_instructor(self): return self.instructor
#
#     def get_meetingTime(self): return self.meeting_time
#
#     def get_room(self): return self.room
#
#     def set_instructor(self, instructor): self.instructor = instructor
#
#     def set_meetingTime(self, meetingTime): self.meeting_time = meetingTime
#
#     def set_room(self, room): self.room = room
#
#
# data = Data()
#
#
# def context_manager(schedule):
#     classes = schedule.get_classes()
#     context = []
#     cls = {}
#     for i in range(len(classes)):
#         cls["section"] = classes[i].section_id
#         cls['dept'] = classes[i].department.dept_name
#         cls['course'] = f'{classes[i].course.course_name} ({classes[i].course.course_number}, ' \
#                         f'{classes[i].course.max_numb_students}'
#         cls['room'] = f'{classes[i].room.r_number} ({classes[i].room.seating_capacity})'
#         cls['instructor'] = f'{classes[i].instructor.name} ({classes[i].instructor.uid})'
#         cls['meeting_time'] = [classes[i].meeting_time.pid, classes[i].meeting_time.day, classes[i].meeting_time.time]
#         context.append(cls)
#     return context
#
#
# def timetable(request):
#     schedule = []
#     population = Population(POPULATION_SIZE)
#     generation_num = 0
#     population.get_schedules().sort(key=lambda x: x.get_fitness(), reverse=True)
#     geneticAlgorithm = GeneticAlgorithm()
#     while population.get_schedules()[0].get_fitness() != 1.0:
#         generation_num += 1
#         print('\n> Generation #' + str(generation_num))
#         population = geneticAlgorithm.evolve(population)
#         population.get_schedules().sort(key=lambda x: x.get_fitness(), reverse=True)
#         schedule = population.get_schedules()[0].get_classes()
#
#     return render(request, 'schedules/gentimetable.html', {'schedule': schedule, 'sections': Section.objects.all(),
#                                               'times': MeetingTime.objects.all()})
#
# ############################################################################
#
#
# def index(request):
#     return render(request, 'index.html', {})
#
#
# def about(request):
#     return render(request, 'aboutus.html', {})
#
#
# def help(request):
#     return render(request, 'help.html', {})
#
#
# def terms(request):
#     return render(request, 'terms.html', {})
#
#
# def contact(request):
#     if request.method == 'POST':
#         message = request.POST['message']
#
#         send_mail('TTGS Contact',
#                   message,
#                   settings.EMAIL_HOST_USER,
#                   ['codevoid12@gmail.com'],
#                   fail_silently=False)
#     return render(request, 'schedules/contact.html', {})
#
# #################################################################################
#
# @login_required
# def admindash(request):
#     return render(request, 'schedules/admindashboard.html', {})
#
# #################################################################################
#
# @login_required
# def addCourses(request):
#     form = CourseForm(request.POST or None)
#     if request.method == 'POST':
#         if form.is_valid():
#             form.save()
#             return redirect('addCourses')
#         else:
#             print('Invalid')
#     context = {
#         'form': form
#     }
#     return render(request, 'schedules/addCourses.html', context)
#
# @login_required
# def course_list_view(request):
#     context = {
#         'courses': Course.objects.all()
#     }
#     return render(request, 'schedules/courseslist.html', context)
#
# @login_required
# def delete_course(request, pk):
#     crs = Course.objects.filter(pk=pk)
#     if request.method == 'POST':
#         crs.delete()
#         return redirect('editcourse')
#
# #################################################################################
#
# @login_required
# def addInstructor(request):
#     form = InstructorForm(request.POST or None)
#     if request.method == 'POST':
#         if form.is_valid():
#             form.save()
#             return redirect('addInstructors')
#     context = {
#         'form': form
#     }
#     return render(request, 'schedules/addInstructors.html', context)
#
# @login_required
# def inst_list_view(request):
#     context = {
#         'instructors': Instructor.objects.all()
#     }
#     return render(request, 'schedules/inslist.html', context)
#
# @login_required
# def delete_instructor(request, pk):
#     inst = Instructor.objects.filter(pk=pk)
#     if request.method == 'POST':
#         inst.delete()
#         return redirect('editinstructor')
#
# #################################################################################
#
# @login_required
# def addRooms(request):
#     form = RoomForm(request.POST or None)
#     if request.method == 'POST':
#         if form.is_valid():
#             form.save()
#             return redirect('addRooms')
#     context = {
#         'form': form
#     }
#     return render(request, 'schedules/addRooms.html', context)
#
# @login_required
# def room_list(request):
#     context = {
#         'rooms': Room.objects.all()
#     }
#     return render(request, 'schedules/roomslist.html', context)
#
# @login_required
# def delete_room(request, pk):
#     rm = Room.objects.filter(pk=pk)
#     if request.method == 'POST':
#         rm.delete()
#         return redirect('editrooms')
#
# #################################################################################
#
# @login_required
# def addTimings(request):
#     form = MeetingTimeForm(request.POST or None)
#     if request.method == 'POST':
#         if form.is_valid():
#             form.save()
#             return redirect('addTimings')
#         else:
#             print('Invalid')
#     context = {
#         'form': form
#     }
#     return render(request, 'schedules/addTimings.html', context)
#
# @login_required
# def meeting_list_view(request):
#     context = {
#         'meeting_times': MeetingTime.objects.all()
#     }
#     return render(request, 'schedules/mtlist.html', context)
#
# @login_required
# def delete_meeting_time(request, pk):
#     mt = MeetingTime.objects.filter(pk=pk)
#     if request.method == 'POST':
#         mt.delete()
#         return redirect('editmeetingtime')
#
# #################################################################################
#
# @login_required
# def addDepts(request):
#     form = DepartmentForm(request.POST or None)
#     if request.method == 'POST':
#         if form.is_valid():
#             form.save()
#             return redirect('addDepts')
#     context = {
#         'form': form
#     }
#     return render(request, 'schedules/addDepts.html', context)
#
# @login_required
# def department_list(request):
#     context = {
#         'departments': Department.objects.all()
#     }
#     return render(request, 'schedules/deptlist.html', context)
#
# @login_required
# def delete_department(request, pk):
#     dept = Department.objects.filter(pk=pk)
#     if request.method == 'POST':
#         dept.delete()
#         return redirect('editdepartment')
#
# #################################################################################
#
# @login_required
# def addSections(request):
#     form = SectionForm(request.POST or None)
#     if request.method == 'POST':
#         if form.is_valid():
#             form.save()
#             return redirect('addSections')
#     context = {
#         'form': form
#     }
#     return render(request, 'schedules/addSections.html', context)
#
# @login_required
# def section_list(request):
#     context = {
#         'sections': Section.objects.all()
#     }
#     return render(request, 'schedules/seclist.html', context)
#
# @login_required
# def delete_section(request, pk):
#     sec = Section.objects.filter(pk=pk)
#     if request.method == 'POST':
#         sec.delete()
#         return redirect('editsection')
#
# #################################################################################
#
# @login_required
# def generate(request):
#     return render(request, 'schedules/generate.html', {})
#
# #################################################################################
#
# class Pdf(View):
#     def get(self, request):
#         params = {
#             'request': request
#         }
#         return Render.render('gentimetable.html', params)
#
#
#
#
#
