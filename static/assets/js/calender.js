document.addEventListener("DOMContentLoaded", function () {
    const calendarEl = document.getElementById("calendar");
    const eventTypeFilter = document.getElementById("event-type-filter");
    const createEventForm = document.getElementById("createEventForm");
    const editEventForm = document.getElementById("editEventForm");
    const createEventModal = new bootstrap.Modal(document.getElementById("createEventModal"));
    const editEventModal = new bootstrap.Modal(document.getElementById("editEventModal"));

    if (!calendarEl) {
        console.error("Calendar element not found.");
        return;
    }

    // Check for authentication token
    const authToken = localStorage.getItem("authToken");
    if (!authToken) {
        console.error("No auth token found. Redirecting to login.");
        alert("Session expired. Please log in again.");
        window.location.href = "/login/";
        return;
    }

    let calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: "dayGridMonth",
        events: function (fetchInfo, successCallback, failureCallback) {
            fetchEvents(successCallback, failureCallback);
        },
        editable: true,
        eventClick: handleEventClick,
    });

    calendar.render();

    // Fetch events function
    async function fetchEvents(successCallback, failureCallback) {
        try {
            const eventType = eventTypeFilter ? eventTypeFilter.value : "all";

            const response = await fetch("/management/events/?event_type=" + eventType, {
                method: "GET",
                credentials: "include",  // ✅ Include session cookie in request
                headers: {"X-Requested-With": "XMLHttpRequest"}
            });

            if (response.status === 403 || response.status === 401) {
                alert("Session expired. Redirecting to login.");
                window.location.href = "/login/";
                return;
            }

            if (!response.ok) throw new Error("Failed to fetch events.");
            const events = await response.json();
            successCallback(events);
        } catch (error) {
            console.error("Error fetching events:", error);
            alert("Error loading events. Please try again.");
            failureCallback(error);
        }
    }


    // Event type filter
    if (eventTypeFilter) {
        eventTypeFilter.addEventListener("change", () => calendar.refetchEvents());
    }

    // Create event submission
    if (createEventForm) {
        createEventForm.addEventListener("submit", async function (event) {
            event.preventDefault();
            const formData = new FormData(createEventForm);
            const eventData = Object.fromEntries(formData.entries());

            try {
                const response = await fetch("/management/create-event/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${authToken}`,
                    },
                    body: JSON.stringify(eventData),
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || "Failed to create event.");
                }

                alert("Event created successfully!");
                calendar.refetchEvents();
                createEventForm.reset();
                createEventModal.hide();
            } catch (error) {
                console.error("Error creating event:", error);
                alert(error.message);
            }
        });
    }

    // Handle event click (Edit Modal)
    function handleEventClick(info) {
        const event = info.event;
        document.getElementById("editEventId").value = event.id;
        document.getElementById("editEventName").value = event.title;
        document.getElementById("editEventDate").value = event.startStr;
        document.getElementById("editEventTime").value = event.extendedProps.time || "";
        document.getElementById("editEventDescription").value = event.extendedProps.description || "";

        editEventModal.show();
    }
});
