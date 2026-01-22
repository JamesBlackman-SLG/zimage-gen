// Z-Image Web UI

const API_BASE = '';
let currentOffset = 0;
const PAGE_SIZE = 20;

// DOM Elements
const form = document.getElementById('generate-form');
const generateBtn = document.getElementById('generate-btn');
const btnText = generateBtn.querySelector('.btn-text');
const btnLoading = generateBtn.querySelector('.btn-loading');
const progressContainer = document.getElementById('progress-container');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');
const resultContainer = document.getElementById('result-container');
const resultImage = document.getElementById('result-image');
const resultSeed = document.getElementById('result-seed');
const downloadLink = document.getElementById('download-link');
const errorContainer = document.getElementById('error-container');
const errorMessage = document.getElementById('error-message');
const galleryGrid = document.getElementById('gallery-grid');
const loadMoreBtn = document.getElementById('load-more');
const modal = document.getElementById('modal');
const modalImage = document.getElementById('modal-image');
const modalPrompt = document.getElementById('modal-prompt');
const modalMeta = document.getElementById('modal-meta');
const modalClose = document.querySelector('.modal-close');

// State
let isGenerating = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadGallery();
    setupEventListeners();
});

function setupEventListeners() {
    form.addEventListener('submit', handleGenerate);
    loadMoreBtn.addEventListener('click', () => loadGallery(true));
    modalClose.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });
}

async function handleGenerate(e) {
    e.preventDefault();
    if (isGenerating) return;

    const prompt = document.getElementById('prompt').value.trim();
    const width = parseInt(document.getElementById('width').value) || 2048;
    const height = parseInt(document.getElementById('height').value) || 2048;
    const seedInput = document.getElementById('seed').value;
    const seed = seedInput ? parseInt(seedInput) : null;

    if (!prompt) {
        showError('Please enter a prompt');
        return;
    }

    setGenerating(true);
    hideError();
    hideResult();
    showProgress();

    try {
        // Start generation task
        const response = await fetch(`${API_BASE}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt, width, height, seed }),
        });

        if (!response.ok) {
            throw new Error('Failed to start generation');
        }

        const { task_id } = await response.json();

        // Connect to WebSocket for progress
        await connectWebSocket(task_id);

    } catch (error) {
        showError(error.message);
        setGenerating(false);
        hideProgress();
    }
}

function connectWebSocket(taskId) {
    return new Promise((resolve, reject) => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const ws = new WebSocket(`${protocol}//${window.location.host}/ws/progress/${taskId}`);

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);

            switch (data.type) {
                case 'started':
                    updateProgress(0, 'Starting generation...');
                    break;

                case 'progress':
                    updateProgress(data.percent, `Step ${data.step}/${data.total}`);
                    break;

                case 'completed':
                    updateProgress(100, 'Complete!');
                    showResult(data.image_id, data.seed);
                    setGenerating(false);
                    loadGallery(); // Refresh gallery
                    ws.close();
                    resolve();
                    break;

                case 'error':
                    showError(data.message);
                    setGenerating(false);
                    hideProgress();
                    ws.close();
                    reject(new Error(data.message));
                    break;
            }
        };

        ws.onerror = () => {
            showError('WebSocket connection error');
            setGenerating(false);
            hideProgress();
            reject(new Error('WebSocket error'));
        };

        ws.onclose = () => {
            if (isGenerating) {
                showError('Connection closed unexpectedly');
                setGenerating(false);
                hideProgress();
            }
        };
    });
}

function setGenerating(state) {
    isGenerating = state;
    generateBtn.disabled = state;
    btnText.hidden = state;
    btnLoading.hidden = !state;
}

function showProgress() {
    progressContainer.hidden = false;
    updateProgress(0, 'Initializing...');
}

function hideProgress() {
    progressContainer.hidden = true;
}

function updateProgress(percent, text) {
    progressFill.style.width = `${percent}%`;
    progressText.textContent = text;
}

function showResult(imageId, seed) {
    const imageUrl = `${API_BASE}/images/${imageId}`;
    resultImage.src = imageUrl;
    resultSeed.textContent = seed;
    downloadLink.href = imageUrl;
    downloadLink.download = `zimage-${seed}.png`;
    resultContainer.hidden = false;
}

function hideResult() {
    resultContainer.hidden = true;
}

function showError(message) {
    errorMessage.textContent = message;
    errorContainer.hidden = false;
}

function hideError() {
    errorContainer.hidden = true;
}

async function loadGallery(append = false) {
    if (!append) {
        currentOffset = 0;
        galleryGrid.innerHTML = '';
    }

    try {
        const response = await fetch(`${API_BASE}/images?limit=${PAGE_SIZE}&offset=${currentOffset}`);
        if (!response.ok) return;

        const data = await response.json();

        data.images.forEach(img => {
            const item = createGalleryItem(img);
            galleryGrid.appendChild(item);
        });

        currentOffset += data.images.length;
        loadMoreBtn.hidden = currentOffset >= data.total;

    } catch (error) {
        console.error('Failed to load gallery:', error);
    }
}

function createGalleryItem(img) {
    const div = document.createElement('div');
    div.className = 'gallery-item';
    div.innerHTML = `
        <img src="${API_BASE}/images/${img.id}" alt="${escapeHtml(img.prompt)}" loading="lazy">
        <div class="overlay">${escapeHtml(truncate(img.prompt, 50))}</div>
    `;
    div.addEventListener('click', () => openModal(img));
    return div;
}

function openModal(img) {
    modalImage.src = `${API_BASE}/images/${img.id}`;
    modalPrompt.textContent = img.prompt;
    modalMeta.textContent = `${img.width}x${img.height} | Seed: ${img.seed} | ${formatDate(img.created_at)}`;
    modal.hidden = false;
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    modal.hidden = true;
    document.body.style.overflow = '';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncate(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function formatDate(isoString) {
    return new Date(isoString).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });
}
