import json
from collections import defaultdict, deque
from heapq import heappop, heappush

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.db import IntegrityError, transaction
from django.db.models import Prefetch
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .forms import SubjectForm, RoomForm, SubjectPreferenceForm
from .models import TeacherAssignment, TimetableSlot, TimeSlot, Room, Subject, SubjectPreference, Notification
import random
import logging

from .serializers import TeacherAssignmentSerializer
from .utils import generate_room_name_from_grade_section
from ..students.models import GradeSection

logger = logging.getLogger(__name__)


@login_required
def add_subject(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)

        if form.is_valid():
            subject_name = form.cleaned_data[
                'name'].strip()  # Don't normalize the name here if you want to preserve original case
            grades_selected = form.cleaned_data['grade']  # Get the grades selected in the form

            # Check if the subject already exists (case insensitive)
            existing_subject = Subject.objects.filter(name__iexact=subject_name).first()

            if existing_subject:
                # If the subject exists, check for new grades to add
                existing_grades = existing_subject.grade.all()
                new_grades = grades_selected.exclude(id__in=existing_grades.values_list('id', flat=True))

                if new_grades.exists():
                    # Add the new grades to the existing subject
                    existing_subject.grade.add(*new_grades)
                    messages.success(
                        request,
                        f"Updated '{existing_subject.name}' to include new grades: {', '.join(grade.name for grade in new_grades)}."
                    )
                else:
                    messages.info(
                        request,
                        f"No new grades were added. '{existing_subject.name}' already has the selected grades."
                    )

                return redirect('subjects_list')

            else:
                # Create a new subject if it doesn't exist
                new_subject = form.save()

                messages.success(request, f"Subject '{new_subject.name}' added successfully!")

                return redirect('subjects_list')

    else:
        form = SubjectForm()

    return render(request, 'performance/add_subject.html', {'form': form})



@login_required
def list_subjects(request):
    subjects = Subject.objects.all()  # or use any other filter you need
    return render(request, 'performance/subjects.html', {'subjects': subjects})



# Edit Subject
def edit_subject(request, id):
    subject = get_object_or_404(Subject, pk=id)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            return redirect('subjects_list')
    else:
        form = SubjectForm(instance=subject)
    return render(request, 'performance/add_subject.html', {'form': form})

def add_room_and_list(request, room_id=None):
    rooms = Room.objects.prefetch_related("related_subjects").select_related("grade_section").all()

    room = None
    edit_mode = False

    if room_id:
        room = get_object_or_404(Room, id=room_id)
        edit_mode = True

    form = RoomForm(request.POST or None, instance=room)

    if request.method == 'POST' and form.is_valid():
        # Check if the room already exists for the same GradeSection
        room_name = form.cleaned_data.get('room_name')
        grade_section = form.cleaned_data.get('grade_section')

        if grade_section and Room.objects.filter(grade_section=grade_section).exclude(id=room_id).exists():
            messages.error(request, f"A room for Grade Section '{grade_section}' already exists.")
        else:
            saved_room = form.save()
            message = f"Room '{saved_room.room_name}' updated successfully!" if edit_mode else f"Room '{saved_room.room_name}' added successfully!"
            messages.success(request, message)
            return redirect('add_edit_room_and_list')

    return render(request, 'schedules/add_rooms.html', {
        'form': form,
        'rooms': rooms,
        'edit_mode': edit_mode,
        'room_id': room_id
    })


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
            # Generate room based on grade section
            room_name = generate_room_name_from_grade_section(grade_section.grade, grade_section.section)
            room, created = Room.objects.get_or_create(
                room_name=room_name, defaults={"is_special": False}
            )

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


# Function to generate room name based on grade and section


class TimetableScheduler:
    def __init__(self, grade_section, days, time_slots, subject_preferences):
        self.grade_section = grade_section
        self.days = days
        self.time_slots = sorted(time_slots, key=lambda ts: ts.start_time)
        self.subject_preferences = subject_preferences
        self.scheduled_slots = defaultdict(set)
        self.teacher_schedule = defaultdict(set)
        self.room_schedule = defaultdict(set)
        self.priority_queue = []
        self.special_room_registry = defaultdict(dict)
        self.core_subject_limit = 2  # Max core subjects per day

        # Initialize data structures
        self._prepare_teacher_assignments()
        self._prepare_subject_queue()
        self._prepare_special_rooms()

    def _prepare_teacher_assignments(self):
        """Create a mapping of subjects to teacher assignments"""
        self.teacher_assignments = {
            ta.subject: ta for ta in self.grade_section.teacher_assignments.all()
        }

    def _prepare_subject_queue(self):
        """Create a priority queue based on subject preferences with stable sorting"""
        for pref in self.subject_preferences.filter(grade_section=self.grade_section):
            priority = self._calculate_priority(pref)
            # Use subject ID as secondary key for stable sorting
            heappush(self.priority_queue, (-priority, pref.subject.id, pref))

    def _calculate_priority(self, preference):
        """Calculate scheduling priority based on multiple factors"""
        priority = 0
        if preference.is_core_subject:
            priority += 100
        if preference.subject.requires_special_room:
            priority += 50
        priority += preference.sessions_per_week * 10
        return priority

    def _prepare_special_rooms(self):
        """Cache special room availability"""
        self.special_rooms = Room.objects.filter(
            subject_special_rooms__isnull=False  # Use your existing related_name
        ).distinct().prefetch_related('timetable_slots')

        for room in self.special_rooms:
            self.special_room_registry[room] = {
                (slot.day_of_week, slot.time_slot_id)
                for slot in room.timetable_slots.all()
            }

    def generate_schedule(self):
        """Main scheduling method"""
        scheduled_slots = []

        # Process core subjects first
        while self.priority_queue:
            priority, subject_id, pref = heappop(self.priority_queue)
            scheduled_slots += self._schedule_subject(pref)

        # Handle remaining subjects
        scheduled_slots += self._schedule_remaining_subjects()

        return scheduled_slots

    def _schedule_subject(self, preference):
        """Schedule a single subject with conflict checking"""
        subject = preference.subject
        teacher_assignment = self.teacher_assignments.get(subject)
        if not teacher_assignment:
            return []

        scheduled = []
        required_sessions = preference.sessions_per_week
        days = deque(self.days)
        random.shuffle(days)  # Distribute across days

        while required_sessions > 0 and days:
            day = days.popleft()
            core_count = self._count_core_subjects(day)

            if core_count >= self.core_subject_limit:
                continue

            time_slots = self._get_optimal_time_slots(subject, day)
            for time_slot in time_slots:
                if required_sessions <= 0:
                    break

                room = self._select_room(subject, day, time_slot)
                if self._is_available(teacher_assignment, day, time_slot, room):
                    scheduled.append(self._create_slot(teacher_assignment, day, time_slot, room))
                    required_sessions -= 1
                    self._update_schedules(day, time_slot, teacher_assignment, room)

        return scheduled

    def _count_core_subjects(self, day):
        """Count core subjects scheduled on a given day"""
        return sum(1 for pref in self.subject_preferences
                   if pref.is_core_subject and day in self.scheduled_slots[pref.subject])

    def _get_optimal_time_slots(self, subject, day):
        """Get time slots ordered by suitability for the subject"""
        if subject.requires_special_room:
            # Afternoon slots first for lab subjects
            return sorted(self.time_slots,
                          key=lambda ts: (not ts.is_afternoon, ts.start_time))
        # Morning slots first for non-lab subjects
        return sorted(self.time_slots,
                      key=lambda ts: (not ts.is_morning, ts.start_time))

    def _select_room(self, subject, day, time_slot):
        """Ensure room assignment with multiple fallbacks"""
        try:
            if subject.requires_special_room:
                special_room = self._find_available_special_room(day, time_slot)
                if special_room:
                    return special_room
                logger.warning(f"No special room available for {subject}, using default")

            # Fallback to grade section's default room
            room = self.grade_section.rooms.filter(is_special=False).first()
            if not room:
                room = self._create_emergency_room()
            return room
        except Exception as e:
            logger.error(f"Room selection failed: {str(e)}")
            raise

    def _create_emergency_room(self):
        """Create emergency room if all else fails"""
        room_name = generate_room_name_from_grade_section(
            self.grade_section.grade,
            self.grade_section.section
        )
        return Room.objects.create(
            room_name=room_name,
            is_special=False,
            grade_section=self.grade_section
        )

    def _find_available_special_room(self, day, time_slot):
        """Find available special room using registry"""
        for room, bookings in self.special_room_registry.items():
            if (day, time_slot.id) not in bookings:
                bookings.add((day, time_slot.id))
                return room
        return None

    def _is_available(self, teacher_assignment, day, time_slot, room):
        """Check availability using in-memory tracking"""
        teacher_key = (teacher_assignment.teacher.id, day, time_slot.id)
        room_key = (room.id, day, time_slot.id) if room else None

        return not (
                teacher_key in self.teacher_schedule or
                (room_key and room_key in self.room_schedule) or
                self._has_conflicting_core_subjects(day, time_slot)
        )

    def _has_conflicting_core_subjects(self, day, time_slot):
        """Prevent back-to-back core subjects using ordered slots"""
        try:
            index = self.time_slots.index(time_slot)
            prev_slot = self.time_slots[index - 1] if index > 0 else None
            next_slot = self.time_slots[index + 1] if index < len(self.time_slots) - 1 else None
        except ValueError:
            return False

        return any(
            self._is_core_subject(day, ts)
            for ts in [prev_slot, next_slot]
            if ts
        )

    def _is_core_subject(self, day, time_slot):
        """Check if time slot contains a core subject"""
        return any(
            pref.is_core_subject
            for pref in self.subject_preferences
            if (day, time_slot.id) in self.scheduled_slots[pref.subject]
        )

    def _create_slot(self, teacher_assignment, day, time_slot, room):
        """Create timetable slot and update tracking"""
        return {
            'teacher_assignment': teacher_assignment,
            'day_of_week': day,
            'time_slot': time_slot,
            'room': room
        }

    def _update_schedules(self, day, time_slot, teacher_assignment, room):
        """Update in-memory schedules"""
        self.teacher_schedule[(teacher_assignment.teacher.id, day, time_slot.id)] = True
        if room:
            self.room_schedule[(room.id, day, time_slot.id)] = True

    def _schedule_remaining_subjects(self):
        """Handle subjects without preferences"""
        scheduled = []
        remaining_subjects = set(self.teacher_assignments.keys()) - {
            pref.subject for pref in self.subject_preferences
        }

        for subject in remaining_subjects:
            teacher_assignment = self.teacher_assignments[subject]
            day = random.choice(self.days)
            time_slot = random.choice(self.time_slots)
            room = self._select_room(subject, day, time_slot)

            if self._is_available(teacher_assignment, day, time_slot, room):
                scheduled.append(self._create_slot(teacher_assignment, day, time_slot, room))
                self._update_schedules(day, time_slot, teacher_assignment, room)

        return scheduled


def auto_create_timetable_slots_for_all():
    try:
        with transaction.atomic():
            # Consolidated prefetch query
            grade_sections = GradeSection.objects.prefetch_related(
                Prefetch('teacher_assignments',
                         queryset=TeacherAssignment.objects
                         .select_related('teacher', 'subject')
                         .prefetch_related(
                             Prefetch('timetable_slots',
                                      queryset=TimetableSlot.objects.select_related('time_slot', 'room')
                                      )
                         )
                         ),
                Prefetch('rooms',
                         queryset=Room.objects.filter(is_special=False)
                         .select_related('grade_section')
                         )
            ).all()

            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            time_slots = TimeSlot.objects.order_by('start_time')
            subject_preferences = SubjectPreference.objects.select_related('subject', 'grade_section')

            total_created = 0
            total_deleted = 0

            for grade_section in grade_sections:
                # Validate room existence before scheduling
                if not grade_section.rooms.exists():
                    raise ValueError(f"No rooms found for {grade_section}")
                # Delete existing slots using the relationship
                deleted_count, _ = TimetableSlot.objects.filter(
                    teacher_assignment__grade_section=grade_section
                ).delete()
                total_deleted += deleted_count

                # Initialize scheduler
                scheduler = TimetableScheduler(
                    grade_section=grade_section,
                    days=days,
                    time_slots=time_slots,
                    subject_preferences=subject_preferences
                )

                # Generate and create slots
                new_slots = [
                    TimetableSlot(
                        teacher_assignment=slot['teacher_assignment'],
                        day_of_week=slot['day_of_week'],
                        time_slot=slot['time_slot'],
                        room=slot['room']
                    ) for slot in scheduler.generate_schedule()
                ]
                # Validate slots before creation
                for slot in new_slots:
                    if not slot.room:
                        raise ValueError(f"Missing room for slot: {slot}")

                TimetableSlot.objects.bulk_create(new_slots)
                total_created += len(new_slots)

            return {
                'status': 'success',
                'deleted': total_deleted,
                'created': total_created
            }

    except Exception as e:
        logger.error(f"Timetable generation failed: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'message': f"Generation failed: {str(e)}"
        }


@require_http_methods(["POST"])
def generate_timetable_view(request):
    """Handle AJAX timetable generation requests only"""
    try:
        with transaction.atomic():
            # Generate timetable
            generation_result = auto_create_timetable_slots_for_all()

            if generation_result['status'] != 'success':
                return JsonResponse({
                    'status': 'error',
                    'message': generation_result.get('message', 'Generation failed')
                }, status=400)

            # Serialize timetable data
            timetable_slots = TimetableSlot.objects.select_related(
                'teacher_assignment__grade_section__grade',
                'teacher_assignment__subject',
                'teacher_assignment__teacher',
                'room',
                'time_slot'
            ).filter(teacher_assignment__isnull=False)

            return JsonResponse({
                'status': 'success',
                'message': f"Generated {generation_result['created']} slots",
                'timetable': [serialize_slot(slot) for slot in timetable_slots]
            })

    except Exception as e:
        logger.error(f"Timetable generation failed: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@require_http_methods(["GET", "POST"])
def timetable_page_view(request):
    """Handle page rendering and form submissions"""
    if request.method == "POST":
        form = SubjectPreferenceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Subject preferences updated successfully!")
            return redirect("timetable_page")
    else:
        form = SubjectPreferenceForm()

    context = {
        # Update prefetch to use "rooms"
        'grade_sections': GradeSection.objects.prefetch_related(
            Prefetch('rooms', queryset=Room.objects.filter(is_special=False)),  # Changed from room_set
            'teacher_assignments__subject',
            'teacher_assignments__teacher'
        ).all(),
        'timetables': TimetableSlot.objects.select_related(
            'teacher_assignment__grade_section',
            'teacher_assignment__subject',
            'teacher_assignment__teacher',
            'room',
            'time_slot'
        ).filter(teacher_assignment__isnull=False),
        'form':form,
    }
    return render(request, 'Manage/generate_timetable_all.html', context)


def serialize_slot(slot):
    return {
        'grade': slot.teacher_assignment.grade_section.grade.name,
        'section': slot.teacher_assignment.grade_section.section.name,
        'subject': slot.teacher_assignment.subject.name,
        'teacher': slot.teacher_assignment.teacher.get_title(),
        'day': slot.day_of_week,
        'time': slot.time_slot.time_range,
        'room': slot.room.room_name
    }


def handle_ajax_generation(request):
    """Process AJAX timetable generation requests"""
    try:
        generation_result = auto_create_timetable_slots_for_all()

        if generation_result['status'] != 'success':
            return JsonResponse({
                'status': 'error',
                'message': generation_result.get('message', 'Generation failed')
            }, status=500)

        # Serialize updated timetable
        timetable_slots = TimetableSlot.objects.select_related(
            'teacher_assignment__grade_section__grade',
            'teacher_assignment__subject',
            'teacher_assignment__teacher',
            'room',
            'time_slot'
        ).filter(teacher_assignment__isnull=False)

        return JsonResponse({
            'status': 'success',
            'message': f"Generated {generation_result['created']} slots, deleted {generation_result['deleted']}",
            'timetable': [serialize_slot(slot) for slot in timetable_slots]
        })

    except Exception as e:
        logger.error(f"Timetable generation failed: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


def get_filtered_timetable(request):
    grade_sections = GradeSection.objects.all()

    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # Parse JSON data
            grade_section_id = data.get('grade_section_id')

            if not grade_section_id:
                return JsonResponse({'error': 'Missing grade_section_id'}, status=400)

            grade_section = GradeSection.objects.get(id=grade_section_id)
            timetable_slots = TimetableSlot.objects.filter(
                teacher_assignment__grade_section=grade_section
            ).select_related('teacher_assignment', 'teacher_assignment__teacher', 'teacher_assignment__subject',
                             'time_slot', 'room')

            timetable_by_day = defaultdict(lambda: defaultdict(list))

            # Iterate over timetable slots to print subjects and other details
            for slot in timetable_slots:
                subject_name = slot.teacher_assignment.subject.name
                timetable_by_day[slot.day_of_week][slot.time_slot.time_range].append({
                    'time_range': slot.time_slot.time_range,
                    'teacher': slot.teacher_assignment.teacher.get_title(),
                    'room': slot.room.room_name,
                    'subject': subject_name
                })

            # Print the data before returning
            print("Timetable Data:", timetable_by_day)

            return JsonResponse({
                'status': 'success',
                'timetable_by_day': dict(timetable_by_day),  # Timetable data for rendering
                'grade_section_name': str(grade_section)  # Add the grade section name as before
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except GradeSection.DoesNotExist:
            return JsonResponse({'error': 'Grade section not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    # If GET request, render the template with grade sections
    return render(request, 'Manage/class_timetable.html', {'grade_sections': grade_sections})


# def get_filtered_timetable(request):
#     grade_sections = GradeSection.objects.all()
#
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)  # Parse JSON data
#             grade_section_id = data.get('grade_section_id')
#
#             if not grade_section_id:
#                 return JsonResponse({'error': 'Missing grade_section_id'}, status=400)
#
#             grade_section = GradeSection.objects.get(id=grade_section_id)
#             timetable_slots = TimetableSlot.objects.filter(
#                 teacher_assignment__grade_section=grade_section
#             ).select_related('teacher_assignment', 'teacher_assignment__teacher', 'teacher_assignment__subject', 'time_slot', 'room')
#
#             timetable_by_day = defaultdict(lambda: defaultdict(list))
#             for slot in timetable_slots:
#                 timetable_by_day[slot.day_of_week][slot.time_slot.time_range].append({
#                     'time_range': slot.time_slot.time_range,
#                     'teacher': slot.teacher_assignment.teacher.get_title(),
#                     'room': slot.room.room_name,
#                     'subject': slot.teacher_assignment.subject.name  # Add the subject here
#                 })
#
#             return JsonResponse({
#                 'status': 'success',
#                 'timetable_by_day': dict(timetable_by_day),
#                 'grade_section_name': str(grade_section)  # Add the grade section name as before
#             })
#
#         except json.JSONDecodeError:
#             return JsonResponse({'error': 'Invalid JSON format'}, status=400)
#         except GradeSection.DoesNotExist:
#             return JsonResponse({'error': 'Grade section not found'}, status=404)
#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=500)
#
#     return render(request, 'Manage/class_timetable.html', {'grade_sections': grade_sections})

#shows timetable by gradesection by days
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




#Rechedule
class RescheduleSlot(View):
    def get(self, request, slot_id):
        teacher = getattr(request.user, 'teacher', None)
        if not teacher:
            messages.error(request, "You are not authorized to reschedule.")
            return redirect('teacher_dashboard')

        slot = get_object_or_404(TimetableSlot, pk=slot_id, teacher_assignment__teacher=teacher)
        available_slots = TimeSlot.objects.exclude(
            timetable_slots__day_of_week=slot.day_of_week
        ).order_by('start_time')

        return render(request, 'teachers/reschedule_form.html', {
            'slot': slot,
            'available_slots': available_slots,
            'rooms': Room.objects.all()
        })

    def post(self, request, slot_id):
        teacher = getattr(request.user, 'teacher', None)
        if not teacher:
            messages.error(request, "Unauthorized access.")
            return redirect('teacher_dashboard')

        slot = get_object_or_404(TimetableSlot, pk=slot_id, teacher_assignment__teacher=teacher)

        new_time_id = request.POST.get('new_time')
        new_room_id = request.POST.get('new_room')
        new_day = request.POST.get('new_day')

        # Validate inputs
        if not new_time_id or not new_room_id or not new_day:
            messages.error(request, "Please select a valid time, day, and room.")
            return redirect('teacher_dashboard')

        # Ensure valid objects exist
        new_time = get_object_or_404(TimeSlot, id=new_time_id)
        new_room = get_object_or_404(Room, id=new_room_id)

        # Check if the slot is available
        conflict = TimetableSlot.objects.filter(
            day_of_week=new_day,
            time_slot=new_time,
            room=new_room
        ).exists()

        if conflict:
            messages.error(request, "Selected slot is already booked.")
        else:
            # Create new rescheduled slot
            TimetableSlot.objects.create(
                teacher_assignment=slot.teacher_assignment,
                day_of_week=new_day,
                time_slot=new_time,
                room=new_room,
                is_rescheduled=True,
                original_slot=slot
            )

            # Mark original slot as rescheduled
            slot.is_rescheduled = True
            slot.save()

            messages.success(request, "Reschedule request submitted successfully!")

        return redirect('teacher_dashboard')




class MarkAsReadView(View):
    def post(self, request, pk):
        notification = get_object_or_404(
            Notification,
            id=pk,
            user=request.user
        )
        if not notification.read:
            notification.read = True
            notification.save()
        return JsonResponse({'status': 'success'})

class MarkAllReadView(View):
    def post(self, request):
        request.user.notifications.filter(read=False).update(read=True)
        return JsonResponse({'status': 'success'})


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


# convert asignments to  list before querying


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
