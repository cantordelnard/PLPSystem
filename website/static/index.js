// **Navigation Hover Effect**

// Select all list items with class "navigation li"
let list = document.querySelectorAll(".navigation li");

function activeLink() {
  // Remove "hovered" class from all list items
  list.forEach((item) => {
    item.classList.remove("hovered");
  });
  // Add "hovered" class to the current list item (the one that triggered the event)
  this.classList.add("hovered");
}

// Add a "mouseover" event listener to each list item, calling the activeLink function
list.forEach((item) => item.addEventListener("mouseover", activeLink));





// **Navigation Menu Toggle**

// Select elements
let toggle = document.querySelector(".toggle");
let navigation = document.querySelector(".navigation");
let main = document.querySelector(".main");

// Add click event listener to the toggle element
toggle.onclick = function () {
  // Toggle "active" class on both navigation and main elements
  navigation.classList.toggle("active");
  main.classList.toggle("active");
};






// **Content Tabs based on Radio Button Selection**

// Select all radio button inputs
const radioInputs = document.querySelectorAll(
  '.radio-inputs input[type="radio"]'
);

// Select all content sections (admin, professor, student)
const contentInfo = document.querySelectorAll(
  ".content-info .admin, .content-info .professor, .content-info .student"
);

radioInputs.forEach((radioInput) => {
  radioInput.addEventListener("click", (event) => {
    // Get the text of the clicked radio button's sibling label (assuming the label is the next element)
    const selectedTab = event.target.nextElementSibling.innerText.toLowerCase();

    // Loop through all content sections
    contentInfo.forEach((info) => {
      // Show the content section that matches the selected tab text (converted to lowercase)
      info.style.display = info.classList.contains(selectedTab)
        ? "block"
        : "none";
    });
  });
});

// Show content for the checked radio button initially

const checkedRadio = document.querySelector(".radio-inputs input:checked");
if (checkedRadio) {
  const selectedTab = checkedRadio.nextElementSibling.innerText.toLowerCase();
  contentInfo.forEach((info) => {
    info.style.display = info.classList.contains(selectedTab)
      ? "block"
      : "none";
  });
}





// Select all radio button inputs within radio-inputs-1
const radioInputs1 = document.querySelectorAll('.radio-inputs-1 input[type="radio"]');

// Select all content sections based on the updated class names
const contentInfo1 = document.querySelectorAll('.content-info > div');

radioInputs1.forEach((radioInput) => {
  radioInput.addEventListener('click', (event) => {
    // Get the text of the clicked radio button's sibling span (assuming the span is the next element)
    const selectedTab = event.target.nextElementSibling.innerText.toLowerCase().replace('_', '_');

    // Loop through all content sections
    contentInfo1.forEach((info) => {
      // Show the content section that matches the selected tab text (converted to lowercase)
      info.style.display = info.classList.contains(selectedTab) ? 'block' : 'none';
    });
  });
});

// Show content for the checked radio button initially
const checkedRadio1 = document.querySelector('.radio-inputs-1 input:checked');
if (checkedRadio1) {
  const selectedTab = checkedRadio1.nextElementSibling.innerText.toLowerCase().replace('_', '_');
  contentInfo1.forEach((info) => {
    info.style.display = info.classList.contains(selectedTab) ? 'block' : 'none';
  });
}












// **Flash Message Auto-Dismiss**

document.addEventListener("DOMContentLoaded", function () {
  const flashMessage = document.getElementById("flash-message");

  if (flashMessage) {
    // Set a timeout to remove the flash message after 3.5 seconds (adjust as needed)
    setTimeout(function () {
      flashMessage.remove();
    }, 3500);
  }
});








const root = document.documentElement;
const marqueeElementsDisplayed = getComputedStyle(root).getPropertyValue("--marquee-elements-displayed");
const marqueeContent = document.querySelector("ul.marquee-content");

root.style.setProperty("--marquee-elements", marqueeContent.children.length);

for (let i = 0; i < marqueeElementsDisplayed; i++) {
    marqueeContent.appendChild(marqueeContent.children[i].cloneNode(true));
}





















