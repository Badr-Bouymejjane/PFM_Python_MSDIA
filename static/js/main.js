/**
 * Course Recommendation System - Main JavaScript
 */

// ===== API Functions =====

/**
 * Search courses by query
 */
async function searchCourses(query, n = 12) {
    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, n })
        });
        return await response.json();
    } catch (error) {
        console.error('Search error:', error);
        return { recommendations: [], error: error.message };
    }
}

/**
 * Get similar courses
 */
async function getSimilarCourses(courseId, n = 6) {
    try {
        const response = await fetch(`/api/recommend/${courseId}?n=${n}`);
        return await response.json();
    } catch (error) {
        console.error('Recommend error:', error);
        return { recommendations: [], error: error.message };
    }
}

/**
 * Get courses with filters
 */
async function getCourses(params = {}) {
    try {
        const queryString = new URLSearchParams(params).toString();
        const response = await fetch(`/api/courses?${queryString}`);
        return await response.json();
    } catch (error) {
        console.error('Get courses error:', error);
        return { courses: [], total: 0, error: error.message };
    }
}

/**
 * Get popular courses
 */
async function getPopularCourses(n = 10, category = null) {
    try {
        let url = `/api/popular?n=${n}`;
        if (category) url += `&category=${category}`;
        const response = await fetch(url);
        return await response.json();
    } catch (error) {
        console.error('Popular error:', error);
        return { courses: [], error: error.message };
    }
}

/**
 * Get statistics
 */
async function getStats() {
    try {
        const response = await fetch('/api/stats');
        return await response.json();
    } catch (error) {
        console.error('Stats error:', error);
        return {};
    }
}

// ===== UI Functions =====

/**
 * Show loading indicator
 */
function showLoading(elementId = 'loading') {
    const loading = document.getElementById(elementId);
    if (loading) loading.classList.add('active');
}

/**
 * Hide loading indicator
 */
function hideLoading(elementId = 'loading') {
    const loading = document.getElementById(elementId);
    if (loading) loading.classList.remove('active');
}

/**
 * Display courses in grid
 */
function displayCourses(courses, gridId = 'courses-grid') {
    const grid = document.getElementById(gridId);
    if (!grid) return;
    
    grid.innerHTML = '';
    
    if (!courses || courses.length === 0) {
        grid.innerHTML = '<p class="no-results">Aucun cours trouvé</p>';
        return;
    }
    
    courses.forEach(course => {
        const card = createCourseCard(course);
        grid.innerHTML += card;
    });
}

/**
 * Create course card HTML
 */
function createCourseCard(course) {
    const platform = (course.platform || 'unknown').toLowerCase();
    
    // Determine logo path
    let logoHtml = '';
    if (platform === 'coursera') {
        logoHtml = `<img src="/static/imgs/coursera-logo.png" alt="Coursera" class="course-logo">`;
    } else if (platform === 'udemy') {
        logoHtml = `<img src="/static/imgs/logo-udemy.svg" alt="Udemy" class="course-logo">`;
    } else {
        // Fallback for other platforms
        logoHtml = `<div class="course-platform ${platform}">${course.platform || 'Unknown'}</div>`;
    }

    const similarity = course.similarity_score ? `
        <div class="similarity-bar-container">
            <div class="similarity-bar">
                <div class="similarity-fill" style="width: ${course.similarity_score}%"></div>
            </div>
        </div>
    ` : '';
    
    return `
        <div class="course-card" onclick="window.location.href='/course/${course.course_id || 0}'">
            ${logoHtml}
            <h3 class="course-title">${truncate(course.title, 60)}</h3>
            <p class="course-instructor"><i data-lucide="user"></i> ${course.instructor || 'N/A'}</p>
            ${similarity}
            <div class="course-meta">
                <span class="meta-badge rating"><i data-lucide="star"></i> ${(course.rating || 0).toFixed(1)}</span>
                <span class="meta-badge level"><i data-lucide="trending-up"></i> ${course.level || 'Tout niveau'}</span>
                <span class="meta-badge category"><i data-lucide="tag"></i> ${course.category || ''}</span>
            </div>
            <div class="course-footer">
                <span class="course-link">Détails →</span>
            </div>
        </div>
    `;
}

/**
 * Truncate text
 */
function truncate(text, maxLength) {
    if (!text) return 'N/A';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

/**
 * Update statistics in navbar
 */
async function updateNavStats() {
    const stats = await getStats();
    const totalCoursesEl = document.getElementById('total-courses');
    if (totalCoursesEl) {
        totalCoursesEl.textContent = stats.total_courses || 0;
    }
}

// ===== Event Listeners =====

document.addEventListener('DOMContentLoaded', function() {
    // Update nav stats
    updateNavStats();
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});

// ===== Export for use in templates =====
window.CourseRecommender = {
    searchCourses,
    getSimilarCourses,
    getCourses,
    getPopularCourses,
    getStats,
    showLoading,
    hideLoading,
    displayCourses,
    createCourseCard,
    truncate
};
