document.addEventListener('DOMContentLoaded', function() {
    console.log("[Job Admin] DOMContentLoaded: Script starting.");

    const customerSelect = document.getElementById('id_customer');
    const startTimeSelect = document.getElementById('id_start_time');
    const endTimeSelect = document.getElementById('id_end_time');

    if (!customerSelect || !startTimeSelect || !endTimeSelect) {
        console.error("[Job Admin] Error: One or more required form elements not found. Exiting.");
        return;
    }
    console.log("[Job Admin] All form elements found successfully.");

    let customerDurations = {};
    try {
        const durationsData = customerSelect.dataset.durations;
        console.log("[Job Admin] Raw data-durations attribute:", durationsData);
        if (!durationsData) {
            throw new Error("data-durations attribute is empty or missing.");
        }
        customerDurations = JSON.parse(durationsData);
        console.log("[Job Admin] Parsed customer durations:", customerDurations);
    } catch (e) {
        console.error("[Job Admin] Error parsing customer durations data:", e);
        return;
    }

    function updateEndTime() {
        console.log("[Job Admin] updateEndTime() called.");

        const customerId = customerSelect.value;
        const duration = customerDurations[customerId];
        const startTime = startTimeSelect.value;

        console.log(`[Job Admin] Current values: customerId='${customerId}', duration='${duration}', startTime='${startTime}'`);

        if (!customerId || !duration || !startTime) {
            console.log("[Job Admin] Not enough info to calculate end time. Aborting update.");
            return;
        }

        console.log("[Job Admin] Calculating new end time...");
        const timeParts = startTime.split(':');
        const hours = parseInt(timeParts[0], 10);
        const minutes = parseInt(timeParts[1], 10);

        const date = new Date(2000, 0, 1, hours, minutes);
        date.setMinutes(date.getMinutes() + duration);

        const endHours = String(date.getHours()).padStart(2, '0');
        const endMinutes = String(date.getMinutes()).padStart(2, '0');

        const newEndTimeValue = `${endHours}:${endMinutes}:00`;
        console.log(`[Job Admin] Calculated newEndTimeValue: '${newEndTimeValue}'`);

        let optionFound = false;
        for (let i = 0; i < endTimeSelect.options.length; i++) {
            if (endTimeSelect.options[i].value === newEndTimeValue) {
                endTimeSelect.options[i].selected = true;
                optionFound = true;
                console.log(`[Job Admin] Found and selected matching option in end_time dropdown.`);
                break;
            }
        }

        if (!optionFound) {
            console.warn(`[Job Admin] Warning: Could not find an option with value '${newEndTimeValue}' in the end_time dropdown.`);
        }
    }

    console.log("[Job Admin] Attaching event listeners...");
    customerSelect.addEventListener('change', updateEndTime);
    startTimeSelect.addEventListener('change', updateEndTime);

    console.log("[Job Admin] Performing initial call to updateEndTime()...");
    updateEndTime();
    console.log("[Job Admin] Script initialization complete.");
});
