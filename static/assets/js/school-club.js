document.addEventListener('DOMContentLoaded', function () {
    // Debounce for search input
    let debounceTimeout;
    const debounceDelay = 500; // Delay of 500ms before making the request

    // Ensure the #studentSearch input exists before adding the event listener
    const studentSearchInput = document.getElementById('studentSearch');
    if (studentSearchInput) {
        studentSearchInput.addEventListener('input', function () {
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(searchStudents, debounceDelay);
        });
    }

    // Function to search students
    function searchStudents() {
        const query = studentSearchInput.value.trim();

        if (query.length > 1) {
            console.log('Searching for:', query);

            fetch(`/management/search_student/?q=${encodeURIComponent(query)}`)
                .then(response => {
                    console.log('Response status:', response.status);
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Data received:', data);

                    if (data.error) {
                        alert('Error: ' + data.error);
                        return;
                    }

                    const studentList = document.getElementById('studentList');
                    if (studentList) {
                        studentList.innerHTML = ''; // Clear existing list

                        if (data.students && data.students.length > 0) {
                            data.students.forEach(student => {
                                const listItem = document.createElement('li');
                                listItem.classList.add('list-group-item');
                                listItem.dataset.id = student.id;
                                listItem.dataset.name = student.name;
                                listItem.dataset.admissionNo = student.admission_no;
                                listItem.dataset.grade = student.grade || '-';
                                listItem.textContent = `${student.name} - ${student.admission_no}`;
                                studentList.appendChild(listItem);
                            });
                        } else {
                            studentList.innerHTML = '<li class="list-group-item">No students found</li>';
                        }
                    } else {
                        console.error('Element #studentList not found');
                    }
                })
                .catch(error => {
                    console.error('Error fetching student data:', error);
                    alert('Failed to fetch student data. Check console for details.');
                });
        }
    }

    // Ensure the #studentList exists and add a click event listener
    const studentList = document.getElementById('studentList');
    if (studentList) {
        // Inside the studentList click event listener:
        studentList.addEventListener('click', function (event) {
            const target = event.target;
            if (target.tagName === 'LI') {
                const studentName = target.dataset.name;
                const studentId = target.dataset.id;
                const admissionNo = target.dataset.admissionNo;
                const grade = target.dataset.grade;

                studentSearchInput.value = studentName;
                studentList.innerHTML = '';

                // Update hidden input
                document.getElementById('selectedStudentId').value = studentId;

                // Update Confirmation Modal's elements
                const confirmationNameElement = document.getElementById('confirmationName');
                const confirmationAdmissionElement = document.getElementById('confirmationAdmissionNo');
                const confirmationGradeElement = document.getElementById('confirmationGrade');

                if (!confirmationNameElement || !confirmationAdmissionElement || !confirmationGradeElement) {
                    console.error("Confirmation modal elements missing!");
                    return;
                }

                confirmationNameElement.textContent = studentName;
                confirmationAdmissionElement.textContent = admissionNo;
                confirmationGradeElement.textContent = grade;

                // Enable Confirm Button
                const confirmAddButton = document.getElementById('confirmAddButton');
                if (confirmAddButton) confirmAddButton.disabled = false;

                // Show Confirmation Modal
                const confirmationModal = new bootstrap.Modal(document.getElementById('studentConfirmationModal'));
                confirmationModal.show();
            }
        });
    }


    // Handle the form submission for adding the member (from the confirmation modal)
    const confirmAddMemberBtn = document.getElementById('confirmAddMemberBtn');
    if (confirmAddMemberBtn) {
        confirmAddMemberBtn.addEventListener('click', function () {
            const studentId = document.querySelector('input[name="student_id"]')?.value;
            const clubId = document.getElementById('clubId')?.value;

            // Simple validation
            if (!studentId || !clubId) {
                alert('Please select a student and a club');
                return;
            }

            fetch(`/management/add_member/${clubId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('input[name="csrfmiddlewaretoken"]').value
                },
                body: JSON.stringify({student_id: studentId})
            })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        alert('Student added successfully!');
                        // Update the member list dynamically (optional)
                        updateMemberTable(clubId);

                        // Close the modal after successful addition
                        $('#studentConfirmationModal').modal('hide');

                        // Reset the form and close the add member modal
                        document.getElementById('addMemberForm').reset();
                        $('#addMemberModal').modal('hide');
                    } else {
                        alert('Error: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error adding member:', error);
                    alert('There was an error adding the student to the club.');
                });
        });
    }

    // Function to update the member list
    function updateMemberTable(clubId) {
        fetch(`/management/get_club_members/${clubId}/`)
            .then(response => response.json())
            .then(data => {
                const tableBody = document.querySelector('.table tbody');
                if (tableBody) {
                    tableBody.innerHTML = '';  // Clear old table rows

                    data.members.forEach(member => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${member.admission_number}</td>
                            <td>${member.name}</td>
                            <td>${member.grade}</td>
                            <td>${member.role}</td>
                            <td>
                                <a href="#" class="btn btn-danger" onclick="removeMember(${member.id}, ${clubId})">Remove</a>
                            </td>
                        `;
                        tableBody.appendChild(row);
                    });
                }
            })
            .catch(error => console.error('Error updating member list:', error));
    }
});
