/**
 * Pinterest Integrator - Material Library
 * JavaScript Application Logic
 */

// ========================================
// Configuration
// ========================================
const CONFIG = {
  // URL to your GitHub library.json
  // For local development:
  libraryUrl: './data/library.json',

  // For production (replace with your GitHub repo):
  // libraryUrl: 'https://raw.githubusercontent.com/USERNAME/REPO/main/data/library.json',

  // For SketchUp WebDialog (file will be bundled):
  // libraryUrl: 'library.json',
};

// ========================================
// State Management
// ========================================
let state = {
  materials: [],
  filteredMaterials: [],
  activeFilter: 'all',
  searchQuery: '',
  isLoading: true,
};

// ========================================
// DOM Elements
// ========================================
const elements = {
  materialsGrid: document.getElementById('materialsGrid'),
  searchInput: document.getElementById('searchInput'),
  filtersContainer: document.getElementById('filtersContainer'),
  materialCount: document.getElementById('materialCount'),
  syncTime: document.getElementById('syncTime'),
  loadingState: document.getElementById('loadingState'),
  toastContainer: document.getElementById('toastContainer'),
  gridViewBtn: document.getElementById('gridViewBtn'),
  listViewBtn: document.getElementById('listViewBtn'),
};

// ========================================
// Data Fetching
// ========================================
async function fetchLibrary() {
  try {
    state.isLoading = true;
    showLoading();

    const response = await fetch(CONFIG.libraryUrl);

    if (!response.ok) {
      throw new Error('Gagal memuat library');
    }

    const data = await response.json();

    state.materials = data.materials || [];
    state.filteredMaterials = [...state.materials];

    // Update sync time
    if (data.last_sync) {
      const syncDate = new Date(data.last_sync);
      elements.syncTime.textContent = `Terakhir sync: ${formatDate(syncDate)}`;
    }

    // Generate filter tags from unique tags in materials
    generateFilterTags();

    // Render materials
    renderMaterials();

    state.isLoading = false;

  } catch (error) {
    console.error('Error fetching library:', error);
    showError('Gagal memuat library. Pastikan file library.json tersedia.');
    state.isLoading = false;
  }
}

// ========================================
// Rendering Functions
// ========================================
function renderMaterials() {
  hideLoading();

  if (state.filteredMaterials.length === 0) {
    elements.materialsGrid.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📭</div>
        <h3 class="empty-title">Tidak ada material ditemukan</h3>
        <p class="empty-text">Coba ubah filter atau kata kunci pencarian Anda</p>
      </div>
    `;
    elements.materialCount.textContent = '0';
    return;
  }

  elements.materialsGrid.innerHTML = state.filteredMaterials
    .map(material => createMaterialCard(material))
    .join('');

  elements.materialCount.textContent = state.filteredMaterials.length;

  // Add click handlers to apply buttons
  document.querySelectorAll('.apply-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const materialId = btn.dataset.id;
      applyMaterial(materialId);
    });
  });

  // Add click handlers to cards
  document.querySelectorAll('.material-card').forEach(card => {
    card.addEventListener('click', () => {
      const materialId = card.dataset.id;
      showMaterialDetails(materialId);
    });
  });
}

function createMaterialCard(material) {
  const tagsHtml = material.tags
    .slice(0, 3)
    .map(tag => `<span class="card-tag">${tag}</span>`)
    .join('');

  return `
    <article class="material-card" data-id="${material.id}">
      <div class="card-image-container">
        <img 
          src="${material.image_url}" 
          alt="${material.title}" 
          class="card-image"
          loading="lazy"
          onerror="this.src='https://via.placeholder.com/400x300?text=Image+Not+Found'"
        >
        <div class="card-overlay">
          <button class="apply-btn" data-id="${material.id}">
            ✨ Terapkan ke SketchUp
          </button>
        </div>
      </div>
      <div class="card-content">
        <h3 class="card-title" title="${material.title}">${material.title}</h3>
        <p class="card-description">${material.description}</p>
        <div class="card-tags">${tagsHtml}</div>
        <div class="card-board">
          <span class="board-icon">📋</span>
          <span>${material.board}</span>
        </div>
      </div>
    </article>
  `;
}

function generateFilterTags() {
  // Get all unique tags from materials
  const allTags = new Set();
  state.materials.forEach(material => {
    material.tags.forEach(tag => allTags.add(tag));
  });

  // Get unique boards
  const boards = new Set(state.materials.map(m => m.board));

  // Create filter buttons for main categories
  const mainCategories = ['kayu', 'batik', 'batu', 'bambu', 'rotan'];
  const categoryTags = mainCategories.filter(cat => allTags.has(cat));

  // Add board filters
  const filtersHtml = categoryTags
    .map(tag => `<button class="filter-tag" data-filter="${tag}">${capitalizeFirst(tag)}</button>`)
    .join('');

  // Insert after the "Semua" button
  const allButton = elements.filtersContainer.querySelector('[data-filter="all"]');
  allButton.insertAdjacentHTML('afterend', filtersHtml);

  // Add event listeners to all filter buttons
  elements.filtersContainer.querySelectorAll('.filter-tag').forEach(btn => {
    btn.addEventListener('click', () => {
      setActiveFilter(btn.dataset.filter);
    });
  });
}

// ========================================
// Filtering & Search
// ========================================
function setActiveFilter(filter) {
  state.activeFilter = filter;

  // Update UI
  elements.filtersContainer.querySelectorAll('.filter-tag').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.filter === filter);
  });

  applyFilters();
}

function applyFilters() {
  let filtered = [...state.materials];

  // Apply tag filter
  if (state.activeFilter !== 'all') {
    filtered = filtered.filter(material =>
      material.tags.includes(state.activeFilter)
    );
  }

  // Apply search filter
  if (state.searchQuery.trim()) {
    const query = state.searchQuery.toLowerCase();
    filtered = filtered.filter(material =>
      material.title.toLowerCase().includes(query) ||
      material.description.toLowerCase().includes(query) ||
      material.tags.some(tag => tag.toLowerCase().includes(query)) ||
      material.board.toLowerCase().includes(query)
    );
  }

  state.filteredMaterials = filtered;
  renderMaterials();
}

// ========================================
// Material Actions
// ========================================
function applyMaterial(materialId) {
  const material = state.materials.find(m => m.id === materialId);

  if (!material) {
    showToast('Material tidak ditemukan', 'error');
    return;
  }

  // This is a placeholder for SketchUp integration
  // In the actual plugin, this would call Ruby functions via sketchup.callback
  console.log('Applying material:', material);

  // Simulate SketchUp integration
  if (typeof sketchup !== 'undefined') {
    // Real SketchUp environment
    sketchup.applyMaterial(JSON.stringify(material));
  } else {
    // Demo mode
    showToast(`✨ Material "${material.title}" siap diterapkan!`, 'success');
  }
}

function showMaterialDetails(materialId) {
  const material = state.materials.find(m => m.id === materialId);

  if (!material) return;

  // For now, open the Pinterest source URL
  if (material.source_url) {
    // In demo mode, just show a toast
    showToast(`📌 ${material.title} - dari board "${material.board}"`, 'success');
  }
}

// ========================================
// UI Helpers
// ========================================
function showLoading() {
  elements.loadingState.style.display = 'flex';
}

function hideLoading() {
  elements.loadingState.style.display = 'none';
}

function showError(message) {
  elements.materialsGrid.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">⚠️</div>
      <h3 class="empty-title">Oops! Terjadi Kesalahan</h3>
      <p class="empty-text">${message}</p>
    </div>
  `;
}

function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${type === 'success' ? '✅' : '❌'}</span>
    <span class="toast-message">${message}</span>
  `;

  elements.toastContainer.appendChild(toast);

  // Auto remove after 3 seconds
  setTimeout(() => {
    toast.style.animation = 'slideIn 0.3s ease reverse';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ========================================
// Utility Functions
// ========================================
function formatDate(date) {
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Baru saja';
  if (diffMins < 60) return `${diffMins} menit lalu`;
  if (diffHours < 24) return `${diffHours} jam lalu`;
  if (diffDays < 7) return `${diffDays} hari lalu`;

  return date.toLocaleDateString('id-ID', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  });
}

function capitalizeFirst(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// ========================================
// Event Listeners
// ========================================
function initEventListeners() {
  // Search input with debounce
  elements.searchInput.addEventListener('input', debounce((e) => {
    state.searchQuery = e.target.value;
    applyFilters();
  }, 300));

  // Clear search on Escape
  elements.searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      elements.searchInput.value = '';
      state.searchQuery = '';
      applyFilters();
    }
  });

  // View toggle buttons (visual only for now)
  elements.gridViewBtn.addEventListener('click', () => {
    elements.gridViewBtn.classList.add('active');
    elements.listViewBtn.classList.remove('active');
    elements.materialsGrid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(280px, 1fr))';
  });

  elements.listViewBtn.addEventListener('click', () => {
    elements.listViewBtn.classList.add('active');
    elements.gridViewBtn.classList.remove('active');
    elements.materialsGrid.style.gridTemplateColumns = '1fr';
  });
}

// ========================================
// SketchUp Bridge Functions
// ========================================
// These functions will be called from Ruby when running in SketchUp

/**
 * Called from Ruby to refresh the material list
 */
function refreshLibrary() {
  fetchLibrary();
}

/**
 * Called from Ruby to update a single material
 */
function updateMaterial(materialJson) {
  try {
    const material = JSON.parse(materialJson);
    const index = state.materials.findIndex(m => m.id === material.id);

    if (index !== -1) {
      state.materials[index] = material;
    } else {
      state.materials.push(material);
    }

    applyFilters();
  } catch (e) {
    console.error('Error updating material:', e);
  }
}

/**
 * Called from Ruby to show a message
 */
function showMessage(message, type = 'success') {
  showToast(message, type);
}

// ========================================
// Initialize App
// ========================================
document.addEventListener('DOMContentLoaded', () => {
  initEventListeners();
  fetchLibrary();
});

// Export for SketchUp bridge
window.PinterestIntegrator = {
  refreshLibrary,
  updateMaterial,
  showMessage,
  applyMaterial,
};
