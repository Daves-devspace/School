<!-- Script to Render the Chart -->

$(document).ready(function () {
    // Check if the chart container exists
    if ($('#apexcharts-area').length > 0) {
        // Fetch data from the Django view
        $.ajax({
            url:"/management/revenue/line-chart/",
            type: 'GET',
            dataType: 'json',
            success: function (response) {
                if (response && response.data) {
                    // Chart configuration
                    var options = {
                        chart: {
                            height: 350,
                            type: "area",
                            toolbar: {
                                show: false
                            },
                        },
                        dataLabels: {
                            enabled: false
                        },
                        stroke: {
                            curve: "smooth"
                        },
                        series: [{
                            name: "Revenue",
                            data: response.data.datasets[0].data
                        }],
                        xaxis: {
                            categories: response.data.labels,
                        }
                    };

                    // Render the chart
                    var chart = new ApexCharts(
                        document.querySelector("#apexcharts-area"),
                        options
                    );
                    chart.render();
                } else {
                    console.error("Invalid response format:", response);
                }
            },
            error: function (xhr, status, error) {
                console.error("Error fetching chart data:", error);
            }
        });
    }
});


//students gender
$(document).ready(function () {
    if ($('#pie').length > 0) { // Ensure the div exists
        $.ajax({
            url:'/management/gender-pie-chart/', // URL of the updated view
            method: 'GET',
            success: function (data) {
                var optionsPie = {
                    chart: {
                        type: 'pie',
                        height: 350,
                    },
                    labels: data.labels, // Gender categories
                    series: data.datasets[0].data, // Gender data
                    colors: data.datasets[0].backgroundColor, // Colors for each section
                    legend: {
                        position: 'bottom',
                    },
                    title: {
                        text: data.title, // Use the title from the API
                        align: 'center',
                        style: {
                            fontSize: '16px',
                        },
                    },
                };

                // Render the chart
                var chartPie = new ApexCharts(document.querySelector('#pie'), optionsPie);
                chartPie.render();
            },
            error: function (error) {
                console.log('Error fetching gender data:', error);
            },
        });

    }
});


if ($('#bar').length > 0) {
    $.ajax({
        url: "/trends-bar-chart-data/", // Update to match your Django URL route
        method: "GET",
        success: function (response) {
            // Create the bar chart dynamically using the response data
            var optionsBar = {
                chart: {
                    type: 'bar',
                    height: 350,
                    width: '100%',
                    stacked: false,
                    toolbar: {show: false},
                },
                dataLabels: {enabled: false},
                plotOptions: {
                    bar: {columnWidth: '55%', endingShape: 'rounded'},
                },
                stroke: {
                    show: true,
                    width: 2,
                    colors: ['transparent'],
                },
                series: [
                    {
                        name: response.datasets[0].label,
                        color: response.datasets[0].backgroundColor,
                        data: response.datasets[0].data,
                    },
                    {
                        name: response.datasets[1].label,
                        color: response.datasets[1].backgroundColor,
                        data: response.datasets[1].data,
                    },
                ],
                labels: response.labels, // Month labels from the view
                xaxis: {
                    labels: {show: true},
                    axisBorder: {show: false},
                    axisTicks: {show: false},
                },
                yaxis: {
                    axisBorder: {show: false},
                    axisTicks: {show: false},
                    labels: {style: {colors: '#777'}},
                },
                title: {
                    text: response.title,
                    align: 'left',
                    style: {fontSize: '18px'},
                },
            };

            // Render the chart
            var chartBar = new ApexCharts(document.querySelector('#bar'), optionsBar);
            chartBar.render();
        },
        error: function (error) {
            console.error("Error fetching bar chart data:", error);
        },
    });
}

