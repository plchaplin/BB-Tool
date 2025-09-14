document.addEventListener('DOMContentLoaded', function() {
    const customerSelect = document.getElementById('id_customer');
    const durationSelect = document.getElementById('id_duration');

    if (!customerSelect || !durationSelect) {
        return; // Exit if elements aren't on the page
    }

    // Create a span for the indicator message and add it after the dropdown
    const indicator = document.createElement('span');
    indicator.className = 'ms-2 fst-italic'; // Bootstrap margin and italic style
    durationSelect.parentElement.appendChild(indicator);

    let customerDurations = {};
    try {
        customerDurations = JSON.parse(customerSelect.dataset.durations);
    } catch (e) {
        console.error("Could not parse customer durations data.", e);
        return;
    }

    function updateDurationIndicator() {
        const customerId = customerSelect.value;
        if (!customerId) {
            indicator.textContent = '';
            return;
        }

        const defaultDuration = customerDurations[customerId];
        const selectedDuration = parseInt(durationSelect.value, 10);

        if (!defaultDuration) {
            indicator.textContent = '';
            return;
        }

        if (selectedDuration === defaultDuration) {
            indicator.textContent = '(Matches customer default)';
            indicator.className = 'ms-2 fst-italic text-muted';
        } else {
            const difference = selectedDuration - defaultDuration;
            if (difference > 0) {
                indicator.textContent = `(${difference} minutes above default)`;
                indicator.className = 'ms-2 fst-italic text-warning';
            } else {
                indicator.textContent = `(${Math.abs(difference)} minutes below default)`;
                indicator.className = 'ms-2 fst-italic text-warning';
            }
        }
    }

    function handleCustomerChange() {
        // When a customer is selected, set the duration to their default.
        // This is primarily for the "Add Job" screen.
        const customerId = customerSelect.value;
        if (customerId) {
            const defaultDuration = customerDurations[customerId];
            if (defaultDuration) {
                durationSelect.value = defaultDuration;
            }
        }
        // Always update the indicator text after a customer change.
        updateDurationIndicator();
    }

    // Attach event listeners
    customerSelect.addEventListener('change', handleCustomerChange);
    durationSelect.addEventListener('change', updateDurationIndicator);

    // Initial call to set the indicator state correctly on page load (for existing jobs)
    updateDurationIndicator();
});
