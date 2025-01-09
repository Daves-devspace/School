'use strict';

$(document).ready(function () {
    // Area chart
    if ($('#apexcharts-area').length > 0) {
        $.ajax({
            url: "{% url 'line_chart' %}",  // Make sure this URL matches the one for your Django view
            type: 'GET',
            dataType: 'json',
            success: function (response) {
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
                        data: response.data.datasets[0].data  // Use the revenue data from the response
                    }],
                    xaxis: {
                        categories: response.data.labels,  // Use the month labels from the response
                    }
                };

                var chart = new ApexCharts(
                    document.querySelector("#apexcharts-area"),
                    options
                );
                chart.render();
            }
        });
    }


    // // For plain JavaScript
    // document.addEventListener("DOMContentLoaded", function () {
    //     const options = {
    //         chart: {
    //             type: 'bar',
    //             height: 350,
    //         },
    //         series: [
    //             {
    //                 name: "Marks",
    //                 data: [85, 90, 78, 88], // Example marks data
    //             },
    //         ],
    //         xaxis: {
    //             categories: ["Math", "Science", "English", "History"], // Subjects
    //         },
    //         title: {
    //             text: "Student Performance in Term 1 Opener",
    //             align: "center",
    //         },
    //     };
    //
    //     const chart = new ApexCharts(document.querySelector("#chart"), options);
    //     chart.render();
    // });


    //
    // // Area chart
    //
    // if ($('#apexcharts-area').length > 0) {
    // var options = {
    // 	chart: {
    // 		height: 350,
    // 		type: "area",
    // 		toolbar: {
    // 			show: false
    // 		},
    // 	},
    // 	dataLabels: {
    // 		enabled: false
    // 	},
    // 	stroke: {
    // 		curve: "smooth"
    // 	},
    // 	series: [{
    // 		name: "Teachers",
    // 		data: [45, 60, 75, 51, 42, 42, 30]
    // 	}, {
    // 		name: "Students",
    // 		color: '#406bd6',
    // 		data: [24, 48, 56, 32, 34, 52, 25]
    // 	}],
    // 	xaxis: {
    // 		categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
    // 	}
    // }
    // var chart = new ApexCharts(
    // 	document.querySelector("#apexcharts-area"),
    // 	options
    // );
    // chart.render();
    // }

//     // Bar chart
//
//     if ($('#bar').length > 0) {
//         var optionsBar = {
//             chart: {
//                 type: 'bar',
//                 height: 350,
//                 width: '100%',
//                 stacked: true,
//                 toolbar: {
//                     show: false
//                 },
//             },
//             dataLabels: {
//                 enabled: false
//             },
//             plotOptions: {
//                 bar: {
//                     columnWidth: '45%',
//                 }
//             },
//             series: [{
//                 name: "Boys",
//                 color: '#fdbb38',
//                 data: [420, 532, 516, 575, 519, 517, 454, 392, 262, 383, 446, 551, 563, 421, 563, 254, 452],
//             }, {
//                 name: "Girls",
//                 color: '#406bd6',
//                 data: [336, 612, 344, 647, 345, 563, 256, 344, 323, 300, 455, 456, 526, 652, 325, 425, 436],
//             }],
//             labels: [2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020],
//             xaxis: {
//                 labels: {
//                     show: false
//                 },
//                 axisBorder: {
//                     show: false
//                 },
//                 axisTicks: {
//                     show: false
//                 },
//             },
//             yaxis: {
//                 axisBorder: {
//                     show: false
//                 },
//                 axisTicks: {
//                     show: false
//                 },
//                 labels: {
//                     style: {
//                         colors: '#777'
//                     }
//                 }
//             },
//             title: {
//                 text: '',
//                 align: 'left',
//                 style: {
//                     fontSize: '18px'
//                 }
//             }
//
//         }
//
//         var chartBar = new ApexCharts(document.querySelector('#bar'), optionsBar);
//         chartBar.render();
//     }
//
// });
//     $(document).ready(function () {
//
//         if ($('#pie').length > 0) {
//             var optionsPie = {
//                 chart: {
//                     type: 'pie',
//                     height: 350,
//                 },
//                 labels: ['Boys', 'Girls'],
//                 series: [420, 336], // Same data as the bar chart for testing
//                 colors: ['#4e73df', '#ff6384'],
//             };
//
//             var chartPie = new ApexCharts(document.querySelector('#pie'), optionsPie);
//             chartPie.render();
//         }
//     });
    $(document).ready(function () {
        if ($('#pie').length > 0) {
            $.ajax({
                url: '{% url "gender-pie-chart" %}',
                type: 'GET',
                dataType: 'json',
                success: function (data) {
                    if (data.labels && data.datasets && data.datasets[0].data) {
                        var optionsPie = {
                            chart: {type: 'pie', height: 350},
                            labels: data.labels,
                            series: data.datasets[0].data,
                            colors: data.datasets[0].backgroundColor,
                            legend: {position: 'bottom'},
                            title: {text: data.title || 'Gender Ratio', align: 'center'},
                        };
                        var chartPie = new ApexCharts(document.querySelector('#pie'), optionsPie);
                        chartPie.render();
                    } else {
                        console.error('Invalid data structure:', data);
                    }
                },
                error: function (xhr, status, error) {
                    console.error('Error fetching data:', status, error);
                },
            });
        }
    });


    // if ($('#pie').length > 0) {
    //     $.ajax({
    //         url: '/gender-pie-chart/',
    //         method: 'GET',
    //         success: function (data) {
    //             if (data.labels && data.datasets && data.datasets[0]) {
    //                 var optionsPie = {
    //                     chart: {
    //                         type: 'pie',
    //                         height: 350,
    //                     },
    //                     labels: ["Boys", "Girls"],
    //                     series: [1, 2], // Hardcoded
    //                     colors: ['#4e73df', '#ff6384'], // Hardcoded
    //                     legend: {
    //                         position: 'bottom',
    //                     },
    //                     title: {
    //                         text: "Gender Ratio",
    //                         align: 'center',
    //                         style: {
    //                             fontSize: '16px',
    //                         },
    //                     },
    //                 };
    //
    //
    //                 var chartPie = new ApexCharts(document.querySelector('#pie'), optionsPie);
    //                 chartPie.render();
    //             } else {
    //                 console.error('Invalid API response structure:', data);
    //             }
    //         },
    //         error: function (error) {
    //             console.error('Error fetching gender data:', error);
    //         },
    //     });
    // }


// if ($('#pie').length > 0) {
//     $.ajax({
//         url: '/gender-pie-chart/', // URL of the updated view
//         method: 'GET',
//         success: function (data) {
//             var optionsPie = {
//                 chart: {
//                     type: 'pie',
//                     height: 350,
//                 },
//                 labels: data.labels, // Gender categories
//                 series: data.datasets[0].data, // Gender data
//                 colors: data.datasets[0].backgroundColor, // Updated colors for the theme
//                 legend: {
//                     position: 'bottom',
//                 },
//                 title: {
//                     text: data.title,
//                     align: 'center',
//                     style: {
//                         fontSize: '16px',
//                     },
//                 },
//             };
//
//             // Use jQuery to select the element and initialize the chart
//             var chartPie = new ApexCharts($('#pie')[0], optionsPie);
//             chartPie.render();
//         },
//         error: function (error) {
//             console.log('Error fetching gender data:', error);
//         },
//     });
// }


    if (document.querySelector('#bar-chart')) {
        fetch('/trends/bar-chart-data/') // URL to fetch bar chart data
            .then(response => response.json())
            .then(data => {
                var optionsBar = {
                    chart: {
                        type: 'bar',
                        height: 350,
                    },
                    series: data.datasets.map(dataset => ({
                        name: dataset.label,
                        data: dataset.data,
                    })),
                    xaxis: {
                        categories: data.labels,
                    },
                    colors: ["rgba(78, 115, 223, 1)", "rgba(28, 200, 138, 1)"], // Custom colors
                    legend: {
                        position: 'top',
                    },
                    title: {
                        text: "Monthly Trends for Boys and Girls",
                        align: 'center',
                        style: {
                            fontSize: '16px',
                        },
                    },
                    dataLabels: {
                        enabled: false,
                    },
                    grid: {
                        borderColor: '#f1f1f1',
                    },
                };

                var chartBar = new ApexCharts(document.querySelector('#bar-chart'), optionsBar);
                chartBar.render();
            })
            .catch(error => console.error("Error fetching bar chart data:", error));
    }


// #revenue chat

// Check if the element for the chart exists
    if ($('#revenue_chart').length > 0) {
        $.ajax({
            url: "{% url 'revenue_line_chart' %}", // Django view URL for chart data
            type: 'GET',
            dataType: 'json',
            success: function (response) {
                // Chart options and configuration
                var options = {
                    chart: {
                        height: 350,
                        type: 'line', // Chart type
                        toolbar: {
                            show: false // Hide the toolbar
                        },
                    },
                    dataLabels: {
                        enabled: false // Disable data labels on points
                    },
                    stroke: {
                        curve: 'smooth' // Smooth curve for lines
                    },
                    title: {
                        text: response.title, // Dynamic chart title from the response
                        align: 'left', // Align title to the left
                        style: {
                            fontSize: '16px',
                            fontWeight: 'bold',
                        }
                    },
                    series: [
                        {
                            name: 'Revenue', // Revenue dataset
                            data: response.data.datasets[0].data
                        },
                        {
                            name: 'Expenses', // Expenses dataset
                            data: response.data.datasets[1].data
                        }
                    ],
                    xaxis: {
                        categories: response.data.labels, // Dynamic x-axis labels
                        title: {
                            text: 'Months' // Label for x-axis
                        }
                    },
                    yaxis: {
                        title: {
                            text: 'Amount (in Ksh)' // Y-axis label
                        }
                    },
                    colors: ['#4e73df', '#ff6384'], // Colors for each dataset
                    tooltip: {
                        shared: true, // Shared tooltip for better clarity
                        intersect: false // Avoid overlapping tooltips
                    },
                    fill: {
                        type: 'gradient',
                        gradient: {
                            shadeIntensity: 1,
                            opacityFrom: 0.5,
                            opacityTo: 0,
                            stops: [0, 90, 100]
                        }
                    }
                };

                // Render the chart in the specified element
                var chart = new ApexCharts(document.querySelector("#revenue_chart"), options);
                chart.render();
            },
            error: function (xhr, status, error) {
                console.error('Error fetching chart data:', error); // Log errors
            }
        });
    }

    if ($('#bar').length > 0) {
        var optionsBar = {
            chart: {type: 'bar', height: 350, width: '100%', stacked: false, toolbar: {show: false},},
            dataLabels: {enabled: false},
            plotOptions: {bar: {columnWidth: '55%', endingShape: 'rounded'},},
            stroke: {show: true, width: 2, colors: ['transparent']},
            series: [{
                name: "Boys",
                color: '#70C4CF',
                data: [420, 532, 516, 575, 519, 517, 454, 392, 262, 383, 446, 551],
            }, {
                name: "Girls",
                color: '#3D5EE1',
                data: [336, 612, 344, 647, 345, 563, 256, 344, 323, 300, 455, 456],
            }],
            labels: [2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020],
            xaxis: {labels: {show: false}, axisBorder: {show: false}, axisTicks: {show: false},},
            yaxis: {axisBorder: {show: false}, axisTicks: {show: false}, labels: {style: {colors: '#777'}}},
            title: {text: '', align: 'left', style: {fontSize: '18px'}}
        }
        var chartBar = new ApexCharts(document.querySelector('#bar'), optionsBar);
        chartBar.render();
    }

})
;


// bar
// if ($('#bar').length > 0) {
//     $.ajax({
//         url: " {% url 'trends-bar-chart-data'%}", // Your Django endpoint
//         method: "GET",
//         success: function (response) {
//             console.log("Bar Chart Response:", response); // Debug response
//
//             var optionsBar = {
//                 chart: {
//                     type: 'bar',
//                     height: 350,
//                     width: '100%',
//                     stacked: false,
//                     toolbar: { show: false },
//                 },
//                 dataLabels: { enabled: false },
//                 plotOptions: {
//                     bar: { columnWidth: '55%', endingShape: 'rounded' },
//                 },
//                 stroke: {
//                     show: true,
//                     width: 2,
//                     colors: ['transparent'],
//                 },
//                 series: [
//                     {
//                         name: response.datasets[0].label,
//                         data: response.datasets[0].data,
//                     },
//                     {
//                         name: response.datasets[1].label,
//                         data: response.datasets[1].data,
//                     },
//                 ],
//                 xaxis: {
//                     categories: response.labels, // Month labels
//                 },
//                 yaxis: {
//                     labels: { style: { colors: '#777' } },
//                 },
//                 title: {
//                     text: response.title,
//                     align: 'left',
//                     style: { fontSize: '18px' },
//                 },
//             };
//
//             var chartBar = new ApexCharts(document.querySelector('#bar'), optionsBar);
//             chartBar.render();
//         },
//         error: function (error) {
//             console.error("Error fetching bar chart data:", error);
//         },
//     });
// }


// new
'use strict';
if ($('#subject-exams-chart').length > 0) {
    var options = {
        chart: {height: 350, type: 'bar', toolbar: {show: false}},
        plotOptions: {
            bar: {horizontal: false, columnWidth: '55%', endingShape: 'rounded'}
        },
        dataLabels: {enabled: false},
        stroke: {show: true, width: 2, colors: ['transparent']},
        series: [
            {name: 'Math - Opener', data: [80, 75, 85]},  // Marks for Math in Opener exam for 3 terms
            {name: 'Math - Midterm', data: [70, 65, 75]},  // Marks for Math in Midterm exam for 3 terms
            {name: 'Science - Opener', data: [75, 80, 85]},  // Marks for Science in Opener exam
            {name: 'Science - Midterm', data: [70, 72, 78]}  // Marks for Science in Midterm exam
        ],
        xaxis: {
            categories: ['Term 1', 'Term 2', 'Term 3'],  // Terms as categories
        },
        yaxis: {
            title: {text: 'Marks'},
        },
        title: {text: 'Subject Marks by Exam Type and Term'},
        fill: {opacity: 1},
        tooltip: {
            y: {
                formatter: function (val) {
                    return val + " Marks";  // Show the marks for each subject/exam type
                }
            }
        }
    }

    var chart = new ApexCharts(document.querySelector("#subject-exams-chart"), options);
    chart.render();
}

$(document).ready(function () {
    if ($('#apexcharts-areas').length > 0) {
        var options = {
            chart: {height: 350, type: "line", toolbar: {show: false},},
            dataLabels: {enabled: false},
            stroke: {curve: "smooth"},
            series: [{name: "Teachers", color: '#3D5EE1', data: [45, 60, 75, 51, 42, 42, 30]}, {
                name: "Students",
                color: '#70C4CF',
                data: [24, 48, 56, 32, 34, 52, 25]
            }],
            xaxis: {categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],}
        }
        var chart = new ApexCharts(document.querySelector("#apexcharts-area"), options);
        chart.render();
    }
    if ($('#school-area').length > 0) {
        var options = {
            chart: {height: 350, type: "area", toolbar: {show: false},},
            dataLabels: {enabled: false},
            stroke: {curve: "straight"},
            series: [{name: "Teachers", color: '#3D5EE1', data: [45, 60, 75, 51, 42, 42, 30]}, {
                name: "Students",
                color: '#70C4CF',
                data: [24, 48, 56, 32, 34, 52, 25]
            }],
            xaxis: {categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],}
        }
        var chart = new ApexCharts(document.querySelector("#school-area"), options);
        chart.render();
    }

    if ($('#s-line').length > 0) {
        var sline = {
            chart: {height: 350, type: 'line', zoom: {enabled: false}, toolbar: {show: false,}},
            dataLabels: {enabled: false},
            stroke: {curve: 'straight'},
            series: [{name: "Desktops", data: [10, 41, 35, 51, 49, 62, 69, 91, 148]}],
            title: {text: 'Product Trends by Month', align: 'left'},
            grid: {row: {colors: ['#f1f2f3', 'transparent'], opacity: 0.5},},
            xaxis: {categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'],}
        }
        var chart = new ApexCharts(document.querySelector("#s-line"), sline);
        chart.render();
    }
});
if ($('#s-line-area').length > 0) {
    var sLineArea = {
        chart: {height: 350, type: 'area', toolbar: {show: false,}},
        dataLabels: {enabled: false},
        stroke: {curve: 'smooth'},
        series: [{name: 'series1', data: [31, 40, 28, 51, 42, 109, 100]}, {
            name: 'series2',
            data: [11, 32, 45, 32, 34, 52, 41]
        }],
        xaxis: {
            type: 'datetime',
            categories: ["2018-09-19T00:00:00", "2018-09-19T01:30:00", "2018-09-19T02:30:00", "2018-09-19T03:30:00", "2018-09-19T04:30:00", "2018-09-19T05:30:00", "2018-09-19T06:30:00"],
        },
        tooltip: {x: {format: 'dd/MM/yy HH:mm'},}
    }
    var chart = new ApexCharts(document.querySelector("#s-line-area"), sLineArea);
    chart.render();
}
if ($('#s-col').length > 0) {
    var sCol = {
        chart: {height: 350, type: 'bar', toolbar: {show: false,}},
        plotOptions: {bar: {horizontal: false, columnWidth: '55%', endingShape: 'rounded'},},
        dataLabels: {enabled: false},
        stroke: {show: true, width: 2, colors: ['transparent']},
        series: [{name: 'subject', data: [44, 55, 57, 56, 61, 58, 63, 60, 66]}, {
            name: 'performance',
            data: [76, 85, 101, 98, 87, 105, 91, 114, 94]
        }],
        xaxis: {categories: ['Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct'],},
        yaxis: {title: {text: '$ (thousands)'}},
        fill: {opacity: 1},
        tooltip: {
            y: {
                formatter: function (val) {
                    return "$ " + val + " thousands"
                }
            }
        }
    }
    var chart = new ApexCharts(document.querySelector("#s-col"), sCol);
    chart.render();
}
if ($('#s-col-stacked').length > 0) {
    var sColStacked = {
        chart: {height: 350, type: 'bar', stacked: true, toolbar: {show: false,}},
        responsive: [{breakpoint: 480, options: {legend: {position: 'bottom', offsetX: -10, offsetY: 0}}}],
        plotOptions: {bar: {horizontal: false,},},
        series: [{name: 'PRODUCT A', data: [44, 55, 41, 67, 22, 43]}, {
            name: 'PRODUCT B',
            data: [13, 23, 20, 8, 13, 27]
        }, {name: 'PRODUCT C', data: [11, 17, 15, 15, 21, 14]}, {name: 'PRODUCT D', data: [21, 7, 25, 13, 22, 8]}],
        xaxis: {
            type: 'datetime',
            categories: ['01/01/2011 GMT', '01/02/2011 GMT', '01/03/2011 GMT', '01/04/2011 GMT', '01/05/2011 GMT', '01/06/2011 GMT'],
        },
        legend: {position: 'right', offsetY: 40},
        fill: {opacity: 1},
    }
    var chart = new ApexCharts(document.querySelector("#s-col-stacked"), sColStacked);
    chart.render();
}
if ($('#s-bar').length > 0) {
    var sBar = {
        chart: {height: 350, type: 'bar', toolbar: {show: false,}},
        plotOptions: {bar: {horizontal: true,}},
        dataLabels: {enabled: false},
        series: [{data: [400, 430, 448, 470, 540, 580, 690, 1100, 1200, 1380]}],
        xaxis: {categories: ['South Korea', 'Canada', 'United Kingdom', 'Netherlands', 'Italy', 'France', 'Japan', 'United States', 'China', 'Germany'],}
    }
    var chart = new ApexCharts(document.querySelector("#s-bar"), sBar);
    chart.render();
}
if ($('#mixed-chart').length > 0) {
    var options = {
        chart: {height: 350, type: 'line', toolbar: {show: false,}},
        series: [{
            name: 'Website Blog',
            type: 'column',
            data: [440, 505, 414, 671, 227, 413, 201, 352, 752, 320, 257, 160]
        }, {name: 'Social Media', type: 'line', data: [23, 42, 35, 27, 43, 22, 17, 31, 22, 22, 12, 16]}],
        stroke: {width: [0, 4]},
        title: {text: 'Traffic Sources'},
        labels: ['01 Jan 2001', '02 Jan 2001', '03 Jan 2001', '04 Jan 2001', '05 Jan 2001', '06 Jan 2001', '07 Jan 2001', '08 Jan 2001', '09 Jan 2001', '10 Jan 2001', '11 Jan 2001', '12 Jan 2001'],
        xaxis: {type: 'datetime'},
        yaxis: [{title: {text: 'Website Blog',},}, {opposite: true, title: {text: 'Social Media'}}]
    }
    var chart = new ApexCharts(document.querySelector("#mixed-chart"), options);
    chart.render();
}
if ($('#donut-chart').length > 0) {
    var donutChart = {
        chart: {height: 350, type: 'donut', toolbar: {show: false,}},
        series: [44, 55, 41, 17],
        responsive: [{breakpoint: 480, options: {chart: {width: 200}, legend: {position: 'bottom'}}}]
    }
    var donut = new ApexCharts(document.querySelector("#donut-chart"), donutChart);
    donut.render();
}
if ($('#radial-chart').length > 0) {
    var radialChart = {
        chart: {height: 350, type: 'radialBar', toolbar: {show: false,}},
        plotOptions: {
            radialBar: {
                dataLabels: {
                    name: {fontSize: '22px',},
                    value: {fontSize: '16px',},
                    total: {
                        show: true, label: 'Total', formatter: function (w) {
                            return 249
                        }
                    }
                }
            }
        },
        series: [44, 55, 67, 83],
        labels: ['Apples', 'Oranges', 'Bananas', 'Berries'],
    }
    var chart = new ApexCharts(document.querySelector("#radial-chart"), radialChart);
    chart.render();
}







