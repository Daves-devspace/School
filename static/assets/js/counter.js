document.addEventListener("DOMContentLoaded", function () {
    // Mark Single Notification as Read
    document.querySelectorAll(".mark-as-read").forEach(item => {
        item.addEventListener("click", function () {
            let notificationId = this.getAttribute("data-id");

            if (!notificationId) return; // Prevent errors if data-id is missing

            fetch(`/schedules/notifications/mark-read/${notificationId}/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCSRFToken(),
                    "Content-Type": "application/json",
                },
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.closest(".notification-message")?.classList.remove("unread");
                        updateNotificationCounter();
                    }
                })
                .catch(error => console.error("Error:", error));
        });
    });

    // Mark All as Read (Both in Base & Inbox)
    let markAllBase = document.getElementById("markAllRead");
    let markAllInbox = document.getElementById("mark-all-read");

    if (markAllBase) markAllBase.addEventListener("click", markAllAsRead);
    if (markAllInbox) markAllInbox.addEventListener("click", markAllAsRead);

    function markAllAsRead() {
        fetch(`/schedules/notifications/mark-all-read/`, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken(),
                "Content-Type": "application/json",
            },
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.querySelectorAll(".notification-message").forEach(item => {
                        item.classList.remove("unread");
                    });
                    updateNotificationCounter();
                }
            })
            .catch(error => console.error("Error:", error));
    }

    function updateNotificationCounter() {
        let unreadCount = document.querySelectorAll(".notification-message.unread").length;

        let counterElement = document.getElementById("notificationCounter");
        let inboxCounter = document.getElementById("notification-count");

        if (counterElement) counterElement.innerText = unreadCount > 0 ? unreadCount : "";
        if (inboxCounter) inboxCounter.innerText = unreadCount > 0 ? unreadCount : "0";
    }

    function getCSRFToken() {
        let tokenElement = document.querySelector("[name=csrfmiddlewaretoken]");
        return tokenElement ? tokenElement.value : ""; // Return empty string if token is missing
    }
});
