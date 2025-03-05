$(document).ready(function () {
    // Function to get CSRF token dynamically
    function getCSRFToken() {
        return $('input[name="csrfmiddlewaretoken"]').val();
    }

    // Set CSRF token in AJAX headers globally
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
                xhr.setRequestHeader("X-CSRFToken", getCSRFToken());
            }
        }
    });

    // Ensure URL is correctly set from Django template
    let addSectionUrl = typeof addSectionUrl !== "undefined" ? addSectionUrl.trim() : "";

    function handleFormSubmission(formId, selectId, modalId, url, successMessage) {
        $(formId).submit(function (e) {
            e.preventDefault();

            let form = $(this);

            console.log(`Submitting to: ${url}`); // Debugging step

            $.ajax({
                type: "POST",
                url: url,
                data: form.serialize(),
                dataType: "json",
                success: function (response) {
                    if (response.success) {
                        if (selectId) {
                            $(selectId).append(`<option value="${response.id}">${response.name}</option>`);
                        }
                        form[0].reset();
                        $(modalId).modal("hide");  // Close modal
                    } else {
                        alert(response.error || `Failed to ${successMessage}.`);
                    }
                },
                error: function (xhr) {
                    alert(xhr.responseJSON?.error || "Something went wrong!");
                }
            });
        });
    }

    // Attach AJAX form handlers with correct URLs
    handleFormSubmission("#addGradeForm", "#gradeSelect", "#addGradeModal", addGradeUrl, "add grade");
    handleFormSubmission("#addSectionForm", "#sectionSelect", "#addSectionModal", addSectionUrl, "add section");

    // Special handling for class form (since it updates a table instead of a dropdown)
    $("#addClassForm").submit(function (e) {
        e.preventDefault();

        let form = $(this);
        let url = form.attr("action").trim(); // Ensure we get the correct URL

        console.log(`Submitting class form to: ${url}`); // Debugging

        $.ajax({
            type: "POST",
            url: url,
            data: form.serialize(),
            dataType: "json",
            success: function (response) {
                if (response.success) {
                    $("#classList").append(`
                        <tr>
                            <td>${response.grade}</td>
                            <td>${response.section || "No Section"}</td>
                            <td>${response.teacher || "No Teacher"}</td>
                        </tr>
                    `);
                    form[0].reset();
                    $("#addClassModal").modal("hide");  // Close modal
                } else {
                    alert(response.error || "Failed to add class.");
                }
            },
            error: function (xhr) {
                alert(xhr.responseJSON?.error || "Something went wrong!");
            }
        });
    });
});
