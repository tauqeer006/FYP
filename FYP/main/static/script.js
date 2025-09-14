// preloader.js

window.addEventListener('load', function () {
  setTimeout(function () {
    const preloader = document.querySelector('.preloader');
    if (preloader) {
      preloader.style.display = 'none';
    }
  }, 800); // Delay before hiding preloader (adjust as needed)
});


//doctor welcome alert 
window.addEventListener("DOMContentLoaded", () => {
    const alertBox = document.getElementById("dashboard-alert");

    // Slide in
    alertBox.classList.remove("translate-x-full", "opacity-0");
    alertBox.classList.add("translate-x-0", "opacity-100");

    // Auto hide after 5 seconds
    setTimeout(() => {
      alertBox.classList.remove("translate-x-0", "opacity-100");
      alertBox.classList.add("translate-x-full", "opacity-0");
    }, 5000);
  });
  // counter on start
document.addEventListener("DOMContentLoaded", function () {
  const contentArea = document.getElementById("content-area");
  contentArea.innerHTML = `
    <div id="default-dashboard" class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
      <div class="bg-white p-6 rounded-lg shadow hover:shadow-md transition">
        <h4 class="text-lg font-semibold text-gray-700 mb-2">Total Patients</h4>
        <p class="text-3xl font-bold text-blue-600">1,230</p>
      </div>
      <div class="bg-white p-6 rounded-lg shadow hover:shadow-md transition">
        <h4 class="text-lg font-semibold text-gray-700 mb-2">Cured Patients</h4>
        <div class="w-full bg-gray-200 rounded-full h-4 mb-2">
          <div class="bg-green-500 h-4 rounded-full" style="width: 78%"></div>
        </div>
        <p class="text-sm text-gray-600">78% of patients cured</p>
      </div>
      <div class="bg-white p-6 rounded-lg shadow hover:shadow-md transition">
        <h4 class="text-lg font-semibold text-gray-700 mb-2">Total Reports</h4>
        <p class="text-3xl font-bold text-purple-600">3,450</p>
      </div>
    </div>`;
});













//Predict llist 
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('predict_btn').addEventListener('click', function (e) {
    e.preventDefault();

    fetch('report/start_diagnosis.html')
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to load form');
        }
        return response.text();
      })
      .then(html => {
        document.getElementById('content-area').innerHTML = html;
      })
      .catch(error => {
        console.error('Error loading form:', error);
        document.getElementById('content-area').innerHTML = '<p class="text-red-500">Could not load form.</p>';
      });
  });
});
