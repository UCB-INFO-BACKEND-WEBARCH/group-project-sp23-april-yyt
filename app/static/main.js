
// Function to handle form submission
function submitForm(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);

    // Show the loading indicator
    document.getElementById('loading-indicator').style.display = 'block';

    // Send the form data to your Flask route
    fetch(form.action, {
        method: form.method,
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        const task_id = data.task_id;
        const user_id = data.user_id;

        // Check the task status every 5 seconds
        const interval = setInterval(() => {
            checkTaskStatus(task_id, (completed) => {
                if (completed) {
                    // If the task is completed, stop checking the status
                    clearInterval(interval);
                    // Hide the loading indicator
                    document.getElementById('loading-indicator').style.display = 'none';
                    // Redirect to the success.html page or update the page with the result
                    window.location.href = '/success/${user_id}/${task_id}';
                }
            });
        }, 5000);
    })
    .catch(error => {
        console.error('Error submitting the form:', error);
    });

}

// Function to check the task status
function checkTaskStatus(task_id, callback) {
    fetch('/check_task_status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `task_id=${task_id}`,
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'completed') {
            // Handle the completed task
            callback(true);
        } else {
            // Handle the in-progress task
            console.log('Task in progress. Current state:', data.current_state);
            callback(false);
        }
    })
    .catch(error => {
        console.error('Error checking task status:', error);
    });
}

// Add an event listener to the form submission
const form = document.querySelector('form');
form.addEventListener('submit', submitForm);
