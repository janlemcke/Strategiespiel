class TownAPI {

    constructor(pk) {
        this.pk = pk;
        this.townUI = new TownUI(pk, this);

        this.loadedUnitCosts = false;

        this.updateResources();
        this.updateBuildings();
    }

    updateResources(pk) {
        fetch('/api/town/' + this.pk + '/resources')
            .then(response => response.json())
            .then(data => {
                // Update the UI with the new resource values
                this.townUI.updateResourcesUI(data);
                this.updateBuildingsUpgradability();
                if(!this.loadedUnitCosts){
                    this.loadUnitCosts();
                    this.loadedUnitCosts = true;
                }

            })
            .catch(error => {
                // Handle errors
                console.error('Error fetching resources:', error);
            });
    }

    updateBuildings() {
        fetch('/api/town/' + this.pk + '/buildings')
            .then(response => response.json())
            .then(data => {
                // Update the UI with the new resource values
                this.townUI.updateBuildingsUI(data);
            })
            .catch(error => {
                // Handle errors
                console.error('Error fetching buildings:', error);
            });
    }

    updateBuildingsUpgradability() {
        fetch('/api/town/' + this.pk + '/buildings/upgradable')
            .then(response => response.json())
            .then(data => {
                // Update the UI with the new resource values
                this.townUI.updateBuildingsUpgradabilityUI(data);
            })
            .catch(error => {
                // Handle errors
                console.error('Error fetching buildings upgradable:', error);
            });

    }

    loadUnitCosts() {
        fetch('/api/town/unit/costs')
            .then(response => response.json())
            .then(data => {
                this.townUI.updateUnitCostsUI(data);
            })
            .catch(error => {
                // Handle errors
                console.error('Error fetching unit costs:', error);
            });
    }
}