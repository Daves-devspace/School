Primary School Management System
Overview
The Primary School Management System is a web-based application built using Django and JavaScript, designed to handle administrative tasks in a primary school. This system streamlines and automates several processes such as student and teacher management, class scheduling, fee collection, report generation, attendance tracking, and more. By integrating different modules into a single platform, the system enables school management to operate more efficiently and helps in better decision-making through real-time data insights.

Features
1. Student Management
Add/Update/Delete Students: Manage student profiles, including personal details, grades, and performance.
View Student Records: Display comprehensive records for each student, including attendance, grades, and activities.
Grade Management: Assign and update grades, view subject-wise progress reports, and track performance over time.
2. Teacher Management
Add/Update/Delete Teachers: Manage teacher profiles with details such as name, subject taught, and contact information.
Assign Subjects to Teachers: Allocate subjects to teachers and manage their schedules.
Attendance Tracking: Track teachers' attendance and generate reports.
3. Fee Management
Fee Records: Track and manage fee payments for students.
Generate Reports: View payment status, outstanding balances, and total revenue.
Multiple Payment Methods: Handle payments via different methods such as cash, bank transfers, and mobile payments.
4. Attendance Management
Track Student Attendance: Record daily attendance for students and generate reports.
Teacher Attendance: Keep track of teachers' attendance for better schedule management.
Reports: Generate reports to analyze attendance trends, absences, and more.
5. Reports & Insights
Financial Reports: View monthly, quarterly, or yearly revenue data, and analyze fee payments.
Student Performance Reports: Generate performance summaries based on grades, attendance, and behavior.
Teacher Reports: Generate reports related to teacher attendance, performance, and class activities.
6. User Management
Role-Based Access: Administrators can create accounts with different roles such as teachers, staff, and students, with varying levels of access.
Secure Authentication: All users must log in with secure authentication, ensuring data privacy.
7. Dashboard
Real-Time Data: View quick statistics and summaries of key metrics like total students, teachers, revenue, and attendance.
Interactive Charts: Visualize data with interactive charts for easy interpretation.

TIMETABLE GENERATION

Documentation
Core Logic
The timetable generator creates schedules that prioritize:

Subject Preferences (core subjects, required sessions/week, special rooms)

Teacher Availability (no double-booking)

Room Constraints (special vs. default rooms)

Time Slot Optimization (morning/afternoon preferences)

Key Preference Adherence
Core Subjects First

Assigned to optimal time slots (mornings by default)

Limited to 2 core subjects/day to prevent overload

Special Room Allocation

Lab/experimental subjects get priority for special rooms

Ensures no overlapping bookings in special rooms

Session Frequency

Subjects with higher sessions_per_week get priority in scheduling

Distributed evenly across days

Teacher Constraints

No overlapping assignments for the same teacher

Balanced workload across days

Generation Process
Preparation

Delete existing timetable slots for the grade section

Prefetch:

Teacher assignments

Subject preferences

Rooms (default + special)

Time slots (ordered chronologically)

Priority Queue Setup

Subjects are ranked by:

python
Copy
Priority = (Core? 100 : 0) + (Special Room? 50 : 0) + (Sessions/Week * 10)  
Higher priority subjects scheduled first.

Core Subject Scheduling

For each core subject:

Assign to non-consecutive days

Use morning time slots first

Check teacher/room availability

Elective Subject Handling

Fill remaining slots randomly

Ensure no conflicts with existing assignments

Conflict Checks

Teacher Conflicts: Track teacher-day-time assignments

Room Conflicts: Track room-day-time usage

Back-to-Back Prevention: Avoid consecutive core subjects

Output

Bulk-create valid timetable slots

Return generation stats (created/deleted slots)

Example Schedule
Day	Time	Subject	Teacher	Room
Monday	09:00-10:00	Math	Mr. Smith	G10A
Monday	10:00-11:00	Physics	Dr. Johnson	Lab 201
Tuesday	08:00-09:00	English	Ms. Davis	G10A
Features
Automated Room Creation: Generates default rooms if missing (e.g., G10A).

Real-Time Updates: Reflects changes to preferences immediately.

Error Handling:

Rollback on failure

Logs conflicts/missing data

Constraints:

No duplicate slots

All fields (room, teacher, time) required

This system ensures efficient, conflict-free timetables while respecting pedagogical priorities and resource constraints.




Username Format Rules:
- Allows letters, numbers, and @/./+/-/_//
- Maximum 150 characters
- Example patterns: TCH/001/24, ADM/045/22