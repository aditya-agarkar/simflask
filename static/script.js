let sidebar = document.querySelector(".sidebar");
let closeBtn = document.querySelector("#btn");
let searchBtn = document.querySelector(".bx-search");
closeBtn.addEventListener("click", () => {
  sidebar.classList.toggle("open");
  menuBtnChange(); //calling the function(optional)
});
searchBtn.addEventListener("click", () => {
  // Sidebar open when you click on the search iocn
  sidebar.classList.toggle("open");
  menuBtnChange(); //calling the function(optional)
});
// following are the code to change sidebar button(optional)
function menuBtnChange() {
  if (sidebar.classList.contains("open")) {
    closeBtn.classList.replace("bx-menu", "bx-menu-alt-right"); //replacing the iocns class
  } else {
    closeBtn.classList.replace("bx-menu-alt-right", "bx-menu"); //replacing the iocns class
  }
}

// Function to open the modal
function addModal() {
    let modal = document.getElementById("addModal");
    modal.style.display = "block";
}

function assignModal() {
    let modal = document.getElementById("assignModal");
    modal.style.display = "block";
}

function moreModal(sim_id) {
    let modal = document.getElementById("moreModal");
    
    // Use AJAX to fetch sim details
    fetch('/get_sim/' + sim_id)
    .then(response => response.json())
    .then(data => {
        // Populate modal placeholders with the fetched data
        //document.getElementById("simId").innerHTML = "ID: " + data.id;
        document.getElementById("simName").innerHTML = data.sim_name;
        document.getElementById("simDesc").innerHTML = data.sim_desc;
        document.getElementById("simEmbed").innerHTML = "https://topsim.ai" + data.id;
        document.getElementById("simImage").innerHTML = "<img src='static/images/" + data.image + "'>";
        let buttonHTML = '<button onclick="location.href=\'/delete_sim/' + data.id + '\'">Delete</button>';
        document.getElementById("delButton").innerHTML=buttonHTML;

        modal.style.display = "block";
    });
}

// Function to close the modal
function closeAddModal() {
    let modal = document.getElementById("addModal");
    modal.style.display = "none";
}

function closeAssignModal() {
    let modal = document.getElementById("assignModal");
    modal.style.display = "none";
}

function closeMoreModal() {
    let modal = document.getElementById("moreModal");
    modal.style.display = "none";
}

