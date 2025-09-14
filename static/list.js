// JS for List page only

// Global state
let currentStatus = '';
let currentType = 'all';
let currentSort = '';
let includedGenres = [];
let excludedGenres = ['nsfw']; // Default excluded
let currentPage = 1;

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Get status from URL path
    const path = window.location.pathname;
    const statusMatch = path.match(/\/series\/(.+)/);
    if (statusMatch) {
        currentStatus = statusMatch[1];
    }

    // Parse URL parameters
    parseURLParams();

    // Initialize UI state
    initializeUI();

    // Load data
    loadSeriesData();
});

function parseURLParams() {
    const urlParams = new URLSearchParams(window.location.search);

    // Get type from URL
    const typeParam = urlParams.get('type');
    if (typeParam) {
        currentType = typeParam;
    }
}

function initializeUI() {
    // Set active type button
    document.querySelectorAll('.type-button').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.type === currentType) {
            btn.classList.add('active');
        }
    });

    // Set sort dropdown
    const sortSelect = document.getElementById('sortSelect');
    sortSelect.value = currentSort;

    // Initialize NSFW as excluded by default
    const nsfwButton = document.querySelector('[data-filter="nsfw"]');
    if (nsfwButton) {
        nsfwButton.classList.add('excluded');
    }
}

function toggleFilterMenu() {
    const filterMenu = document.getElementById('filterMenu');
    filterMenu.classList.toggle('hidden');
    const mainContent = document.getElementById('mainContent');
    mainContent.classList.toggle('with_filter-menu');
}

function selectType(button) {
    // Remove active class from all type buttons
    document.querySelectorAll('.type-button').forEach(btn => {
        btn.classList.remove('active');
    });

    // Add active class to clicked button
    button.classList.add('active');

    // Update current type
    currentType = button.dataset.type;

    // Update URL and reload data
    updateURLAndReload();
}

function toggleFilter(button) {
    const filterValue = button.dataset.filter || button.dataset.genre;

    if (button.classList.contains('included')) {
        // Switch to excluded
        button.classList.remove('included');
        button.classList.add('excluded');

        // Remove from included, add to excluded
        includedGenres = includedGenres.filter(g => g !== filterValue);
        if (!excludedGenres.includes(filterValue)) {
            excludedGenres.push(filterValue);
        }
    } else if (button.classList.contains('excluded')) {
        // Switch to inactive
        button.classList.remove('excluded');

        // Remove from excluded
        excludedGenres = excludedGenres.filter(g => g !== filterValue);
    } else {
        // Switch to included
        button.classList.add('included');

        // Add to included, remove from excluded
        if (!includedGenres.includes(filterValue)) {
            includedGenres.push(filterValue);
        }
        excludedGenres = excludedGenres.filter(g => g !== filterValue);
    }
}

function handleGenreInput(event) {
    if (event.key === 'Enter') {
        applyFilters();
    }
}

function parseGenreInput() {
    const input = document.getElementById('genreInput').value;
    const genres = input.split(',').map(g => g.trim()).filter(g => g);

    const tempIncluded = [...includedGenres];
    const tempExcluded = [...excludedGenres];

    genres.forEach(genre => {
        if (genre.startsWith('-')) {
            const cleanGenre = genre.substring(1);
            if (!tempExcluded.includes(cleanGenre)) {
                tempExcluded.push(cleanGenre);
            }
            // Remove from included if it's there
            const index = tempIncluded.indexOf(cleanGenre);
            if (index > -1) {
                tempIncluded.splice(index, 1);
            }
        } else {
            if (!tempIncluded.includes(genre)) {
                tempIncluded.push(genre);
            }
            // Remove from excluded if it's there
            const index = tempExcluded.indexOf(genre);
            if (index > -1) {
                tempExcluded.splice(index, 1);
            }
        }
    });

    return { included: tempIncluded, excluded: tempExcluded };
}

function applySorting() {
    const sortSelect = document.getElementById('sortSelect');
    currentSort = sortSelect.value;
    loadSeriesData();
}

function applyFilters() {
    // Parse genre input and combine with button selections
    const parsedGenres = parseGenreInput();
    includedGenres = parsedGenres.included;
    excludedGenres = parsedGenres.excluded;

    // Reset to first page
    currentPage = 1;

    // Load data with filters
    loadSeriesData();
}

function resetFilters() {
    // Reset all filter states
    includedGenres = [];
    excludedGenres = ['nsfw'];
    currentSort = '';
    currentPage = 1;

    // Reset UI
    document.querySelectorAll('.genre-button').forEach(btn => {
        btn.classList.remove('included', 'excluded');
    });

    // Set NSFW as excluded by default
    const nsfwButton = document.querySelector('[data-filter="nsfw"]');
    if (nsfwButton) {
        nsfwButton.classList.add('excluded');
    }

    // Clear input
    document.getElementById('genreInput').value = '';

    // Reset sort
    document.getElementById('sortSelect').value = '';

    // Load data
    loadSeriesData();
}

function updateURLAndReload() {
    const url = new URL(window.location);

    // Update type parameter
    if (currentType === 'all') {
        url.searchParams.delete('type');
    } else {
        url.searchParams.set('type', currentType);
    }

    // Update browser URL
    window.history.pushState({}, '', url);

    // Reset page and reload data
    currentPage = 1;
    loadSeriesData();
}

function loadSeriesData() {
    const loadingSpinner = document.getElementById('loadingSpinner');
    const tableBody = document.getElementById('seriesTableBody');

    // Show loading
    loadingSpinner.classList.remove('hidden');

    // Build API URL
    const apiUrl = buildAPIURL();

    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            if (data.result === 'OK') {
                renderSeriesTable(data.data);
            } else {
                console.error('API Error:', data.error);
                tableBody.innerHTML = '<tr><td colspan="5">Error loading data: ' + data.error + '</td></tr>';
            }
        })
        .catch(error => {
            console.error('Fetch Error:', error);
            tableBody.innerHTML = '<tr><td colspan="5">Error loading data</td></tr>';
        })
        .finally(() => {
            loadingSpinner.classList.add('hidden');
        });
}

function buildAPIURL() {
    const params = new URLSearchParams();

    // Add status (required)
    const statusMap = {
        'plan-to': 'Plan to Read',
        'reading': 'Reading',
        'completed': 'Completed',
        'one-shots': 'One-shot',
        'on-hold': 'On hold',
        'dropped': 'Dropped',
        'ongoing': 'Ongoing'
    };

    const mappedStatus = statusMap[currentStatus];
    if (mappedStatus) {
        params.append('status', mappedStatus);
    }

    // Add type if not 'all'
    if (currentType !== 'all') {
        // Capitalize first letter for API
        const typeForAPI = currentType === 'minor' ? 'minor' :
                          currentType.charAt(0).toUpperCase() + currentType.slice(1);
        params.append('type', typeForAPI);
    }

    // Add included genres
    if (includedGenres.length > 0) {
        params.append('included', includedGenres.join(','));
    }

    // Add excluded genres
    if (excludedGenres.length > 0) {
        params.append('excluded', excludedGenres.join(','));
    }

    // Add sort
    if (currentSort) {
        params.append('sort_by', currentSort);
    }

    // Add pagination
    params.append('page', currentPage.toString());

    return '/api/v1/series?' + params.toString();
}

function renderSeriesTable(seriesData) {
    const tableBody = document.getElementById('seriesTableBody');

    if (!seriesData || seriesData.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5">No series found</td></tr>';
        return;
    }

    tableBody.innerHTML = seriesData.map(series => createSeriesRow(series)).join('');
}

function createSeriesRow(series) {
    const thumbnailUrl = `/static/thumbnails/${series.id}.${series.thumbnail_ext}`;

    // Create title section
    const titleSection = createTitleSection(series);

    // Create genres list
    const genresList = createGenresList(series.genres);

    // Create description (handle markdown)
    const description = createDescription(series.description, series.is_md);

    // Create vol-ch (handle markdown)
    const volCh = createVolCh(series.vol_ch, series.is_md);

    return `
        <tr>
            <td>
                <img src="${thumbnailUrl}" alt="${series.title}" class="thumbnail" 
                     onerror="this.src='/static/thumbnails/default.png'">
            </td>
            <td>${titleSection}</td>
            <td>${genresList}</td>
            <td class="description">${description}</td>
            <td class="vol-ch">${volCh}</td>
        </tr>
    `;
}

function createTitleSection(series) {
    const altTitlesBtn = series.alt_titles && series.alt_titles.length > 0
        ? `<button class="alt-titles-btn" onclick="showAltTitles(${JSON.stringify(series.alt_titles).replace(/"/g, '&quot;')})">A</button>`
        : '';

    const rating =`<div class="rating">★ ${series.rating}</div>`;

    const externalLinks = createExternalLinks(series.ids);

    return `
        <div class="title-section">
            <div class="title-row">
                <span class="series-title">${series.title}</span>
                ${altTitlesBtn}
            </div>
            <hr>
            ${rating}
            <hr>
            <div class="external-links">
                ${externalLinks}
            </div>
        </div>
    `;
}

function createExternalLinks(ids) {
    let links = [];

    if (ids.mu) {
        links.push(`<a href="https://www.mangaupdates.com/series/${ids.mu}" target="_blank">
            <img src="/static/icons/mangaupdates.svg" alt="MU" title="MangaUpdates">
        </a>`);
    }

    if (ids.dex) {
        links.push(`<a href="https://mangadex.org/manga/${ids.dex}" target="_blank">
            <img src="/static/icons/mangadex.svg" alt="Dex" title="MangaDex">
        </a>`);
    }

    if (ids.mal) {
        links.push(`<a href="https://myanimelist.net/manga/${ids.mal}" target="_blank">
            <img src="/static/icons/myanimelist.ico" alt="MAL" title="MyAnimeList">
        </a>`);
    }

    if (ids.bato) {
        links.push(`<a href="https://bato.to/series/${ids.bato}" target="_blank">
            <img src="/static/icons/bato.png" alt="Bato" title="Bato.to">
        </a>`);
    }

    if (ids.line) {
        const lineUrl = ids.line.startsWith('o:')
            ? `https://www.webtoons.com/en/original/${ids.line.substring(2)}`
            : `https://www.webtoons.com/en/canvas/${ids.line.substring(2)}`;
        links.push(`<a href="${lineUrl}" target="_blank">
            <img src="/static/icons/line.png" alt="LINE" title="LINE Webtoon">
        </a>`);
    }

    return links.join('');
}

function createGenresList(genres) {
    if (!genres || genres.length === 0) return '';

    return `
        <div class="genres-list">
            ${genres.map(genre => `<span class="genre-tag">${genre}</span>`).join('')}
        </div>
    `;
}

function createDescription(description, isMarkdown) {
    if (!description) return '';

    if (isMarkdown && typeof marked !== 'undefined') {
        return marked.parse(description);
    }

    return description;
}

function createVolCh(volCh, isMarkdown) {
    if (!volCh) return '';

    if (isMarkdown && typeof marked !== 'undefined') {
        return marked.parse(volCh);
    }

    return volCh;
}

function showAltTitles(altTitles) {
    // Create popup overlay
    const overlay = document.createElement('div');
    overlay.className = 'popup-overlay';
    overlay.onclick = () => closeAltTitles();

    // Create popup content
    const popup = document.createElement('div');
    popup.className = 'alt-titles-popup';
    popup.innerHTML = `
        <h3>Alternative Titles</h3>
        <ul>
            ${altTitles.map(title => `<li>${title}</li>`).join('')}
        </ul>
    `;

    // Add to page
    document.body.appendChild(overlay);
    document.body.appendChild(popup);
}

function closeAltTitles() {
    const overlay = document.querySelector('.popup-overlay');
    const popup = document.querySelector('.alt-titles-popup');

    if (overlay) overlay.remove();
    if (popup) popup.remove();
}
