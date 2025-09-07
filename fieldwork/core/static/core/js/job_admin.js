document.addEventListener('DOMContentLoaded', function() {
    const customerSelect = document.getElementById('id_customer');
    const startTimeSelect = document.getElementById('id_start_time');
    const endTimeSelect = document.getElementById('id_end_time');

    // Exit if any of the required elements are not on the page.
    if (!customerSelect || !startTimeSelect || !endTimeSelect) {
        return;
    }

    let customerDurations = {};
    try {
        // The data-durations attribute holds a JSON string mapping customer IDs to their default job duration in minutes.
        customerDurations = JSON.parse(customerSelect.dataset.durations);
    } catch (e) {
        console.error("Could not parse customer durations data from the 'data-durations' attribute.", e);
        return;
    }

    /**
     * Calculates and sets the end time based on the selected customer's default duration and the selected start time.
     */
    function updateEndTime() {
        const customerId = customerSelect.value;
        const duration = customerDurations[customerId]; // Duration in minutes
        const startTime = startTimeSelect.value; // Format "HH:MM:SS"

        // We need all three values to proceed.
        if (!customerId || !duration || !startTime) {
            return;
        }

        // --- Time Calculation ---
        const timeParts = startTime.split(':');
        const hours = parseInt(timeParts[0], 10);
        const minutes = parseInt(timeParts[1], 10);

        // Use a dummy date object to safely perform time calculations.
        const date = new Date(2000, 0, 1, hours, minutes);
        date.setMinutes(date.getMinutes() + duration);

        const endHours = String(date.getHours()).padStart(2, '0');
        const endMinutes = String(date.getMinutes()).padStart(2, '0');

        // The TimeSelectWidget uses values in "HH:MM:SS" format.
        const newEndTimeValue = `${endHours}:${endMinutes}:00`;

        // --- Update End Time Dropdown ---
        // Find the option that matches the calculated time and select it.
        for (let i = 0; i < endTimeSelect.options.length; i++) {
            if (endTimeSelect.options[i].value === newEndTimeValue) {
                endTimeSelect.options[i].selected = true;
                break;
            }
        }
    }

    // Add event listeners to trigger the update function whenever the customer or start time changes.
    customerSelect.addEventListener('change', updateEndTime);
    startTimeSelect.addEventListener('change', updateEndTime);

    // Run the function once on page load to set the initial end time if a customer is already selected.
    updateEndTime();
});
