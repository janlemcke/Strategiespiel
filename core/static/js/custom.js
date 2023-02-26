// Define a function to make the API request and update the UI
function updateResources(pk) {
    fetch('/api/town/' + pk + '/resources')
        .then(response => response.json())
        .then(data => {
            // Update the UI with the new resource values
            updateResourcesUI(data.resources);
        })
        .catch(error => {
            // Handle errors
            console.error('Error fetching resources:', error);
        });
}

// Define a function to update the UI with the new resource values
function updateResourcesUI(resources) {
    // Update the UI with the new resource values
    const wood_resource = document.querySelector('#wood');
    const stone_resource = document.querySelector('#stone');
    const gold_resource = document.querySelector('#gold');
    const tools_resource = document.querySelector('#tools');

    wood_resource.textContent = resources.wood;
    stone_resource.textContent = resources.stone;
    gold_resource.textContent = resources.gold;
    tools_resource.textContent = resources.tools;

    wood_resource.classList.add("updated");
    stone_resource.classList.add("updated");
    gold_resource.classList.add("updated");
    tools_resource.classList.add("updated");

    setTimeout(() => {
        wood_resource.classList.remove('updated');
        stone_resource.classList.remove('updated');
        gold_resource.classList.remove('updated');
        tools_resource.classList.remove('updated');
    }, 5 * 1000);
}

function countdown(object, startDate, endDate) {
    var countDownDate = new Date(endDate);
    var startDate = new Date(startDate);
    var totalSeconds = countDownDate - startDate;
    x = setInterval(function () {

        var now = new Date().getTime();
        // Find the distance between now and the count down date
        var distance = countDownDate - now;

        // Time calculations for days, hours, minutes and seconds
        var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        var seconds = Math.floor((distance % (1000 * 60)) / 1000);
        var progress = Math.round((totalSeconds - distance) / totalSeconds * 100, 2);

        if (hours < 10)
            hour_string = "0" + hours;
        else
            hour_string = hours;
        if (minutes < 10)
            min_string = "0" + minutes;
        else
            min_string = minutes;
        if (seconds < 10)
            sec_string = "0" + seconds;
        else
            sec_string = seconds;

        object.innerText = hour_string + ":"
            + min_string + ":" + sec_string;

        object.style.width = progress + "%";
        object.setAttribute("aria-valuenow", progress);

        // If the countdown is finished, write some text
        if (distance < 0) {
            clearInterval(x);
            window.location.href = "{% url 'home' %}";
        }
    }, 1000);
}