document.addEventListener("DOMContentLoaded", function () {
    const gradeSectionDropdown = document.getElementById("grade-section");
    const timetableTable = document.getElementById("timetable").getElementsByTagName("tbody")[0];

    const API_URL = "http://localhost/management/api/timetable/";

    // Fetch API data
    async function fetchTimetable(selectedGradeSection = null) {
        try {
            const response = await fetch(
                `${API_URL}${selectedGradeSection ? `?grade_section=${selectedGradeSection}` : ""}`
            );
            const jsonResponse = await response.json();

            console.log("API Response:", jsonResponse); // Debugging

            // Validate response
            if (jsonResponse.status === "success" && jsonResponse.data) {
                const data = jsonResponse.data;

                // Populate grade sections dropdown
                populateGradeSections(data.grade_sections);

                // Update timetable with sorted lessons
                updateTimetable(data);
            } else {
                console.error("Error:", jsonResponse.message || "Unexpected response format.");
                displayErrorMessage(jsonResponse.message || "Failed to fetch timetable data.");
            }
        } catch (error) {
            console.error("Error fetching timetable data:", error);
            displayErrorMessage("An error occurred while fetching data. Please try again later.");
        }
    }

    // Populate grade sections dropdown
    function populateGradeSections(gradeSections) {
        if (!gradeSections || !Array.isArray(gradeSections)) {
            console.error("Invalid grade sections data.");
            return;
        }

        // Clear existing options
        gradeSectionDropdown.innerHTML = "";

        // Add a default "Select" option
        const defaultOption = document.createElement("option");
        defaultOption.value = "";
        defaultOption.textContent = "Select a grade section";
        gradeSectionDropdown.appendChild(defaultOption);

        // Add grade section options
        gradeSections.forEach(section => {
            const option = document.createElement("option");
            option.value = section.id;
            option.textContent = `${section.grade__name} - ${section.section__name}`;
            gradeSectionDropdown.appendChild(option);
        });
    }

    // Update timetable based on API data
    function updateTimetable(data) {
        // Clear existing timetable
        timetableTable.innerHTML = "";

        if (data.selected_grade_section && data.timetable_data && Object.keys(data.timetable_data).length) {
            // Sort unique times in ascending order (morning to evening)
            const sortedTimes = data.unique_times.sort((a, b) => {
                const timeTo24Hr = time => {
                    const [hours, minutes] = time.match(/\d{1,2}:\d{2}/)[0].split(":");
                    const period = time.includes("PM") && !time.startsWith("12") ? 12 : 0;
                    return parseInt(hours) % 12 + period + minutes / 60;
                };
                return timeTo24Hr(a) - timeTo24Hr(b);
            });

            // Create rows based on sorted times
            sortedTimes.forEach(time => {
                const row = document.createElement("tr");

                // Add time column
                const timeCell = document.createElement("td");
                timeCell.textContent = time;
                row.appendChild(timeCell);

                // Add data for each day of the week
                data.days_of_week.forEach(day => {
                    const dayCell = document.createElement("td");
                    const lessons = data.timetable_data[day]?.filter(lesson => lesson.time === time) || [];

                    if (lessons.length) {
                        dayCell.textContent = `${lessons[0].subject} (${lessons[0].teacher})`;
                    } else {
                        dayCell.textContent = "N/L"; // No lesson at this time
                    }

                    row.appendChild(dayCell);
                });

                timetableTable.appendChild(row);
            });
        } else {
            displayErrorMessage("No timetable available for the selected grade section.");
        }
    }

    // Display error message in the timetable
    function displayErrorMessage(message) {
        timetableTable.innerHTML = "";
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 8;
        cell.textContent = message;
        row.appendChild(cell);
        timetableTable.appendChild(row);
    }

    // Event listener for grade section selection
    gradeSectionDropdown.addEventListener("change", function () {
        const selectedGradeSection = this.value;
        if (selectedGradeSection) {
            fetchTimetable(selectedGradeSection);
        } else {
            // Clear timetable if no grade section is selected
            displayErrorMessage("Please select a grade section to view the timetable.");
        }
    });

    // Initial fetch to populate dropdown
    fetchTimetable();
});
const socket = new WebSocket('ws://localhost:8000/ws/timetable/');

socket.onopen = function (e) {
    console.log('WebSocket connection established');

    // Request data for a specific grade_section
    socket.send(JSON.stringify({grade_section: 1}));
};

socket.onmessage = function (e) {
    const data = JSON.parse(e.data);
    console.log('Received data:', data);

    if (data.error) {
        alert(data.error);
    } else {
        // Process and display timetable data
        console.log('Timetable:', data.data);
    }
};

socket.onclose = function (e) {
    console.log('WebSocket connection closed');
};

socket.onerror = function (e) {
    console.error('WebSocket error', e);
};
