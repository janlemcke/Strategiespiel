function getCookie(name) {
    // Split cookie string and get all individual name=value pairs in an array
    var cookieArr = document.cookie.split(";");

    // Loop through the array elements
    for (var i = 0; i < cookieArr.length; i++) {
        var cookiePair = cookieArr[i].split("=");

        /* Removing whitespace at the beginning of the cookie name
        and compare it with the given string */
        if (name == cookiePair[0].trim()) {
            // Decode the cookie value and return
            return decodeURIComponent(cookiePair[1]);
        }
    }

    // Return null if not found
    return null;
}

function updateResources(pk) {
    fetch('/api/town/' + pk + '/resources')
        .then(response => response.json())
        .then(data => {
            // Update the UI with the new resource values
            updateResourcesUI(data);
            updateBuildingsUpgradability(pk);
        })
        .catch(error => {
            // Handle errors
            console.error('Error fetching resources:', error);
        });
}

function updateBuildingsUpgradability(pk) {
    fetch('/api/town/' + pk + '/buildings/upgradable')
        .then(response => response.json())
        .then(data => {
            // Update the UI with the new resource values
            updateBuildingsUpgradabilityUI(pk, data);
        })
        .catch(error => {
            // Handle errors
            console.error('Error fetching buildings upgradable:', error);
        });

}

function updateBuildingsUpgradabilityUI(pk, data) {
    // iterate over the data
    for (let i = 0; i < data.length; i++) {
        updateBuildingUpgradabilityUI(pk, data[i]);
    }
}

function updateBuildingUpgradabilityBtnAndTooltip(upgrade_button, tooltip_upgrade_btn, building, current_level) {
    if (building.can_upgrade) {
        upgrade_button.classList.remove("btn-disabled");
        tooltip_upgrade_btn.setAttribute("data-tip", "Ausbauen auf Level " + (current_level + 1));
    } else {
        upgrade_button.classList.add("btn-disabled");
        if (Object.keys(building.needed_resources).length === 0) {
            tooltip_upgrade_btn.setAttribute("data-tip", "Maximales Level erreicht");
        } else {
            const tooltip_text = "Es fehlt: " + Object.keys(building.needed_resources).map(function (key) {
                // Translate key in german
                if (key === "wood") {
                    word = "Holz";
                } else if (key === "stone") {
                    word = "Stein";
                } else if (key === "gold") {
                    word = "Gold";
                } else if (key === "tools") {
                    word = "Werkzeuge";
                }
                return building.needed_resources[key] + " " + word;
            }).join(", ");
            tooltip_upgrade_btn.setAttribute("data-tip", tooltip_text);
        }
    }
}

function updateBuildingUpgradabilityUI(pk, building) {
    const building_element = document.querySelector('#' + building.name);
    const level_element = building_element.querySelector('#building-lvl');
    const upgrade_button = building_element.querySelector('#upgrade-button');
    const tooltip_upgrade_btn = building_element.querySelector('#tooltip-upgrade-btn');
    const current_level = parseInt(level_element.textContent.slice(-1));
    updateBuildingUpgradabilityBtnAndTooltip(upgrade_button, tooltip_upgrade_btn, building, current_level);
}

function updateBuildings(pk) {
    fetch('/api/town/' + pk + '/buildings')
        .then(response => response.json())
        .then(data => {
            // Update the UI with the new resource values
            updateBuildingsUI(pk, data);
        })
        .catch(error => {
            // Handle errors
            console.error('Error fetching buildings:', error);
        });
}

function updateBuildingsUI(pk, data) {
    // iterate over the data
    for (let i = 0; i < data.length; i++) {
        updateBuildingUI(pk, data[i]);
    }
}

function updateBuildingUI(pk, building) {
    const building_element = document.querySelector('#' + building.name);
    const building_lvl_element = building_element.querySelector('#building-lvl');
    const upgrade_button = building_element.querySelector('#upgrade-button');
    const progress_bar = building_element.querySelector('.progress');
    const tooltip_progress = building_element.querySelector('#tooltip-progress');
    const tooltip_upgrade_btn = building_element.querySelector('#tooltip-upgrade-btn');


    building_lvl_element.textContent = building.level;

    if (building.under_construction === false) {
        progress_bar.classList.add("hidden");
        upgrade_button.classList.remove("btn-disabled");
    } else {
        upgrade_button.classList.add("btn-disabled");
        progress_bar.classList.remove("hidden");
        countdown(pk, building.name, progress_bar, tooltip_progress, building.construction_started_at, building.construction_finished_at);
    }

    updateBuildingUpgradabilityBtnAndTooltip(upgrade_button, tooltip_upgrade_btn, building, building.level);

    upgrade_button.onclick = function () {
        // send the upgrade request
        fetch('/api/town/' + pk + '/buildings/' + building.name + '/upgrade', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
        })
            .then(response => response.json())
            .then(data => {
                updateResources(pk);
                updateBuildings(pk, building.name);
            })
            .catch(error => {
                // Handle errors
                console.error('Error upgrading building:', error);
            });
    }
}


function updateResourcesUI(data) {
    const join_items = document.querySelector(".navbar").querySelectorAll('.join-item');

    for (let i = 0; i < join_items.length; i++) {
        const item = join_items[i];
        const tooltip = item.querySelector('.tooltip');
        const progress = item.querySelector('.radial-progress');

        const resource = data.resources[i][0];

        const percentage = Math.round(resource / data.capacity * 100);

        progress.style.setProperty("--value", percentage);
        progress.innerHTML = "<small>" + resource + "</small>";

        if (resource === data.capacity) {
            progress.classList.add("text-error");
        } else {
            progress.classList.remove("text-error");
        }

        progress.classList.add("animate-pulse");
        tooltip.setAttribute("data-tip", "Voll in " + data.resources[i][1]);

        setTimeout(() => {
            progress.classList.remove("animate-pulse");
        }, 2 * 1000);
    }
}

function countdown(pk, building_name, progress_bar, tooltip, startDate, endDate) {
    endDate = new Date(endDate);
    startDate = new Date(startDate);
    var totalSeconds = endDate - startDate + 5 * 1000;

    const updateProgressBar = () => {
        const now = new Date(new Date().getTime() + (new Date().getTimezoneOffset() * 60000));
        const distance = endDate - now;

        // Time calculations for days, hours, minutes and seconds
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);
        const progress = Math.round((totalSeconds - distance) / totalSeconds * 100);

        const padZero = (value) => (value < 10 ? "0" + value : value);

        const hourString = padZero(hours);
        const minString = padZero(minutes);
        const secString = padZero(seconds);

        const text = `${hourString}:${minString}:${secString}`;

        progress_bar.value = progress;
        tooltip.setAttribute("data-tip", text);
    };

    const updateUIAndClearInterval = () => {
        clearInterval(x);
        updateBuildings(pk, building_name);
    };

    const x = setInterval(() => {
        const now = new Date(new Date().getTime() + (new Date().getTimezoneOffset() * 60000));
        const distance = endDate - now;
        if (distance <= 0) {
            updateUIAndClearInterval(distance);
        } else {
            updateProgressBar();
        }
    }, 1000);
}