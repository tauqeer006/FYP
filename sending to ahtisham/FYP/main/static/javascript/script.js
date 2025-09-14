const wrapper = document.querySelector(".wrapper"),
signupHeader = document.querySelector(".signup header"),
loginHeader = document.querySelector(".login header");

loginHeader.addEventListener("click", () => {
wrapper.classList.add("active");
});

signupHeader.addEventListener("click", () => {
wrapper.classList.remove("active");
});

function showPopup() {
alert("Your account has been created");
wrapper.classList.add("active"); // Open the login panel after clicking "OK"
}


let arrow = document.querySelectorAll(".arrow");
  for (var i = 0; i < arrow.length; i++) {
    arrow[i].addEventListener("click", (e)=>{
   let arrowParent = e.target.parentElement.parentElement;//selecting main parent of arrow
   arrowParent.classList.toggle("showMenu");
    });
  }
  let sidebar = document.querySelector(".sidebar");
  let sidebarBtn = document.querySelector(".bx-menu");
  console.log(sidebarBtn);
  sidebarBtn.addEventListener("click", ()=>{
    sidebar.classList.toggle("close");
  }); 


  ///signup choice/
  // Toggle signup options display
document.getElementById('loginBtn').addEventListener('click', function () {
  var signupOptions = document.getElementById('signupOptions');
  signupOptions.classList.toggle('show');
});

// Handle doctor signup button click
document.getElementById('doctorSignupBtn').addEventListener('click', function () {
  alert('Doctor signup clicked');
  window.location.href = 'signup.html';
});

// Handle patient signup button click
document.getElementById('patientSignupBtn').addEventListener('click', function () {
  alert('Patient signup clicked');
  window.location.href = 'signup.html';
});

// Style doctor signup button
var doctorSignupBtn = document.getElementById('doctorSignupBtn');
doctorSignupBtn.style.backgroundColor = 'rgb(14, 225, 200)';
doctorSignupBtn.style.color = 'white';
doctorSignupBtn.style.border = 'none';

// Style patient signup button
var patientSignupBtn = document.getElementById('patientSignupBtn');
patientSignupBtn.style.backgroundColor = 'rgb(14, 225, 200)';
patientSignupBtn.style.border = 'none';
patientSignupBtn.style.color = 'white';

