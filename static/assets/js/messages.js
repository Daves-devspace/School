document.addEventListener('DOMContentLoaded', function () {
    // Element References
    const elements = {
        templateVarsSection: document.getElementById('templateVarsSection'),
        templateVars: document.getElementById('templateVars'),
        toggleVarsButton: document.getElementById('toggleVars'),
        messageTextarea: document.querySelector('textarea[name="message"]'),
        smsTypeInput: document.getElementById('smsTypeInput'),
        typeCards: document.querySelectorAll('.sms-type-card'),
        termSelect: document.querySelector('select[name="term"]'),
        examTypeSelect: document.querySelector('select[name="exam_type"]'),
        gradeSectionsSelect: document.querySelector('select[name="grade_sections"]'),
        charCount: document.getElementById('charCount'),
        form: document.getElementById('smsForm'),
        messagePreview: document.getElementById('messagePreview'),
        recipientCount: document.getElementById('recipientCount'),
        confirmBtn: document.getElementById('confirmSend'),
        modal: document.getElementById('confirmationModal'),
    };

    // State Management
    let currentType = elements.smsTypeInput?.value || 'bulk';
    const paramsSections = {
        results: document.querySelector('.params-results'),
        class: document.querySelector('.params-class'),
    };

    // Initialization
    initialize();

    function initialize() {
        setupEventListeners();
        initTooltips();
        updateUI(currentType);
        updateLivePreview();
        updateCharacterCount();
    }

    function setupEventListeners() {
        elements.templateVarsSection?.addEventListener('click', handleTemplateVarClick);
        elements.toggleVarsButton?.addEventListener('click', toggleVariablesSection);

        elements.typeCards.forEach(card => {
            card.style.cursor = 'pointer';
            card.setAttribute('role', 'button');
            card.setAttribute('tabindex', '0');
            card.addEventListener('click', handleTypeSelection);
            card.addEventListener('keydown', e => {
                if (e.key === 'Enter' || e.key === ' ') handleTypeSelection(e);
            });
        });

        [elements.gradeSectionsSelect, elements.termSelect, elements.examTypeSelect].forEach(select => {
            select?.addEventListener('change', handleParameterChange);
        });

        elements.messageTextarea?.addEventListener('input', debounce(handleMessageInput, 300));
        elements.form?.addEventListener('submit', handleFormSubmit);
        elements.confirmBtn?.addEventListener('click', handleConfirmation);
    }

    function updateUI(type) {
        updateTemplateUI(type);
        updateFieldValidation(type);
        updateRecipientCount(type);
        updateTemplateVars(type);
    }

    function updateTemplateUI(type) {
        if (!elements.messageTextarea || !elements.templateVarsSection) return;

        elements.templateVarsSection.style.display = type === 'results' ? 'block' : 'none';
        elements.messageTextarea.placeholder = type === 'results'
            ? "Example: {parent_name}, {student_name} scored {total_marks} in {term}"
            : "Write your message here...";
    }

    function updateFieldValidation(type) {
        const isResults = type === 'results';

        [elements.termSelect, elements.examTypeSelect].forEach(el => {
            if (el) {
                el.disabled = !isResults;
                el.required = isResults;
                if (!isResults) el.value = ''; // Reset values if not required
            }
        });

        if (paramsSections.results) {
            paramsSections.results.style.display = isResults ? 'block' : 'none';
        }
    }

    async function updateRecipientCount(type) {
        if (!elements.recipientCount || !elements.form) return;

        elements.recipientCount.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Calculating...`;

        try {
            const params = new URLSearchParams();
            if (type === 'results') {
                params.append('term', elements.termSelect?.value || '');
                params.append('exam_type', elements.examTypeSelect?.value || '');
            } else if (type === 'class') {
                params.append('grade_sections',
                    [...elements.gradeSectionsSelect?.selectedOptions].map(opt => opt.value).join(',')
                );
            }

            const response = await fetch(`${elements.form.dataset.url}?type=${type}&${params.toString()}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const data = await response.json();
            elements.recipientCount.textContent = data.error
                ? "Error calculating recipients"
                : `${data.count} recipients`;
        } catch (error) {
            console.error('Recipient count error:', error);
            elements.recipientCount.textContent = "Error loading count";
        }
    }

    function handleMessageInput() {
        updateCharacterCount();
        updateLivePreview();
    }

    function updateCharacterCount() {
        if (!elements.messageTextarea || !elements.charCount) return;
        const length = elements.messageTextarea.value.length;
        elements.charCount.textContent = length;
        elements.charCount.classList.toggle('text-danger', length > 160);
    }

    function updateLivePreview() {
        if (!elements.messagePreview || !elements.messageTextarea) return;

        const sampleValues = {
            "{parent_name}": "John",
            "{student_name}": "Alice",
            // "{total_marks}": "95",
            "{avg_marks}": "85",
            "{grade}": "A",
            "{term}": "Term 1",
            "{exam_type}": "Mid-Term",
            "{class_name}": "Grade 5A",
            "{teacher_name}": "Ms. Smith"
        };

        elements.messagePreview.textContent = Object.entries(sampleValues).reduce(
            (text, [key, val]) => text.replace(new RegExp(key, 'g'), val),
            elements.messageTextarea.value
        );
    }

    function debounce(func, delay) {
        let timer;
        return function (...args) {
            clearTimeout(timer);
            timer = setTimeout(() => func.apply(this, args), delay);
        };
    }

    function showErrorAlert(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.innerHTML = `${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
        document.querySelector('.container.py-5')?.prepend(alert);
    }
});






















// document.addEventListener('DOMContentLoaded', function () {
//     // Element References
//     const elements = {
//         templateVarsSection: document.getElementById('templateVarsSection'),
//         templateVars: document.getElementById('templateVars'),
//         toggleVarsButton: document.getElementById('toggleVars'),
//         messageTextarea: document.querySelector('textarea[name="message"]'),
//         smsTypeInput: document.getElementById('smsTypeInput'),
//         typeCards: document.querySelectorAll('.sms-type-card'),
//         termSelect: document.querySelector('select[name="term"]'),
//         examTypeSelect: document.querySelector('select[name="exam_type"]'),
//         gradeSectionsSelect: document.querySelector('select[name="grade_sections"]'),
//         charCount: document.getElementById('charCount'),
//         form: document.getElementById('smsForm'),
//         messagePreview: document.getElementById('messagePreview'),
//         recipientCount: document.getElementById('recipientCount'),
//         confirmBtn: document.getElementById('confirmSend'),
//         modal: document.getElementById('confirmationModal'),
//     };
//
//     // State Management
//     let currentType = elements.smsTypeInput?.value || 'bulk';
//     const paramsSections = {
//         results: document.querySelector('.params-results'),
//         class: document.querySelector('.params-class'),
//     };
//
//     // Initialization
//     initialize();
//
//     function initialize() {
//         setupEventListeners();
//         initTooltips();
//         updateUI(currentType);
//         updateLivePreview();
//         updateCharacterCount();
//     }
//
//     function setupEventListeners() {
//         if (elements.templateVarsSection) {
//             elements.templateVarsSection.addEventListener('click', handleTemplateVarClick);
//         }
//
//         if (elements.toggleVarsButton) {
//             elements.toggleVarsButton.addEventListener('click', toggleVariablesSection);
//         }
//
//         elements.typeCards.forEach(card => {
//             card.style.cursor = 'pointer';
//             card.setAttribute('role', 'button');
//             card.setAttribute('tabindex', '0');
//             card.addEventListener('click', handleTypeSelection);
//             card.addEventListener('keydown', e => {
//                 if (e.key === 'Enter') handleTypeSelection(e);
//             });
//         });
//
//         [elements.gradeSectionsSelect, elements.termSelect, elements.examTypeSelect].forEach(select => {
//             select?.addEventListener('change', handleParameterChange);
//         });
//
//         elements.messageTextarea?.addEventListener('input', handleMessageInput);
//         elements.form?.addEventListener('submit', handleFormSubmit);
//         elements.confirmBtn?.addEventListener('click', handleConfirmation);
//     }
//
//     function updateUI(type) {
//         updateTemplateUI(type);
//         updateFieldValidation(type);
//         updateRecipientCount(type);
//         updateTemplateVars(type);
//     }
//
//     function updateTemplateUI(type) {
//         if (!elements.messageTextarea || !elements.templateVarsSection) return;
//
//         elements.templateVarsSection.style.display = type === 'results' ? 'block' : 'none';
//         elements.messageTextarea.placeholder = type === 'results'
//             ? "Example: {parent_name}, {student_name} scored {total_marks} in {term}"
//             : "Write your message here...";
//     }
//
//     function updateFieldValidation(type) {
//         const isResults = type === 'results';
//
//         [elements.termSelect, elements.examTypeSelect].forEach(el => {
//             if (el) {
//                 el.disabled = !isResults;
//                 el.required = isResults;
//                 if (!isResults) el.value = ''; // Reset values if not required
//             }
//         });
//
//         if (paramsSections.results) {
//             paramsSections.results.style.display = isResults ? 'block' : 'none';
//         }
//     }
//
//     async function updateRecipientCount(type) {
//         if (!elements.recipientCount || !elements.form) return;
//
//         elements.recipientCount.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Calculating...`;
//
//         try {
//             const params = new URLSearchParams();
//             if (type === 'results') {
//                 params.append('term', elements.termSelect?.value || '');
//                 params.append('exam_type', elements.examTypeSelect?.value || '');
//             } else if (type === 'class') {
//                 params.append('grade_sections',
//                     [...elements.gradeSectionsSelect?.selectedOptions].map(opt => opt.value).join(',')
//                 );
//             }
//
//             const response = await fetch(`${elements.form.dataset.url}?type=${type}&${params.toString()}`);
//             if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
//
//             const data = await response.json();
//             elements.recipientCount.textContent = data.error
//                 ? "Error calculating recipients"
//                 : `${data.count} recipients`;
//         } catch (error) {
//             console.error('Recipient count error:', error);
//             elements.recipientCount.textContent = "Error loading count";
//         }
//     }
//
//     function handleTypeSelection(e) {
//         const card = e.currentTarget;
//         elements.typeCards.forEach(c => c.classList.remove('active'));
//         card.classList.add('active');
//         currentType = card.dataset.type;
//         elements.smsTypeInput.value = currentType;
//         updateUI(currentType);
//     }
//
//     function handleFormSubmit(e) {
//         e.preventDefault();
//
//         document.querySelectorAll('.alert-dismissible').forEach(alert => alert.remove());
//
//         if (!elements.messageTextarea) return;
//
//         if (elements.messageTextarea.value.length > 160) {
//             showErrorAlert('Message exceeds 160 character limit!');
//             return;
//         }
//
//         if (elements.modal) {
//             document.getElementById('modalRecipientCount').textContent =
//                 elements.recipientCount.textContent.match(/\d+/)?.[0] || '0';
//             new bootstrap.Modal(elements.modal).show();
//         }
//     }
//
//     function handleConfirmation() {
//         elements.form.submit();
//     }
//
//     function updateCharacterCount() {
//         if (!elements.messageTextarea || !elements.charCount) return;
//         elements.charCount.textContent = elements.messageTextarea.value.length;
//         elements.charCount.classList.toggle('text-danger', elements.messageTextarea.value.length > 160);
//     }
//
//     function handleMessageInput() {
//         updateCharacterCount();
//         updateLivePreview();
//     }
//
//     function updateLivePreview() {
//         if (!elements.messagePreview || !elements.messageTextarea) return;
//
//         const sampleValues = {
//             "{parent_name}": "John",
//             "{student_name}": "Alice",
//             "{total_marks}": "95",
//             "{avg_marks}": "85",
//             "{grade}": "A",
//             "{term}": "Term 1",
//             "{exam_type}": "Mid-Term",
//             "{class_name}": "Grade 5A",
//             "{teacher_name}": "Ms. Smith"
//         };
//
//         elements.messagePreview.textContent = Object.entries(sampleValues).reduce(
//             (text, [key, val]) => text.replace(new RegExp(key, 'g'), val),
//             elements.messageTextarea.value
//         );
//     }
//
//     function toggleVariablesSection() {
//         if (elements.templateVarsSection) {
//             elements.templateVarsSection.style.display =
//                 elements.templateVarsSection.style.display === 'none' ? 'block' : 'none';
//         }
//     }
//
//     function showErrorAlert(message) {
//         const alert = document.createElement('div');
//         alert.className = 'alert alert-danger alert-dismissible fade show';
//         alert.innerHTML = `${message}
//             <button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
//         document.querySelector('.container.py-5')?.prepend(alert);
//     }
// });
