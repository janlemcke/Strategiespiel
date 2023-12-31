class TownUI {
    constructor(pk, townAPI) {
        this.pk = pk;
        this.townAPI = townAPI;
    }

    resources = [];
    capacity = 300;

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === name + "=") {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    updateBuildingsUpgradabilityUI(data) {
        for (let i = 0; i < data.length; i++) {
            this.updateBuildingUpgradabilityUI(data[i]);
        }
    }

    updateBuildingUpgradabilityBtnAndTooltip(upgrade_button, tooltip_upgrade_btn, building, current_level) {
        if (building.can_upgrade) {
            upgrade_button.classList.remove("btn-disabled");
            tooltip_upgrade_btn.setAttribute("data-tip", "Ausbauen auf Level " + (current_level + 1));
        } else {
            upgrade_button.classList.add("btn-disabled");
            if (Object.keys(building.needed_resources).length === 0) {
                if (current_level === 20) {
                    tooltip_upgrade_btn.setAttribute("data-tip", "Maximales Level erreicht");
                } else {
                    tooltip_upgrade_btn.setAttribute("data-tip", "Der Ausbau ist noch nicht fertig.");
                }
            } else {
                const tooltip_text = "Es fehlt: " + Object.keys(building.needed_resources).map(function (key) {
                    // Translate key in german
                    let word = "";
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

    updateBuildingUpgradabilityUI(building) {
        const building_element = document.querySelector('#' + building.name);
        const level_element = building_element.querySelector('#building-lvl');
        const upgrade_button = building_element.querySelector('#upgrade-button');
        const tooltip_upgrade_btn = building_element.querySelector('#tooltip-upgrade-btn');
        const current_level = parseInt(level_element.textContent.slice(-1));
        this.updateBuildingUpgradabilityBtnAndTooltip(upgrade_button, tooltip_upgrade_btn, building, current_level);
    }

    updateBuildingsUI(data) {
        // iterate over the data
        for (let i = 0; i < data.length; i++) {
            this.updateBuildingUI(data[i]);
        }
    }

    updateBuildingUI(building) {
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
            this.countdown(building.name, progress_bar, tooltip_progress, building.construction_started_at, building.construction_finished_at);
        }

        this.updateBuildingUpgradabilityBtnAndTooltip(upgrade_button, tooltip_upgrade_btn, building, building.level);

        upgrade_button.onclick = () => {
            // send the upgrade request
            fetch('/api/town/' + this.pk + '/buildings/' + building.name + '/upgrade', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken'),
                },
            })
                .then(response => response.json())
                .then(data => {
                    this.townAPI.updateResources();
                    this.townAPI.updateBuildings();
                })
                .catch(error => {
                    // Handle errors
                    console.error('Error upgrading building:', error);
                });
        }
    }

    updateResourcesUI(data) {
        const join_items = document.querySelector(".navbar").querySelectorAll('.join-item');

        this.resources = data.resources;
        this.capacity = data.capacity;

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

    countdown(building_name, progress_bar, tooltip, startDate, endDate) {
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
            this.townAPI.updateBuildings();
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

    updateUnitCostsUI(data) {
        const training_table_header = document.querySelector('#barrack-header').querySelectorAll('th');
        const unit_inputs = document.querySelectorAll('.unit-input');
        const train_btn = document.querySelector('#train-btn');
        const total_costs_element = document.querySelector('#training-costs');

        let wood_cost = 0;
        let stone_cost = 0;
        let gold_cost = 0;
        let tools_cost = 0;
        let resources = this.resources.map((item) => item[0]);

        for (let i = 0; i < data["costs"].length; i++) {
            let unit_costs = data["costs"][i];
            training_table_header[i].innerHTML += "<br><small>Kosten: " + unit_costs.join(", ") + "</small>";
            unit_inputs[i].onchange = () => {
                calculateTotalCosts(); // Call a function to calculate and update the total costs
            }
        }

        function calculateTotalCosts() {
            wood_cost = 0;
            stone_cost = 0;
            gold_cost = 0;
            tools_cost = 0;

            for (let i = 0; i < data["costs"].length; i++) {
                const unit_costs = data["costs"][i];
                const amount = parseInt(unit_inputs[i].value);

                wood_cost += amount * unit_costs[0];
                stone_cost += amount * unit_costs[1];
                gold_cost += amount * unit_costs[2];
                tools_cost += amount * unit_costs[3];
            }

            total_costs_element.innerHTML = "Gesamtkosten: " + wood_cost + " Holz, " + stone_cost + " Stein, " + gold_cost + " Gold, " + tools_cost + " Werkzeuge";
            train_btn.disabled = wood_cost > resources[0] || stone_cost > resources[1] || gold_cost > resources[2] || tools_cost > resources[3];
        }

        train_btn.onclick = () => {
            const unit_amounts = [];
            for (let i = 0; i < data["costs"].length; i++) {
                const amount = parseInt(unit_inputs[i].value);
                unit_inputs[i].value = 0;
                unit_amounts.push(amount);

            }
            wood_cost = 0;
            stone_cost = 0;
            gold_cost = 0;
            tools_cost = 0;
            total_costs_element.innerHTML = "Gesamtkosten: " + wood_cost + " Holz, " + stone_cost + " Stein, " + gold_cost + " Gold, " + tools_cost + " Werkzeuge";

            fetch('/api/town/' + this.pk + '/barracks/train', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken'),
                },
                body: JSON.stringify({
                    unit_amounts: unit_amounts,
                })
            })
                .then(response => response.json())
                .then(data => {
                    this.townAPI.updateResources();
                })
                .catch(error => {
                    // Handle errors
                    console.error('Error training units:', error);
                });
        }
    }

}