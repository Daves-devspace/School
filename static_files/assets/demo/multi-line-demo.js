// var ctx = document.getElementById('myChart').getContext('2d');
// var myChart = new Chart(ctx, {
//   type: 'bar', // Bar chart type
//   data: {
//     labels: ['Term 1', 'Term 2', 'Term 3'], // X-axis representing the terms
//     datasets: [
//       // Data for each subject in each test
//       {
//         label: 'English - Opener',
//         data: [75, 85, 80],
//         backgroundColor: 'rgba(255, 99, 132, 0.7)', // Red color
//         borderColor: 'rgba(255, 99, 132, 1)',
//         borderWidth: 1,
//         stack: 'stack1' // Group bars by stack
//       },
//       {
//         label: 'Kiswahili - Opener',
//         data: [70, 80, 75],
//         backgroundColor: 'rgba(54, 162, 235, 0.7)', // Blue color
//         borderColor: 'rgba(54, 162, 235, 1)',
//         borderWidth: 1,
//         stack: 'stack1'
//       },
//       {
//         label: 'Math - Opener',
//         data: [85, 90, 88],
//         backgroundColor: 'rgba(75, 192, 192, 0.7)', // Green color
//         borderColor: 'rgba(75, 192, 192, 1)',
//         borderWidth: 1,
//         stack: 'stack1'
//       },
//       {
//         label: 'Science - Opener',
//         data: [92, 94, 93],
//         backgroundColor: 'rgba(153, 102, 255, 0.7)', // Purple color
//         borderColor: 'rgba(153, 102, 255, 1)',
//         borderWidth: 1,
//         stack: 'stack1'
//       },
//       {
//         label: 'Social Studies - Opener',
//         data: [78, 85, 82],
//         backgroundColor: 'rgba(255, 159, 64, 0.7)', // Orange color
//         borderColor: 'rgba(255, 159, 64, 1)',
//         borderWidth: 1,
//         stack: 'stack1'
//       },
//       {
//         label: 'CRE - Opener',
//         data: [80, 88, 84],
//         backgroundColor: 'rgba(255, 205, 86, 0.7)', // Yellow color
//         borderColor: 'rgba(255, 205, 86, 1)',
//         borderWidth: 1,
//         stack: 'stack1'
//       },
//       {
//         label: 'English - Mid-Term',
//         data: [78, 85, 80],
//         backgroundColor: 'rgba(255, 99, 132, 0.7)', // Red color
//         borderColor: 'rgba(255, 99, 132, 1)',
//         borderWidth: 1,
//         stack: 'stack2' // Different stack for Mid-Term
//       },
//       {
//         label: 'Kiswahili - Mid-Term',
//         data: [72, 82, 78],
//         backgroundColor: 'rgba(54, 162, 235, 0.7)', // Blue color
//         borderColor: 'rgba(54, 162, 235, 1)',
//         borderWidth: 1,
//         stack: 'stack2'
//       },
//       {
//         label: 'Math - Mid-Term',
//         data: [88, 92, 90],
//         backgroundColor: 'rgba(75, 192, 192, 0.7)', // Green color
//         borderColor: 'rgba(75, 192, 192, 1)',
//         borderWidth: 1,
//         stack: 'stack2'
//       },
//       {
//         label: 'Science - Mid-Term',
//         data: [94, 96, 95],
//         backgroundColor: 'rgba(153, 102, 255, 0.7)', // Purple color
//         borderColor: 'rgba(153, 102, 255, 1)',
//         borderWidth: 1,
//         stack: 'stack2'
//       },
//       {
//         label: 'Social Studies - Mid-Term',
//         data: [82, 88, 85],
//         backgroundColor: 'rgba(255, 159, 64, 0.7)', // Orange color
//         borderColor: 'rgba(255, 159, 64, 1)',
//         borderWidth: 1,
//         stack: 'stack2'
//       },
//       {
//         label: 'CRE - Mid-Term',
//         data: [85, 90, 87],
//         backgroundColor: 'rgba(255, 205, 86, 0.7)', // Yellow color
//         borderColor: 'rgba(255, 205, 86, 1)',
//         borderWidth: 1,
//         stack: 'stack2'
//       },
//       {
//         label: 'English - End of Term',
//         data: [80, 88, 85],
//         backgroundColor: 'rgba(255, 99, 132, 0.7)', // Red color
//         borderColor: 'rgba(255, 99, 132, 1)',
//         borderWidth: 1,
//         stack: 'stack3' // Different stack for End of Term
//       },
//       {
//         label: 'Kiswahili - End of Term',
//         data: [75, 85, 80],
//         backgroundColor: 'rgba(54, 162, 235, 0.7)', // Blue color
//         borderColor: 'rgba(54, 162, 235, 1)',
//         borderWidth: 1,
//         stack: 'stack3'
//       },
//       {
//         label: 'Math - End of Term',
//         data: [90, 95, 92],
//         backgroundColor: 'rgba(75, 192, 192, 0.7)', // Green color
//         borderColor: 'rgba(75, 192, 192, 1)',
//         borderWidth: 1,
//         stack: 'stack3'
//       },
//       {
//         label: 'Science - End of Term',
//         data: [96, 98, 97],
//         backgroundColor: 'rgba(153, 102, 255, 0.7)', // Purple color
//         borderColor: 'rgba(153, 102, 255, 1)',
//         borderWidth: 1,
//         stack: 'stack3'
//       },
//       {
//         label: 'Social Studies - End of Term',
//         data: [85, 90, 88],
//         backgroundColor: 'rgba(255, 159, 64, 0.7)', // Orange color
//         borderColor: 'rgba(255, 159, 64, 1)',
//         borderWidth: 1,
//         stack: 'stack3'
//       },
//       {
//         label: 'CRE - End of Term',
//         data: [88, 93, 90],
//         backgroundColor: 'rgba(255, 205, 86, 0.7)', // Yellow color
//         borderColor: 'rgba(255, 205, 86, 1)',
//         borderWidth: 1,
//         stack: 'stack3'
//       }
//     ]
//   },
//   options: {
//     scales: {
//       xAxes: [{
//         stacked: true,  // Enable stacked bars
//       }],
//       yAxes: [{
//         stacked: true,  // Enable stacking on y-axis
//         ticks: {
//           beginAtZero: true,
//           max: 100  // Set max score to 100
//         }
//       }]
//     },
//     responsive: true,
//     maintainAspectRatio: false,
//     title: {
//       display: true,
//       text: 'Term-wise Performance by Subject (Opener, Mid-Term, End of Term)'
//     }
//   }
// });











    var ctx = document.getElementById('myChart').getContext('2d');
    var myChart = new Chart(ctx, {
      type: 'line',  // Line chart type
      data: {
        labels: [
          'Term 1: Opener', 'Term 1: Mid-Term', 'Term 1: End of Term',  // Term 1 tests
          'Term 2: Opener', 'Term 2: Mid-Term', 'Term 2: End of Term',  // Term 2 tests
          'Term 3: Opener', 'Term 3: Mid-Term', 'End of Year Exam'  // Term 3 tests (End of Year Exam)
        ],
        datasets: [
          {
            label: 'English',  // Dataset for English
            data: [75, 80, 70, 85, 88, 90, 80, 85, 90],  // English test scores
            borderColor: 'rgba(255, 99, 132, 1)',  // Line color (Red)
            backgroundColor: 'rgba(255, 99, 132, 0.2)',  // Fill color
            fill: true,  // Fill area under the line
            borderWidth: 3,  // Line width
            tension: 0.4,  // Smoothness of the line
            pointRadius: 2,  // Radius of the points
            pointBackgroundColor: 'rgba(255, 99, 132, 1)',  // Point color
          },
          {
            label: 'Kiswahili',  // Dataset for Kiswahili
            data: [70, 72, 68, 80, 82, 85, 75, 80, 88],  // Kiswahili test scores
            borderColor: 'rgba(54, 162, 235, 1)',  // Line color (Blue)
            backgroundColor: 'rgba(54, 162, 235, 0.2)',  // Fill color
            fill: true,  // Fill area under the line
            borderWidth: 3,  // Line width
            tension: 0.4,  // Smoothness of the line
            pointRadius: 2,  // Radius of the points
            pointBackgroundColor: 'rgba(54, 162, 235, 1)',  // Point color
          },
          {
            label: 'Math',  // Dataset for Math
            data: [85, 88, 80, 92, 90, 95, 84, 86, 91],  // Math test scores
            borderColor: 'rgba(75, 192, 192, 1)',  // Line color (Teal)
            backgroundColor: 'rgba(75, 192, 192, 0.2)',  // Fill color
            fill: true,  // Fill area under the line
            borderWidth: 3,  // Line width
            tension: 0.4,  // Smoothness of the line
            pointRadius: 2,  // Radius of the points
            pointBackgroundColor: 'rgba(75, 192, 192, 1)',  // Point color
          },
          {
            label: 'Science',  // Dataset for Science
            data: [92, 90, 88, 94, 93, 97, 90, 93, 96],  // Science test scores
            borderColor: 'rgba(153, 102, 255, 1)',  // Line color (Purple)
            backgroundColor: 'rgba(153, 102, 255, 0.2)',  // Fill color
            fill: true,  // Fill area under the line
            borderWidth: 3,  // Line width
            tension: 0.4,  // Smoothness of the line
            pointRadius: 2,  // Radius of the points
            pointBackgroundColor: 'rgba(153, 102, 255, 1)',  // Point color
          },
          {
            label: 'Social Studies',  // Dataset for Social Studies
            data: [78, 80, 75, 85, 84, 90, 82, 88, 91],  // Social Studies test scores
            borderColor: 'rgba(255, 159, 64, 1)',  // Line color (Orange)
            backgroundColor: 'rgba(255, 159, 64, 0.2)',  // Fill color
            fill: true,  // Fill area under the line
            borderWidth: 3,  // Line width
            tension: 0.4,  // Smoothness of the line
            pointRadius: 2,  // Radius of the points
            pointBackgroundColor: 'rgba(255, 159, 64, 1)',  // Point color
          },
          {
            label: 'CRE',  // Dataset for CRE
            data: [80, 85, 78, 88, 87, 92, 85, 90, 93],  // CRE test scores
            borderColor: 'rgba(255, 205, 86, 1)',  // Line color (Yellow)
            backgroundColor: 'rgba(255, 205, 86, 0.2)',  // Fill color
            fill: true,  // Fill area under the line
            borderWidth: 3,  // Line width
            tension: 0.4,  // Smoothness of the line
            pointRadius:2,  // Radius of the points
            pointBackgroundColor: 'rgba(255, 205, 86, 1)',  // Point color
          }
        ]
      },
      options: {
        scales: {
          xAxes: [{
            ticks: {
              autoSkip: true,  // Skip some labels to prevent overlap
              maxRotation: 45,  // Rotate labels for better visibility
              minRotation: 30,  // Set a minimum rotation for legibility
            },
            scaleLabel: {
              display: true,
              labelString: 'Tests'  // Label for x-axis
            }
          }],
          yAxes: [{
            ticks: {
              beginAtZero: true,  // Start y-axis from zero
              max: 100,  // Maximum value for marks
            },
            scaleLabel: {
              display: true,
              labelString: 'Marks (%)'  // Label for y-axis
            }
          }]
        },
        title: {
          display: true,
          text: 'Student Performance over 3 Terms (with Tests)'  // Title of the chart
        },
        legend: {
          position: 'top',  // Position the legend at the top
          labels: {
            fontColor: '#333',  // Customize font color
            boxWidth: 20,  // Legend box width
          }
        },
        responsive: true,  // Make the chart responsive
        maintainAspectRatio: false,  // Allow resizing the chart
        tooltips: {
          mode: 'nearest',  // Tooltip display mode
          intersect: false,  // Tooltip does not show when hovering over the lines directly
        }
      }
    });

