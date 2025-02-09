
function animateElements() {
    $('.circle-bar1').each(function () {
        var elementPos = $(this).offset().top;
        var topOfWindow = $(window).scrollTop();
        var percent = $(this).find('.circle-graph1').attr('data-percent');
        var animate = $(this).data('animate');

        // Check if the element is within the viewport and has not been animated
        if (elementPos < topOfWindow + $(window).height() - 30 && !animate) {
            $(this).data('animate', true);

            // Animate the circle with the percentage of progress
            $(this).find('.circle-graph1').circleProgress({
                value: percent / 100,  // Convert percentage to decimal (circleProgress expects a value between 0 and 1)
                size: 400,
                thickness: 30,
                fill: {color: '#6e6bfa'}
            });
        }
    });
}

// Call the function to animate elements when the page is loaded
$(document).ready(function () {
    animateElements();
});

// Optionally, you can also call this function during scroll events if you'd like the animation to trigger when the user scrolls:
$(window).scroll(function () {
    animateElements();
});

