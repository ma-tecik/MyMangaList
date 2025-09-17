// Tab Navigation
class TabManager {
    constructor() {
        this.externalTab = document.getElementById('tab-external');
        this.manualTab = document.getElementById('tab-manual');
        this.externalContent = document.getElementById('external-tab');
        this.manualContent = document.getElementById('manual-tab');

        this.init();
    }

    init() {
        this.externalTab.addEventListener('click', () => this.switchTab('external'));
        this.manualTab.addEventListener('click', () => this.switchTab('manual'));
    }

    switchTab(tab) {
        if (tab === 'external') {
            this.externalTab.classList.add('active');
            this.manualTab.classList.remove('active');
            this.externalContent.classList.add('active');
            this.manualContent.classList.remove('active');
        } else {
            this.manualTab.classList.add('active');
            this.externalTab.classList.remove('active');
            this.manualContent.classList.add('active');
            this.externalContent.classList.remove('active');
        }
    }
}

// Message Manager
class MessageManager {
    constructor() {
        this.successElement = document.getElementById('success-message');
        this.errorElement = document.getElementById('error-message');
    }

    showSuccess(message) {
        this.hideAll();
        this.successElement.textContent = message;
        this.successElement.classList.remove('hidden');
        this.scrollToMessage();
    }

    showError(message) {
        this.hideAll();
        this.errorElement.textContent = message;
        this.errorElement.classList.remove('hidden');
        this.scrollToMessage();
    }

    hideAll() {
        this.successElement.classList.add('hidden');
        this.errorElement.classList.add('hidden');
    }

    scrollToMessage() {
        setTimeout(() => {
            const messageElement = !this.successElement.classList.contains('hidden')
                ? this.successElement
                : this.errorElement;
            messageElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);
    }
}

// External Data Fetcher
class ExternalDataFetcher {
    constructor(messageManager) {
        this.messageManager = messageManager;
        this.fetchButton = document.getElementById('fetch-data-btn');
        this.fetchedDataSection = document.getElementById('fetched-data-section');
        this.fetchedDataForm = document.getElementById('fetched-data-form');

        this.init();
    }

    init() {
        this.fetchButton.addEventListener('click', () => this.fetchExternalData());
    }

    async fetchExternalData() {
        const formData = new FormData(document.getElementById('external-form'));
        const params = new URLSearchParams();

        // Collect external IDs
        ['mu', 'dex', 'mal', 'bato', 'line'].forEach(provider => {
            const value = formData.get(provider);
            if (value && value.trim()) {
                params.append(provider, value.trim());
            }
        });

        if (params.toString() === '') {
            this.messageManager.showError('Please enter at least one external ID');
            return;
        }

        this.setLoading(true);
        this.messageManager.hideAll();

        try {
            const response = await fetch(`/api/v1/external/series/data?${params.toString()}`);
            const data = await response.json();

            if (response.ok && data.result === 'OK') {
                this.populateFetchedForm(data.data);
                this.fetchedDataSection.classList.remove('hidden');
                this.messageManager.showSuccess('Series data fetched successfully! Review and edit as needed.');
            } else {
                this.messageManager.showError(data.error || 'Failed to fetch series data');
            }
        } catch (error) {
            this.messageManager.showError('Network error: ' + error.message);
        } finally {
            this.setLoading(false);
        }
    }

    populateFetchedForm(seriesData) {
        const form = this.fetchedDataForm;
        form.innerHTML = '';

        // Create form fields based on fetched data
        const fields = [
            { name: 'title', label: 'Title *', type: 'text', value: seriesData.title || '', required: true },
            { name: 'alt_titles', label: 'Alternative Titles', type: 'text', value: (seriesData.alt_titles || []).join(', ') },
            { name: 'type', label: 'Type *', type: 'select', value: seriesData.type || '', required: true, options: ['Manga', 'Manhwa', 'Manhua', 'OEL', 'Vietnamese', 'Malaysian', 'Indonesian', 'Novel', 'Artbook', 'Other'] },
            { name: 'status', label: 'Reading Status *', type: 'select', value: seriesData.status || 'plan-to', required: true, options: ['plan-to', 'reading', 'completed', 'one-shot', 'dropped', 'on-hold', 'ongoing'] },
            { name: 'year', label: 'Year', type: 'number', value: seriesData.year || '' },
            { name: 'description', label: 'Description', type: 'textarea', value: seriesData.description || '' },
            { name: 'vol_ch', label: 'Volume/Chapter Info', type: 'text', value: seriesData.vol_ch || '' },
            { name: 'is_md', label: 'Description is in Markdown format', type: 'checkbox', value: seriesData.is_md || false },
            { name: 'genres', label: 'Genres', type: 'text', value: (seriesData.genres || []).join(', ') },
            { name: 'authors', label: 'Authors', type: 'text', value: this.formatAuthors(seriesData.authors || []) },
            { name: 'thumbnail', label: 'Thumbnail URL *', type: 'url', value: seriesData.thumbnail || '', required: true }
        ];

        const grid = document.createElement('div');
        grid.className = 'form-grid';

        fields.forEach(field => {
            const group = document.createElement('div');
            group.className = field.name === 'title' || field.name === 'alt_titles' || field.name === 'description' || field.name === 'genres' || field.name === 'authors' || field.name === 'thumbnail' ? 'form-group full-width' : 'form-group';

            if (field.type === 'checkbox') {
                group.className += ' checkbox-group';
                group.innerHTML = `
                    <label for="fetched-${field.name}" class="checkbox-label">
                        <input type="checkbox" id="fetched-${field.name}" name="${field.name}" ${field.value ? 'checked' : ''}>
                        <span class="checkmark"></span>
                        ${field.label}
                    </label>
                `;
            } else {
                const label = document.createElement('label');
                label.htmlFor = `fetched-${field.name}`;
                label.textContent = field.label;

                let input;
                if (field.type === 'select') {
                    input = document.createElement('select');
                    input.innerHTML = field.options.map(opt =>
                        `<option value="${opt}" ${opt === field.value ? 'selected' : ''}>${this.formatOptionText(opt)}</option>`
                    ).join('');
                } else if (field.type === 'textarea') {
                    input = document.createElement('textarea');
                    input.rows = 4;
                    input.value = field.value;
                } else {
                    input = document.createElement('input');
                    input.type = field.type;
                    input.value = field.value;
                    if (field.type === 'number') {
                        input.min = '1900';
                        input.max = '2030';
                    }
                }

                input.id = `fetched-${field.name}`;
                input.name = field.name;
                if (field.required) input.required = true;

                group.appendChild(label);
                group.appendChild(input);
            }

            grid.appendChild(group);
        });

        const submitButton = document.createElement('button');
        submitButton.type = 'submit';
        submitButton.className = 'primary-button';
        submitButton.innerHTML = `
            <span class="button-text">Add Series</span>
            <div class="loading-spinner hidden"></div>
        `;

        form.appendChild(grid);
        form.appendChild(submitButton);

        // Add form submission handler
        form.addEventListener('submit', (e) => this.submitFetchedData(e));
    }

    formatAuthors(authors) {
        return authors.map(author => author.name || author).join(', ');
    }

    formatOptionText(value) {
        const statusMap = {
            'plan-to': 'Plan to Read',
            'reading': 'Reading',
            'completed': 'Completed',
            'one-shot': 'One-shot',
            'dropped': 'Dropped',
            'on-hold': 'On Hold',
            'ongoing': 'Ongoing'
        };
        return statusMap[value] || value;
    }

    async submitFetchedData(event) {
        event.preventDefault();

        const formData = new FormData(event.target);
        const payload = this.buildSeriesPayload(formData);

        // Add external IDs from the original form
        const externalFormData = new FormData(document.getElementById('external-form'));
        payload.ids = {};
        ['mu', 'dex', 'mal', 'bato', 'line'].forEach(provider => {
            const value = externalFormData.get(provider);
            if (value && value.trim()) {
                payload.ids[provider] = provider === 'mal' || provider === 'bato'
                    ? parseInt(value.trim())
                    : value.trim();
            }
        });

        await this.submitSeries(payload, event.target);
    }

    buildSeriesPayload(formData) {
        const payload = {};

        for (let [key, value] of formData.entries()) {
            if (key === 'alt_titles' || key === 'genres') {
                payload[key] = value ? value.split(',').map(v => v.trim()).filter(Boolean) : [];
            } else if (key === 'authors') {
                payload[key] = value ? value.split(',').map(name => ({
                    name: name.trim(),
                    type: 'Author'
                })).filter(author => author.name) : [];
            } else if (key === 'is_md') {
                payload[key] = formData.has('is_md');
            } else if (key === 'year') {
                payload[key] = value ? parseInt(value) : null;
            } else if (value !== '') {
                payload[key] = value;
            }
        }

        return payload;
    }

    async submitSeries(payload, form) {
        const submitButton = form.querySelector('button[type="submit"]');
        this.setButtonLoading(submitButton, true);
        this.messageManager.hideAll();

        try {
            const response = await fetch('/api/v1/series', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok && data.result === 'OK') {
                this.messageManager.showSuccess('Series added successfully!');
                // Reset forms
                document.getElementById('external-form').reset();
                this.fetchedDataSection.classList.add('hidden');
            } else if (response.status === 409) {
                this.messageManager.showError('Series already exists. ' + (data.error || ''));
            } else {
                this.messageManager.showError(data.error || 'Failed to add series');
            }
        } catch (error) {
            this.messageManager.showError('Network error: ' + error.message);
        } finally {
            this.setButtonLoading(submitButton, false);
        }
    }

    setLoading(loading) {
        const button = this.fetchButton;
        this.setButtonLoading(button, loading);
    }

    setButtonLoading(button, loading) {
        const spinner = button.querySelector('.loading-spinner');
        const text = button.querySelector('.button-text');

        if (loading) {
            button.disabled = true;
            spinner.classList.remove('hidden');
            text.style.opacity = '0.7';
        } else {
            button.disabled = false;
            spinner.classList.add('hidden');
            text.style.opacity = '1';
        }
    }
}

// Manual Form Handler
class ManualFormHandler {
    constructor(messageManager) {
        this.messageManager = messageManager;
        this.form = document.getElementById('manual-form');

        this.init();
    }

    init() {
        this.form.addEventListener('submit', (e) => this.submitManualData(e));
    }

    async submitManualData(event) {
        event.preventDefault();

        const formData = new FormData(event.target);
        const payload = this.buildSeriesPayload(formData);

        // Empty external IDs for manual entry
        payload.ids = {};

        const submitButton = event.target.querySelector('button[type="submit"]');
        this.setButtonLoading(submitButton, true);
        this.messageManager.hideAll();

        try {
            const response = await fetch('/api/v1/series', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok && data.result === 'OK') {
                this.messageManager.showSuccess('Series added successfully!');
                this.form.reset();
            } else if (response.status === 409) {
                this.messageManager.showError('Series already exists. ' + (data.error || ''));
            } else {
                this.messageManager.showError(data.error || 'Failed to add series');
            }
        } catch (error) {
            this.messageManager.showError('Network error: ' + error.message);
        } finally {
            this.setButtonLoading(submitButton, false);
        }
    }

    buildSeriesPayload(formData) {
        const payload = {};

        for (let [key, value] of formData.entries()) {
            if (key === 'alt_titles' || key === 'genres') {
                payload[key] = value ? value.split(',').map(v => v.trim()).filter(Boolean) : [];
            } else if (key === 'authors') {
                payload[key] = value ? value.split(',').map(name => ({
                    name: name.trim(),
                    type: 'Author'
                })).filter(author => author.name) : [];
            } else if (key === 'is_md') {
                payload[key] = formData.has('is_md');
            } else if (key === 'year') {
                payload[key] = value ? parseInt(value) : null;
            } else if (value !== '') {
                payload[key] = value;
            }
        }

        return payload;
    }

    setButtonLoading(button, loading) {
        const spinner = button.querySelector('.loading-spinner');
        const text = button.querySelector('.button-text');

        if (loading) {
            button.disabled = true;
            spinner.classList.remove('hidden');
            text.style.opacity = '0.7';
        } else {
            button.disabled = false;
            spinner.classList.add('hidden');
            text.style.opacity = '1';
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const messageManager = new MessageManager();
    const tabManager = new TabManager();
    const externalDataFetcher = new ExternalDataFetcher(messageManager);
    const manualFormHandler = new ManualFormHandler(messageManager);
});

