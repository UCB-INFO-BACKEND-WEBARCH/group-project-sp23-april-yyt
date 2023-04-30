// Replace `task_id` with the actual task ID you get from calling the task
const task_id = "your_task_id_here";

function checkTaskStatus() {
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
            console.log('Task completed:', data.result);
            // Redirect to the success/viz page or update the page with the result
            // window.location.href = '/success';
        } else {
            // Handle the in-progress task
            console.log('Task in progress. Current state:', data.current_state);
        }
    })
    .catch(error => {
        console.error('Error checking task status:', error);
    });
}