// JS for Login page only

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const errorMessage = document.getElementById('error-message');
    const loginBtn = loginForm.querySelector('.login-btn');

    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Disable button and show loading state
        loginBtn.disabled = true;
        loginBtn.textContent = 'Logging in...';

        // Hide any previous error messages
        errorMessage.classList.add('hidden');

        const formData = new FormData();
        formData.append('password', document.getElementById('password').value);

        try {
            const response = await fetch('/api/v1/login', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok && data.result === 'OK') {
                // Login successful, redirect to main page
                window.location.href = '/';
            } else {
                // Show error message
                errorMessage.textContent = data.error || 'Login failed';
                errorMessage.classList.remove('hidden');
            }
        } catch (error) {
            console.error('Login error:', error);
            errorMessage.textContent = 'Connection error. Please try again.';
            errorMessage.classList.remove('hidden');
        } finally {
            // Re-enable button
            loginBtn.disabled = false;
            loginBtn.textContent = 'Login';
        }
    });

    // Clear error message when user starts typing
    document.getElementById('password').addEventListener('input', function() {
        if (!errorMessage.classList.contains('hidden')) {
            errorMessage.classList.add('hidden');
        }
    });
});
