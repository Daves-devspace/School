!function ($) {
    "use strict";

    var CalendarApp = function () {
        this.$body = $("body")
        this.$calendar = $('#calendar'),
            this.$event = $('#calendar-events div.calendar-events'),
            this.$categoryForm = $('#add_new_event form'),
            this.$extEvents = $('#calendar-events'),
            this.$modal = $('#my_event'),
            this.$saveCategoryBtn = $('.save-category'),
            this.$calendarObj = null;
    };

    // Drag & Drop Feature
    CalendarApp.prototype.onDrop = function (eventObj, date) {
        var $this = this;
        var originalEventObject = eventObj.data('eventObject');
        var $categoryClass = eventObj.attr('data-class');
        var copiedEventObject = $.extend({}, originalEventObject);
        copiedEventObject.start = date;
        if ($categoryClass) copiedEventObject.className = [$categoryClass];

        $this.$calendar.fullCalendar('renderEvent', copiedEventObject, true);
        if ($('#drop-remove').is(':checked')) eventObj.remove();
    };

    // Event Click
    CalendarApp.prototype.onEventClick = function (calEvent, jsEvent, view) {
        var $this = this;
        var form = $("<form></form>");
        form.append("<label>Change event name</label>");
        form.append("<div class='input-group'><input class='form-control' type='text' value='" + calEvent.title + "' /><span class='input-group-append'><button type='submit' class='btn btn-success'><i class='fa fa-check'></i> Save</button></span></div>");

        $this.$modal.modal({backdrop: 'static'});
        $this.$modal.find('.delete-event').show().end()
            .find('.save-event').hide().end()
            .find('.modal-body').empty().prepend(form);

        $this.$modal.find('.delete-event').unbind('click').click(function () {
            $this.$calendarObj.fullCalendar('removeEvents', function (ev) {
                return (ev._id == calEvent._id);
            });
            $this.$modal.modal('hide');
        });

        $this.$modal.find('form').on('submit', function () {
            calEvent.title = form.find("input[type=text]").val();
            $this.$calendarObj.fullCalendar('updateEvent', calEvent);
            $this.$modal.modal('hide');
            return false;
        });
    };

    // Select Event
    CalendarApp.prototype.onSelect = function (start, end, allDay) {
        var $this = this;
        $this.$modal.modal({backdrop: 'static'});

        var form = $("<form></form>");
        form.append("<div class='event-inputs'></div>");
        form.find(".event-inputs").append(`
            <div class='form-group'>
                <label class='control-label'>Event Name</label>
                <input class='form-control' placeholder='Insert Event Name' type='text' name='title'/>
            </div>
            <div class='form-group mb-0'>
                <label class='control-label'>Category</label>
                <select class='form-control' name='category'>
                    <option value='bg-danger'>Danger</option>
                    <option value='bg-success'>Success</option>
                    <option value='bg-purple'>Purple</option>
                    <option value='bg-primary'>Primary</option>
                    <option value='bg-info'>Info</option>
                    <option value='bg-warning'>Warning</option>
                </select>
            </div>
        `);

        $this.$modal.find('.delete-event').hide().end()
            .find('.save-event').show().end()
            .find('.modal-body').empty().prepend(form);

        $this.$modal.find('.save-event').unbind('click').click(function () {
            form.submit();
        });

        $this.$modal.find('form').on('submit', function () {
            var title = form.find("input[name='title']").val();
            var categoryClass = form.find("select[name='category'] option:checked").val();

            if (title !== null && title.length !== 0) {
                $this.$calendarObj.fullCalendar('renderEvent', {
                    title: title,
                    start: start,
                    end: end,
                    allDay: true,
                    className: categoryClass
                }, true);
                $this.$modal.modal('hide');
            } else {
                alert('You have to give a title to your event');
            }
            return false;
        });

        $this.$calendarObj.fullCalendar('unselect');
    };

    // Enable Dragging
    CalendarApp.prototype.enableDrag = function () {
        $(this.$event).each(function () {
            var eventObject = {title: $.trim($(this).text())};
            $(this).data('eventObject', eventObject);
            $(this).draggable({zIndex: 999, revert: true, revertDuration: 0});
        });
    };

    // Initialize Calendar
    CalendarApp.prototype.init = function () {
        var $this = this;
        this.enableDrag();

        // Fetch Events from API
        function fetchEvents(callback) {
            $.ajax({
                url: "/management/api/events/", // Update with your Django API endpoint
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${localStorage.getItem("authToken")}`,
                    "X-CSRFToken": getCookie("csrftoken"),
                    "Accept": "application/json"
                },
                dataType: "json",
                success: function (data) {
                    callback(data);
                },
                error: function () {
                    console.error("Failed to fetch events");
                    callback([]);
                }
            });
        }

        fetchEvents(function (events) {
            $this.$calendarObj = $this.$calendar.fullCalendar({
                slotDuration: '00:15:00',
                minTime: '08:00:00',
                maxTime: '19:00:00',
                defaultView: 'month',
                handleWindowResize: true,
                header: {left: 'prev,next today', center: 'title', right: 'month,agendaWeek,agendaDay'},
                events: events, // Load dynamic events
                editable: true,
                droppable: true,
                eventLimit: true,
                selectable: true,
                drop: function (date) {
                    $this.onDrop($(this), date);
                },
                select: function (start, end, allDay) {
                    $this.onSelect(start, end, allDay);
                },
                eventClick: function (calEvent, jsEvent, view) {
                    $this.onEventClick(calEvent, jsEvent, view);
                }
            });
        });

        // Add new event category
        this.$saveCategoryBtn.on('click', function () {
            var categoryName = $this.$categoryForm.find("input[name='category-name']").val();
            var categoryColor = $this.$categoryForm.find("select[name='category-color']").val();

            if (categoryName !== null && categoryName.length !== 0) {
                $this.$extEvents.append(`
                    <div class="calendar-events" data-class="bg-${categoryColor}" style="position: relative;">
                        <i class="fa fa-circle text-${categoryColor}"></i> ${categoryName}
                    </div>
                `);
                $this.enableDrag();
            }
        });
    };

    $.CalendarApp = new CalendarApp();
    $.CalendarApp.Constructor = CalendarApp;

}(window.jQuery);

// Initialize Calendar
(function ($) {
    "use strict";
    $.CalendarApp.init();
})(window.jQuery);
