document.addEventListener('DOMContentLoaded', function () {
    const section = "settings";
    const el = document.getElementById(`${section}`);
    if (el) {
        el.classList.add('active');
    }
});

class SettingsManager {
    constructor() {
        this.originalData = null;
        this.isLoading = false;
        this.init();
    }

    init() {
        // Mark active navigation item
        const settingsNav = document.getElementById('settings');
        if (settingsNav) {
            settingsNav.classList.add('active');
        }

        this.bindEvents();
        this.loadSettings();
    }

    bindEvents() {
        // Form submission
        const form = document.getElementById('settingsForm');
        form.addEventListener('submit', (e) => this.handleSubmit(e));

        // Reset button
        const resetBtn = document.getElementById('resetButton');
        resetBtn.addEventListener('click', () => this.resetForm());

        // Integration toggles
        this.setupIntegrationToggles();
    }

    setupIntegrationToggles() {
        // MangaUpdates toggle
        const muToggle = document.getElementById('muIntegration');
        const muFields = document.getElementById('muFields');

        muToggle.addEventListener('change', () => {
            muFields.style.display = muToggle.checked ? 'block' : 'none';
            this.updateRequiredFields();
        });

        // MangaDex toggle
        const dexToggle = document.getElementById('dexIntegration');
        const dexFields = document.getElementById('dexFields');

        dexToggle.addEventListener('change', () => {
            dexFields.style.display = dexToggle.checked ? 'block' : 'none';
            this.updateRequiredFields();
        });

        // MyAnimeList toggle (only affects automation visibility, not Client ID)
        const malToggle = document.getElementById('malIntegration');
        const malFields = document.getElementById('malFields');

        malToggle.addEventListener('change', () => {
            malFields.style.display = malToggle.checked ? 'block' : 'none';
        });
    }

    updateRequiredFields() {
        // MangaUpdates: Username always required when enabled, password conditional
        const muEnabled = document.getElementById('muIntegration').checked;
        const muUsername = document.getElementById('muUsername');
        const muPassword = document.getElementById('muPassword');
        const muPasswordRequired = document.getElementById('muPasswordRequired');

        if (muEnabled) {
            muUsername.setAttribute('required', 'required');

            // Password only required if not previously saved (API returns false)
            const muPasswordSaved = this.originalData?.mu_password === true;
            if (!muPasswordSaved) {
                muPassword.setAttribute('required', 'required');
                muPasswordRequired.style.display = 'inline';
            } else {
                muPassword.removeAttribute('required');
                muPasswordRequired.style.display = 'none';
            }
        } else {
            muUsername.removeAttribute('required');
            muPassword.removeAttribute('required');
            muPasswordRequired.style.display = 'inline'; // Show when disabled (default state)
        }

        // MangaDex: Username and Client ID always required when enabled, password and secret conditional
        const dexEnabled = document.getElementById('dexIntegration').checked;
        const dexUsername = document.getElementById('dexUsername');
        const dexPassword = document.getElementById('dexPassword');
        const dexClientId = document.getElementById('dexClientId');
        const dexSecret = document.getElementById('dexSecret');
        const dexPasswordRequired = document.getElementById('dexPasswordRequired');
        const dexSecretRequired = document.getElementById('dexSecretRequired');

        if (dexEnabled) {
            dexUsername.setAttribute('required', 'required');
            dexClientId.setAttribute('required', 'required');

            // Password only required if not previously saved (API returns false)
            const dexPasswordSaved = this.originalData?.dex_password === true;
            if (!dexPasswordSaved) {
                dexPassword.setAttribute('required', 'required');
                dexPasswordRequired.style.display = 'inline';
            } else {
                dexPassword.removeAttribute('required');
                dexPasswordRequired.style.display = 'none';
            }

            // Secret only required if not previously saved (API returns false)
            const dexSecretSaved = this.originalData?.dex_secret === true;
            if (!dexSecretSaved) {
                dexSecret.setAttribute('required', 'required');
                dexSecretRequired.style.display = 'inline';
            } else {
                dexSecret.removeAttribute('required');
                dexSecretRequired.style.display = 'none';
            }
        } else {
            dexUsername.removeAttribute('required');
            dexPassword.removeAttribute('required');
            dexClientId.removeAttribute('required');
            dexSecret.removeAttribute('required');
            dexPasswordRequired.style.display = 'inline'; // Show when disabled (default state)
            dexSecretRequired.style.display = 'inline'; // Show when disabled (default state)
        }
    }

    setupFormValidation() {
        const titleLanguagesInput = document.getElementById('titleLanguages');
        const dexClientIdInput = document.getElementById('dexClientId');

        // Title languages validation
        titleLanguagesInput.addEventListener('input', (e) => {
            const value = e.target.value;
            const pattern = /^[a-z]{2}(,[a-z]{2})*$/;

            if (value && !pattern.test(value)) {
                e.target.setCustomValidity('Please enter valid ISO 639-1 language codes (e.g., en,tr,de)');
            } else {
                e.target.setCustomValidity('');
            }
        });

        // MangaDex Client ID validation
        dexClientIdInput.addEventListener('input', (e) => {
            const value = e.target.value;
            const pattern = /^personal-client-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

            if (value && !pattern.test(value)) {
                e.target.setCustomValidity('Client ID must be in format: personal-client-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx');
            } else {
                e.target.setCustomValidity('');
            }
        });

        // Real-time validation feedback
        const form = document.getElementById('settingsForm');
        const inputs = form.querySelectorAll('input, select');

        inputs.forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('input', () => {
                if (input.classList.contains('error')) {
                    this.validateField(input);
                }
            });
        });
    }

    validateField(field) {
        const isValid = field.checkValidity();

        if (isValid) {
            field.classList.remove('error');
            this.clearFieldError(field);
        } else {
            field.classList.add('error');
            this.showFieldError(field, field.validationMessage);
        }

        return isValid;
    }

    showFieldError(field, message) {
        this.clearFieldError(field);

        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error';
        errorDiv.textContent = message;

        field.parentNode.appendChild(errorDiv);
    }

    clearFieldError(field) {
        const existingError = field.parentNode.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }
    }

    async loadSettings() {
        try {
            this.showLoading(true);
            this.hideError();

            const response = await fetch('/api/v1/settings', {
                method: 'GET',
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();

            if (result.result === 'OK') {
                this.originalData = result.data;
                this.populateForm(result.data);
                this.showForm();
            } else {
                throw new Error(result.error || 'Failed to load settings');
            }

        } catch (error) {
            console.error('Error loading settings:', error);
            this.showError(`Failed to load settings: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }

    populateForm(data) {
        // General settings
        document.getElementById('mainRating').value = data.main_rating || 'mu';
        document.getElementById('titleLanguages').value = data.title_languages || '';

        // MangaUpdates
        const muIntegration = document.getElementById('muIntegration');
        const muFields = document.getElementById('muFields');

        muIntegration.checked = data.mu_integration || false;
        muFields.style.display = muIntegration.checked ? 'block' : 'none';

        if (data.mu_username) {
            document.getElementById('muUsername').value = data.mu_username;
        }

        // Set placeholder for MU password based on saved state
        const muPasswordField = document.getElementById('muPassword');
        if (data.mu_password === true) {
            muPasswordField.placeholder = '••••••••';
            muPasswordField.title = 'Password is already saved. Leave empty to keep current password.';
        } else {
            muPasswordField.placeholder = 'Enter MangaUpdates password';
            muPasswordField.title = '';
        }

        document.getElementById('muAutomation').checked = data.mu_automation || false;

        // MU Lists mapping
        if (data.mu_lists) {
            document.getElementById('muListPlanTo').value = data.mu_lists['plan-to'] || 102;
            document.getElementById('muListReading').value = data.mu_lists.reading || 0;
            document.getElementById('muListCompleted').value = data.mu_lists.completed || 2;
            document.getElementById('muListOneShots').value = data.mu_lists['one-shots'] || 101;
            document.getElementById('muListDropped').value = data.mu_lists.dropped || 3;
            document.getElementById('muListOnHold').value = data.mu_lists['on-hold'] || 4;
            document.getElementById('muListOngoing').value = data.mu_lists.ongoing || 1;
        }

        // MangaDex
        const dexIntegration = document.getElementById('dexIntegration');
        const dexFields = document.getElementById('dexFields');

        dexIntegration.checked = data.dex_integration || false;
        dexFields.style.display = dexIntegration.checked ? 'block' : 'none';

        if (data.dex_username) {
            document.getElementById('dexUsername').value = data.dex_username;
        }
        if (data.dex_client_id) {
            document.getElementById('dexClientId').value = data.dex_client_id;
        }

        // Set placeholder for MangaDex password based on saved state
        const dexPasswordField = document.getElementById('dexPassword');
        if (data.dex_password === true) {
            dexPasswordField.placeholder = '••••••••';
            dexPasswordField.title = 'Password is already saved. Leave empty to keep current password.';
        } else {
            dexPasswordField.placeholder = 'Enter MangaDex password';
            dexPasswordField.title = '';
        }

        // Set placeholder for MangaDex secret based on saved state
        const dexSecretField = document.getElementById('dexSecret');
        if (data.dex_secret === true) {
            dexSecretField.placeholder = '••••••••••••••••';
            dexSecretField.title = 'Client secret is already saved. Leave empty to keep current secret.';
        } else {
            dexSecretField.placeholder = 'Enter MangaDex client secret';
            dexSecretField.title = '';
        }

        document.getElementById('dexAutomation').checked = data.dex_automation || false;
        document.getElementById('dexFetchIds').checked = data.dex_fetch_ids || false;
        document.getElementById('dexForced').checked = data.dex_integration_forced || false;

        // MyAnimeList - Client ID always visible, integration fields conditional
        if (data.mal_client_id) {
            document.getElementById('malClientId').value = data.mal_client_id;
        }

        const malIntegration = document.getElementById('malIntegration');
        const malFields = document.getElementById('malFields');

        malIntegration.checked = data.mal_integration || false;
        malFields.style.display = malIntegration.checked ? 'block' : 'none';

        document.getElementById('malAutomation').checked = data.mal_automation || false;

        // Update required fields based on integration states
        this.updateRequiredFields();
    }

    // Helper function to check if a value is not empty
    hasValue(value) {
        return value !== null && value !== undefined && value !== '';
    }

    // Helper function to build data object with only non-empty values
    buildSettingsData(formData) {
        const settings = {};

        // Always include these basic fields
        settings.main_rating = formData.get('main_rating');

        // Only include if has value
        const titleLanguages = formData.get('title_languages');
        if (this.hasValue(titleLanguages)) {
            settings.title_languages = titleLanguages;
        }

        // MangaUpdates integration
        settings.mu_integration = formData.has('mu_integration');
        if (settings.mu_integration) {
            settings.mu_automation = formData.has('mu_automation');

            // Username always required when integration is enabled
            const muUsername = formData.get('mu_username');
            if (this.hasValue(muUsername)) {
                settings.mu_username = muUsername;
            }

            // Password only included if user provided it (not required if already saved)
            const muPassword = formData.get('mu_password');
            if (this.hasValue(muPassword)) {
                settings.mu_password = muPassword;
            }
        }

        // MU Lists - only include if any values are provided
        const muLists = {};
        const listFields = [
            { key: 'plan-to', field: 'mu_list_plan_to', default: 102 },
            { key: 'reading', field: 'mu_list_reading', default: 0 },
            { key: 'completed', field: 'mu_list_completed', default: 2 },
            { key: 'one-shots', field: 'mu_list_one_shots', default: 101 },
            { key: 'dropped', field: 'mu_list_dropped', default: 3 },
            { key: 'on-hold', field: 'mu_list_on_hold', default: 4 },
            { key: 'ongoing', field: 'mu_list_ongoing', default: 1 }
        ];

        let hasListValues = false;
        listFields.forEach(({ key, field, default: defaultValue }) => {
            const value = formData.get(field);
            if (this.hasValue(value)) {
                muLists[key] = parseInt(value);
                hasListValues = true;
            } else if (settings.mu_integration) {
                muLists[key] = defaultValue;
                hasListValues = true;
            }
        });

        if (hasListValues) {
            settings.mu_lists = muLists;
        }

        // MangaDex integration
        settings.dex_integration = formData.has('dex_integration');
        settings.dex_fetch_ids = formData.has('dex_fetch_ids');
        if (settings.dex_integration) {
            settings.dex_automation = formData.has('dex_automation');
            settings.dex_integration_forced = formData.has('dex_integration_forced');

            // Username and Client ID always required when integration is enabled
            const dexUsername = formData.get('dex_username');
            const dexClientId = formData.get('dex_client_id');
            if (this.hasValue(dexUsername)) {
                settings.dex_username = dexUsername;
            }
            if (this.hasValue(dexClientId)) {
                settings.dex_client_id = dexClientId;
            }

            // Password and Secret only included if user provided them (not required if already saved)
            const dexPassword = formData.get('dex_password');
            const dexSecret = formData.get('dex_secret');
            if (this.hasValue(dexPassword)) {
                settings.dex_password = dexPassword;
            }
            if (this.hasValue(dexSecret)) {
                settings.dex_secret = dexSecret;
            }
        }

        // MyAnimeList integration
        settings.mal_integration = formData.has('mal_integration');
        if (settings.mal_integration) {
            settings.mal_automation = formData.has('mal_automation');
        }

        // MAL Client ID - always include if provided (even if integration is off)
        const malClientId = formData.get('mal_client_id');
        if (this.hasValue(malClientId)) {
            settings.mal_client_id = malClientId;
        }

        // Password change - only include if provided
        const newPassword = formData.get('new_password');
        if (this.hasValue(newPassword)) {
            settings.password = newPassword;
        }

        return settings;
    }

    async handleSubmit(e) {
        e.preventDefault();

        if (this.isLoading) return;

        const form = e.target;
        const formData = new FormData(form);

        // Validate all fields
        const inputs = form.querySelectorAll('input, select');
        let isValid = true;

        inputs.forEach(input => {
            if (!this.validateField(input)) {
                isValid = false;
            }
        });

        if (!isValid) {
            this.showMessage('Please fix the validation errors before saving.', 'error');
            return;
        }

        try {
            this.setLoading(true);

            // Build settings object with only non-empty values
            const settings = this.buildSettingsData(formData);

            const response = await fetch('/api/v1/settings', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(settings)
            });

            if (response.ok) {
                this.showMessage('Settings saved successfully! 🎉', 'success');

                // Update original data to reflect changes
                this.originalData = { ...this.originalData, ...settings };
                delete this.originalData.password; // Don't store passwords

                // Clear sensitive fields that were just saved
                document.getElementById('newPassword').value = '';
                document.getElementById('muPassword').value = '';
                document.getElementById('dexPassword').value = '';
                document.getElementById('dexSecret').value = '';

            } else {
                const result = await response.json();
                throw new Error(result.error || `HTTP ${response.status}: ${response.statusText}`);
            }

        } catch (error) {
            console.error('Error saving settings:', error);
            this.showMessage(`Failed to save settings: ${error.message}`, 'error');
        } finally {
            this.setLoading(false);
        }
    }

    resetForm() {
        if (this.originalData) {
            this.populateForm(this.originalData);

            // Clear all sensitive fields
            document.getElementById('newPassword').value = '';
            document.getElementById('muPassword').value = '';
            document.getElementById('dexPassword').value = '';
            document.getElementById('dexSecret').value = '';

            // Clear validation errors
            const form = document.getElementById('settingsForm');
            const errorFields = form.querySelectorAll('.error');
            errorFields.forEach(field => {
                field.classList.remove('error');
                this.clearFieldError(field);
            });

            this.showMessage('Changes have been reset.', 'info');
        }
    }

    setLoading(loading) {
        this.isLoading = loading;
        const saveBtn = document.getElementById('saveButton');
        const spinner = saveBtn.querySelector('.loading-spinner');
        const text = saveBtn.querySelector('.button-text');

        if (loading) {
            saveBtn.disabled = true;
            spinner.classList.remove('hidden');
            text.textContent = 'Saving...';
        } else {
            saveBtn.disabled = false;
            spinner.classList.add('hidden');
            text.textContent = 'Save Settings';
        }
    }

    showLoading(show) {
        const loadingSpinner = document.getElementById('loadingSpinner');
        const errorContainer = document.getElementById('errorContainer');
        const settingsForm = document.getElementById('settingsForm');

        if (show) {
            loadingSpinner.classList.remove('hidden');
            errorContainer.classList.add('hidden');
            settingsForm.classList.add('hidden');
        } else {
            loadingSpinner.classList.add('hidden');
        }
    }

    showForm() {
        const settingsForm = document.getElementById('settingsForm');
        settingsForm.classList.remove('hidden');
    }

    showError(message) {
        const errorContainer = document.getElementById('errorContainer');
        const errorText = document.getElementById('errorText');

        errorText.textContent = message;
        errorContainer.classList.remove('hidden');
    }

    hideError() {
        const errorContainer = document.getElementById('errorContainer');
        errorContainer.classList.add('hidden');
    }

    showMessage(message, type = 'success') {
        const container = document.getElementById('messageContainer');

        // Clear existing messages
        container.innerHTML = '';

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;

        const icon = type === 'success' ? '✅' :
                    type === 'error' ? '❌' :
                    type === 'info' ? 'ℹ️' : '⚠️';

        messageDiv.innerHTML = `
            <span class="message-icon">${icon}</span>
            <span class="message-text">${message}</span>
        `;

        container.appendChild(messageDiv);

        // Auto-hide after 5 seconds for success/info messages
        if (type === 'success' || type === 'info') {
            setTimeout(() => {
                messageDiv.remove();
            }, 5000);
        }

        // Scroll message into view
        messageDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new SettingsManager();
});
