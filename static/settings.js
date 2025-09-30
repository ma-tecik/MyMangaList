document.addEventListener('DOMContentLoaded', function () {
    const section = "settings";
    const el = document.getElementById(`${section}`);
    if (el) {
        el.classList.add('active');
    }

    // Load settings from API
    loadSettings();

    // Setup event listeners
    setupEventListeners();

    function loadSettings() {
        fetch('/api/v1/settings')
            .then(response => response.json())
            .then(data => {
                if (data.result === 'OK' && data.data) {
                    populateForm(data.data);
                } else {
                    showStatus('Failed to load settings', 'error');
                }
            })
            .catch(error => {
                console.error('Error loading settings:', error);
                showStatus('Failed to load settings', 'error');
            });
    }

    function populateForm(settings) {
        // General settings
        document.getElementById('main_rating').value = settings.main_rating || 'mu';
        document.getElementById('title_languages').value = settings.title_languages || '';

        // MangaUpdates integration
        const muIntegration = document.getElementById('mu_integration');
        muIntegration.checked = !!settings.mu_integration;
        document.getElementById('mu_username').value = settings.mu_username || '';
        document.getElementById('mu_password').value = settings.mu_password || '';

        // Mangadex integration
        const dexIntegration = document.getElementById('dex_integration');
        dexIntegration.checked = !!settings.dex_integration;
        document.getElementById('dex_token').value = settings.dex_token || '';

        // MyAnimeList integration
        document.getElementById('mal_integration').checked = !!settings.mal_integration;

        // Update credential visibility
        toggleCredentials();
    }

    function setupEventListeners() {
        // Toggle credential fields visibility
        document.getElementById('mu_integration').addEventListener('change', toggleCredentials);
        document.getElementById('dex_integration').addEventListener('change', toggleCredentials);

        // Form submission
        document.getElementById('settingsForm').addEventListener('submit', handleFormSubmit);
    }

    function toggleCredentials() {
        const muIntegration = document.getElementById('mu_integration').checked;
        const dexIntegration = document.getElementById('dex_integration').checked;

        // Toggle MangaUpdates credentials
        document.querySelectorAll('.mu-credentials').forEach(el => {
            el.style.display = muIntegration ? 'block' : 'none';
        });

        // Toggle Mangadex credentials
        document.querySelectorAll('.dex-credentials').forEach(el => {
            el.style.display = dexIntegration ? 'block' : 'none';
        });
    }

    function handleFormSubmit(e) {
        e.preventDefault();

        const saveBtn = document.getElementById('saveBtn');
        const btnText = saveBtn.querySelector('.btn-text');
        const btnLoader = saveBtn.querySelector('.btn-loader');

        // Show loading state
        btnText.style.opacity = '0';
        btnLoader.classList.remove('hidden');
        saveBtn.disabled = true;

        // Collect form data
        const formData = {
            main_rating: document.getElementById('main_rating').value,
            title_languages: document.getElementById('title_languages').value,
            mu_integration: document.getElementById('mu_integration').checked,
            mu_username: document.getElementById('mu_username').value,
            mu_password: document.getElementById('mu_password').value,
            dex_integration: document.getElementById('dex_integration').checked,
            dex_token: document.getElementById('dex_token').value,
            mal_integration: document.getElementById('mal_integration').checked
        };

        // Send to API
        fetch('/api/v1/settings', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        })
        .then(response => {
            if (response.status === 204) {
                showStatus('Settings saved successfully!', 'success');
            } else {
                return response.json().then(data => {
                    throw new Error(data.message || 'Failed to save settings');
                });
            }
        })
        .catch(error => {
            console.error('Error saving settings:', error);
            showStatus(error.message || 'Failed to save settings', 'error');
        })
        .finally(() => {
            // Reset button state
            btnText.style.opacity = '1';
            btnLoader.classList.add('hidden');
            saveBtn.disabled = false;
        });
    }

    function showStatus(message, type) {
        const statusEl = document.getElementById('statusMessage');
        statusEl.textContent = message;
        statusEl.className = `status-message ${type}`;

        // Auto-hide after 5 seconds
        setTimeout(() => {
            statusEl.textContent = '';
            statusEl.className = 'status-message';
        }, 5000);
    }
});