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
        confirmBtn: document.getElementById('confirmSend')
    };

    // State Management
    let currentType = elements.smsTypeInput?.value || 'bulk';
    const paramsSections = {
        results: document.querySelector('.params-results'),
        class: document.querySelector('.params-class')
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
        // Template Variables
        if (elements.templateVarsSection) {
            elements.templateVarsSection.addEventListener('click', handleTemplateVarClick);
        }

        // Toggle Variables
        if (elements.toggleVarsButton) {
            elements.toggleVarsButton.addEventListener('click', toggleVariablesSection);
        }

        // SMS Type Cards
        elements.typeCards.forEach(card => {
            card.style.cursor = 'pointer';
            card.setAttribute('role', 'button');
            card.setAttribute('tabindex', '0');
            card.addEventListener('click', handleTypeSelection);
            card.addEventListener('keydown', e => {
                if (e.key === 'Enter') handleTypeSelection(e);
            });
        });

        // Form Elements
        [elements.gradeSectionsSelect, elements.termSelect, elements.examTypeSelect].forEach(select => {
            select?.addEventListener('change', handleParameterChange);
        });

        elements.messageTextarea?.addEventListener('input', handleMessageInput);

        // Form Submission
        elements.form?.addEventListener('submit', handleFormSubmit);
        elements.confirmBtn?.addEventListener('click', handleConfirmation);
    }

    // Core Functions
    function updateUI(type) {
        updateTemplateUI(type);
        updateFieldValidation(type);
        updateRecipientCount(type);
        updateTemplateVars(type);
    }

    function updateTemplateUI(type) {
        if (!elements.messageTextarea) return;

        elements.templateVarsSection.style.display = type === 'results' ? 'block' : 'none';
        elements.messageTextarea.placeholder = type === 'results'
            ? "Example: {parent_name}, {student_name} scored {total_marks} in {term}"
            : "Write your message here...";
    }

    function updateFieldValidation(type) {
        const resultsContainer = paramsSections.results;
        const isResults = type === 'results';

        [elements.termSelect, elements.examTypeSelect].forEach(el => {
            if (el) {
                el.disabled = !isResults;
                el.required = isResults;
            }
        });

        if (resultsContainer) {
            resultsContainer.style.display = isResults ? 'block' : 'none';
            if (!isResults) {
                elements.termSelect.value = '';
                elements.examTypeSelect.value = '';
            }
        }
    }

    async function updateRecipientCount(type) {
        if (!elements.recipientCount) return;

        try {
            elements.recipientCount.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Calculating...`;

            const params = new URLSearchParams();
            if (type === 'results') {
                params.append('term', elements.termSelect?.value || '');
                params.append('exam_type', elements.examTypeSelect?.value || '');
            } else if (type === 'class') {
                params.append('grade_sections',
                    [...elements.gradeSectionsSelect.selectedOptions].map(opt => opt.value).join(','));
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

    // Event Handlers
    function handleTypeSelection(e) {
        const card = e.currentTarget;
        elements.typeCards.forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        currentType = card.dataset.type;
        elements.smsTypeInput.value = currentType;
        updateUI(currentType);
    }

    function handleParameterChange() {
        if ((currentType === 'class' && this === elements.gradeSectionsSelect) ||
            (currentType === 'results' && [elements.termSelect, elements.examTypeSelect].includes(this))) {
            updateRecipientCount(currentType);
        }
    }

    function handleFormSubmit(e) {
        e.preventDefault();

        // Clear existing alerts
        document.querySelectorAll('.alert-dismissible').forEach(alert => alert.remove());

        // Validate inputs
        let isValid = true;

        if (currentType === 'results' && (!elements.termSelect.value || !elements.examTypeSelect.value)) {
            isValid = false;
            showErrorAlert('Please select both term and exam type');
        }

        if (currentType === 'class' && elements.gradeSectionsSelect.selectedOptions.length === 0) {
            isValid = false;
            showErrorAlert('Please select at least one class section');
        }

        if (elements.messageTextarea.value.length > 160) {
            isValid = false;
            showErrorAlert('Message exceeds 160 character limit!');
        }

        if (isValid) {
            document.getElementById('modalRecipientCount').textContent =
                elements.recipientCount.textContent.match(/\d+/)?.[0] || '0';
            new bootstrap.Modal(document.getElementById('confirmationModal')).show();
        }
    }

    function handleConfirmation() {
        elements.form.submit();
    }

    // Helper Functions
    function initTooltips() {
        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
            new bootstrap.Tooltip(el);
        });
    }

    function updateTemplateVars(type) {
        const variables = {
            results: "Available variables: {parent_name}, {student_name}, {total_marks}, {term}, {exam_type}",
            class: "Available variables: {class_name}, {teacher_name}"
        };
        elements.templateVars.textContent = variables[type] || '';
    }

    function insertAtCursor(value) {
        const field = elements.messageTextarea;
        const start = field.selectionStart;
        const end = field.selectionEnd;
        field.value = field.value.slice(0, start) + value + field.value.slice(end);
        field.selectionStart = field.selectionEnd = start + value.length;
        field.focus();
        updateLivePreview();
    }

    function updateLivePreview() {
        if (!elements.messagePreview || !elements.messageTextarea) return;

        const sampleValues = {
            "{parent_name}": "John",
            "{student_name}": "Alice",
            "{total_marks}": "95",
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

    function updateCharacterCount() {
        if (!elements.messageTextarea) return;
        elements.charCount.textContent = elements.messageTextarea.value.length;
        elements.charCount.classList.toggle('text-danger', elements.messageTextarea.value.length > 160);
    }

    function handleMessageInput() {
        updateCharacterCount();
        updateLivePreview();
    }

    function toggleVariablesSection() {
        elements.templateVarsSection.style.display =
            elements.templateVarsSection.style.display === 'none' ? 'block' : 'none';
    }

    function handleTemplateVarClick(e) {
        const btn = e.target.closest('.template-var');
        if (btn) {
            e.preventDefault();
            insertAtCursor(btn.dataset.var);
            elements.templateVarsSection.style.display = 'none';
        }
    }

    function showErrorAlert(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.container.py-5').prepend(alert);
    }
});