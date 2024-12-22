// Set new default font family and font color to mimic Bootstrap's default styling
Chart.defaults.global.defaultFontFamily = '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#292b2c';

// Pie Chart Example
fetch('/students/pie-chart/') // Replace with your actual API endpoint
  .then(response => response.json())
  .then(data => {
var ctx = document.getElementById("myPieChart");
var myPieChart = new Chart(ctx, {
  type: 'pie',
  data: {
    labels: data.data.labels,
    datasets: [{
      data: data.data.datasets[0].data, // Use data from the API response
      backgroundColor:data.data.datasets[0].backgroundColor,
    }],
  },
});
  })
  .catch(error => {
    console.error('Error fetching pie chart data:', error);
  });
