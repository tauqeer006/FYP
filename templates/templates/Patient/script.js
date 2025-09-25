//pre loader
window.addEventListener('load', () => {
  const preloader = document.getElementById('preloader');
  if (preloader) {
    preloader.classList.add('opacity-0', 'transition-opacity', 'duration-500');
    setTimeout(() => preloader.style.display = 'none', 500);
  }
});

















document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('create-user-btn').addEventListener('click', function (e) {
    e.preventDefault();

    fetch('user/create_user.html')
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
//user llist 
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('user_list').addEventListener('click', function (e) {
    e.preventDefault();

    fetch('user/user_list.html')
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
//edit user page
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('edit_btn').addEventListener('click', function (e) {
    e.preventDefault();

    fetch('user/edit_user.html')
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
//doctors section btn
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('detaill_patient_btn').addEventListener('click', function (e) {
    e.preventDefault();

    fetch('report/detailed_history.html')
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
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('edit_doctor_btn_2').addEventListener('click', function (e) {
    e.preventDefault();

    fetch('doctor/edit_doctor.html')
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
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('list_doctor_btn_2').addEventListener('click', function (e) {
    e.preventDefault();

    fetch('doctor/list_doctor.html')
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
