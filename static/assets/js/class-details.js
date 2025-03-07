document.addEventListener("DOMContentLoaded", function () {
    const firstGradeSectionId = "{{ grade_sections.0.id }}"; // First available grade_section ID

    if (firstGradeSectionId) {
        document.querySelector(".edit-btn").setAttribute("data-bs-target", `#editModal${firstGradeSectionId}`);
        document.querySelector(".split-btn").setAttribute("data-bs-target", `#splitClassModal${firstGradeSectionId}`);
        document.querySelector(".merge-btn").setAttribute("data-bs-target", `#mergeClassModal${firstGradeSectionId}`);
    }
});


// // Attach event listener to confirm button
// document.getElementById("confirmMergeBtn").onclick = function () {
//     document.getElementById(`mergeForm${gradeSectionId}`).submit();
// };
//
// // Show the confirmation modal
// new bootstrap.Modal(document.getElementById('confirmMergeModal')).show();
// }
