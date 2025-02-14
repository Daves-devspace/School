document.addEventListener("DOMContentLoaded", function () {
    const detailsDiv = document.getElementById("appointment-details");
    const replyBtn = document.getElementById("send-reply");
    const replyInput = document.getElementById("reply-message");
    const notificationCount = document.getElementById("notification-count");
    const markAllReadBtn = document.getElementById("mark-all-read");
    const notificationBadge = document.getElementById("notification-badge");

    function getCSRFToken() {
        const csrfTokenField = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (csrfTokenField) return csrfTokenField.value;

        const cookieToken = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
        return cookieToken ? cookieToken.split('=')[1] : "";
    }

    function updateNotificationCount() {
        // fetch(`/schedules/notifications/count/`)
        fetch(window.location.origin + "/notifications/count/")

            .then(response => response.json())
            .then(data => {
                if (data && typeof data.notification_count !== "undefined") {
                    if (notificationCount) notificationCount.textContent = data.notification_count;
                    if (notificationBadge) {
                        notificationBadge.style.display = data.total_unread > 0 ? "inline-block" : "none";
                        notificationBadge.innerText = data.total_unread;
                    }
                }
            })
            .catch(error => console.error("Error fetching notifications:", error));
    }

    function fetchAppointmentDetails(appointmentId, element) {
        if (!appointmentId) return;

        fetch(`/get-appointment/${appointmentId}/`)
            .then(response => response.json())
            .then(data => {
                if (detailsDiv && data) {
                    detailsDiv.innerHTML = `
                        <strong>Guardian:</strong> ${data.guardian || 'N/A'} <br>
                        <strong>Child:</strong> ${data.child || 'N/A'} <br>
                        <strong>Date:</strong> ${data.date || 'N/A'} at ${data.time || 'N/A'} <br>
                        <strong>Phone:</strong> ${data.phone || 'N/A'} <br>
                        <strong>Email:</strong> ${data.email || 'N/A'} <br>
                        <hr>
                        <p><strong>Message:</strong> ${data.message || 'No message provided'}</p>
                    `;
                    if (replyBtn) {
                        replyBtn.setAttribute("data-id", appointmentId);
                        replyBtn.disabled = false;
                    }
                    if (element) {
                        element.classList.remove("fw-bold", "bg-light");
                        element.classList.add("text-muted");
                    }
                }
            })
            .catch(error => console.error("Error fetching appointment:", error));
    }

    function sendReply(appointmentId, message) {
        if (!message.trim()) {
            alert("Reply cannot be empty!");
            return;
        }

        fetch(`/reply-appointment/${appointmentId}/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
            body: JSON.stringify({message})
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === "success") {
                    alert("Reply sent!");
                    if (replyInput) replyInput.value = "";
                } else {
                    alert(data.message || "Failed to send reply.");
                }
            })
            .catch(error => {
                console.error("Error sending reply:", error);
                alert("An error occurred.");
            });
    }

    function markAllNotificationsRead() {
        fetch(`/schedules/notifications/mark-all-read/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            }
        })
            .then(response => response.json())
            .then(data => {
                console.log("Response:", data);
                if (data.status === "success") {
                    console.log("All notifications marked as read!");
                    // Instead of setting count directly, re-fetch notification count
                    updateNotificationCount();
                    alert("All notifications marked as read.");
                }
            })
            .catch(error => console.error("Error marking notifications as read:", error));
    }

    // Use event delegation for dynamically loaded elements
    document.body.addEventListener("click", function (event) {
        const appointmentElement = event.target.closest(".appointment-item");
        if (appointmentElement) {
            const appointmentId = appointmentElement.getAttribute("data-id");
            if (appointmentId) fetchAppointmentDetails(appointmentId, appointmentElement);
        }
    });

    if (replyBtn) {
        replyBtn.addEventListener("click", function () {
            const appointmentId = this.getAttribute("data-id");
            if (appointmentId) sendReply(appointmentId, replyInput.value);
        });
    }

    if (markAllReadBtn) {
        markAllReadBtn.addEventListener("click", markAllNotificationsRead);
    }

    // Update unread notifications count every 30 seconds
    setInterval(updateNotificationCount, 30000);
});
