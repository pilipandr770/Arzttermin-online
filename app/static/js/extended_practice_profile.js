// Extended Practice Profile Management

let practiceData = {};

document.addEventListener('DOMContentLoaded', function() {
    loadExtendedProfile();
    setupFormHandler();
});

async function loadExtendedProfile() {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch('/api/practice/profile', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            practiceData = await response.json();
            populateForm();
            calculateCompleteness();
        } else {
            showAlert('danger', 'Fehler beim Laden des Profils');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('danger', 'Fehler beim Laden des Profils: ' + error.message);
    }
}

function populateForm() {
    // Helper function to safely set value
    const setValueSafe = (id, value) => {
        const element = document.getElementById(id);
        if (element) {
            element.value = value || '';
        }
    };
    
    // Basic fields
    setValueSafe('phone', practiceData.phone);
    setValueSafe('emergency_phone', practiceData.emergency_phone);
    setValueSafe('whatsapp_number', practiceData.whatsapp_number);
    setValueSafe('telegram_username', practiceData.telegram_username);
    setValueSafe('contact_email', practiceData.contact_email);
    setValueSafe('website', practiceData.website);
    
    // Google Business
    setValueSafe('google_business_url', practiceData.google_business_url);
    
    // Social media
    const social = practiceData.social_media || {};
    setValueSafe('social_facebook', social.facebook);
    setValueSafe('social_instagram', social.instagram);
    setValueSafe('social_linkedin', social.linkedin);
    setValueSafe('social_twitter', social.twitter);
    setValueSafe('social_youtube', social.youtube);
    setValueSafe('social_tiktok', social.tiktok);
    
    // Media
    setValueSafe('video_url', practiceData.video_url);
    setValueSafe('virtual_tour_url', practiceData.virtual_tour_url);
    
    // Services
    const services = practiceData.services || [];
    loadServices(services);
    
    // Equipment
    const equipment = practiceData.equipment || [];
    loadEquipment(equipment);
    
    // Insurances
    const insurances = practiceData.accepted_insurances || [];
    loadInsurances(insurances);
    
    // Features
    const features = practiceData.features || [];
    loadFeatures(features);
    
    // Chatbot instructions
    setValueSafe('chatbot_instructions', practiceData.chatbot_instructions);
}

// Gallery Photos
function loadGalleryPhotos(photos) {
    const container = document.getElementById('gallery-photos-list');
    container.innerHTML = '';
    
    photos.forEach(photo => {
        const template = document.getElementById('gallery-photo-template');
        const clone = template.content.cloneNode(true);
        clone.querySelector('.photo-url').value = photo.url || '';
        clone.querySelector('.photo-title').value = photo.title || '';
        container.appendChild(clone);
    });
}

function addGalleryPhoto() {
    const container = document.getElementById('gallery-photos-list');
    const template = document.getElementById('gallery-photo-template');
    const clone = template.content.cloneNode(true);
    container.appendChild(clone);
}

function removeGalleryPhoto(btn) {
    btn.closest('.gallery-photo-item').remove();
}

function collectGalleryPhotos() {
    const photos = [];
    document.querySelectorAll('.gallery-photo-item').forEach((item, index) => {
        const url = item.querySelector('.photo-url').value;
        const title = item.querySelector('.photo-title').value;
        if (url) {
            photos.push({ url, title, order: index });
        }
    });
    return photos;
}

// Services
function loadServices(services) {
    const container = document.getElementById('services-list');
    container.innerHTML = '';
    
    services.forEach(service => {
        const template = document.getElementById('service-template');
        const clone = template.content.cloneNode(true);
        clone.querySelector('.service-name').value = service.name || '';
        clone.querySelector('.service-description').value = service.description || '';
        container.appendChild(clone);
    });
}

function addService() {
    const container = document.getElementById('services-list');
    const template = document.getElementById('service-template');
    const clone = template.content.cloneNode(true);
    container.appendChild(clone);
}

function removeService(btn) {
    btn.closest('.service-item').remove();
}

function collectServices() {
    const services = [];
    document.querySelectorAll('.service-item').forEach(item => {
        const name = item.querySelector('.service-name').value;
        const description = item.querySelector('.service-description').value;
        if (name) {
            services.push({ name, description });
        }
    });
    return services;
}

// Equipment
function loadEquipment(equipment) {
    const container = document.getElementById('equipment-list');
    container.innerHTML = '';
    
    equipment.forEach(item => {
        const template = document.getElementById('equipment-template');
        const clone = template.content.cloneNode(true);
        clone.querySelector('.equipment-name').value = item.name || '';
        clone.querySelector('.equipment-description').value = item.description || '';
        container.appendChild(clone);
    });
}

function addEquipment() {
    const container = document.getElementById('equipment-list');
    const template = document.getElementById('equipment-template');
    const clone = template.content.cloneNode(true);
    container.appendChild(clone);
}

function removeEquipment(btn) {
    btn.closest('.equipment-item').remove();
}

function collectEquipment() {
    const equipment = [];
    document.querySelectorAll('.equipment-item').forEach(item => {
        const name = item.querySelector('.equipment-name').value;
        const description = item.querySelector('.equipment-description').value;
        if (name) {
            equipment.push({ name, description });
        }
    });
    return equipment;
}

// Insurances
function loadInsurances(insurances) {
    const container = document.getElementById('insurance-list');
    container.innerHTML = '';
    
    insurances.forEach(insurance => {
        const template = document.getElementById('insurance-template');
        const clone = template.content.cloneNode(true);
        clone.querySelector('.insurance-name').value = insurance.name || '';
        clone.querySelector('.insurance-type').value = insurance.type || 'public';
        clone.querySelector('.insurance-logo').value = insurance.logo_url || '';
        container.appendChild(clone);
    });
}

function addInsurance() {
    const container = document.getElementById('insurance-list');
    const template = document.getElementById('insurance-template');
    const clone = template.content.cloneNode(true);
    container.appendChild(clone);
}

function quickAddInsurance(name, type) {
    const container = document.getElementById('insurance-list');
    const template = document.getElementById('insurance-template');
    const clone = template.content.cloneNode(true);
    clone.querySelector('.insurance-name').value = name;
    clone.querySelector('.insurance-type').value = type;
    container.appendChild(clone);
    
    showAlert('success', `${name} hinzugefügt`);
}

function removeInsurance(btn) {
    btn.closest('.insurance-item').remove();
}

function collectInsurances() {
    const insurances = [];
    document.querySelectorAll('.insurance-item').forEach(item => {
        const name = item.querySelector('.insurance-name').value;
        const type = item.querySelector('.insurance-type').value;
        const logo_url = item.querySelector('.insurance-logo').value;
        if (name) {
            insurances.push({ name, type, logo_url });
        }
    });
    return insurances;
}

// Features
function loadFeatures(features) {
    document.querySelectorAll('.feature-checkbox').forEach(checkbox => {
        checkbox.checked = features.includes(checkbox.value);
    });
}

function collectFeatures() {
    const features = [];
    document.querySelectorAll('.feature-checkbox:checked').forEach(checkbox => {
        features.push(checkbox.value);
    });
    return features;
}

// FAQ
function loadFAQ(faq) {
    const container = document.getElementById('faq-list');
    container.innerHTML = '';
    
    faq.forEach(item => {
        const template = document.getElementById('faq-template');
        const clone = template.content.cloneNode(true);
        clone.querySelector('.faq-question').value = item.question || '';
        clone.querySelector('.faq-answer').value = item.answer || '';
        container.appendChild(clone);
    });
}

function addFAQ() {
    const container = document.getElementById('faq-list');
    const template = document.getElementById('faq-template');
    const clone = template.content.cloneNode(true);
    container.appendChild(clone);
}

function removeFAQ(btn) {
    btn.closest('.faq-item').remove();
}

function collectFAQ() {
    const faq = [];
    document.querySelectorAll('.faq-item').forEach((item, index) => {
        const question = item.querySelector('.faq-question').value;
        const answer = item.querySelector('.faq-answer').value;
        if (question && answer) {
            faq.push({ question, answer, order: index });
        }
    });
    return faq;
}

// Form submission
function setupFormHandler() {
    document.getElementById('extended-practice-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Helper function to safely get value
        const getValueSafe = (id) => {
            const element = document.getElementById(id);
            return element ? element.value : '';
        };
        
        // Collect all data
        const formData = {
            phone: getValueSafe('phone'),
            emergency_phone: getValueSafe('emergency_phone'),
            whatsapp_number: getValueSafe('whatsapp_number'),
            telegram_username: getValueSafe('telegram_username'),
            contact_email: getValueSafe('contact_email'),
            website: getValueSafe('website'),
            google_business_url: getValueSafe('google_business_url'),
            social_media: {
                facebook: getValueSafe('social_facebook'),
                instagram: getValueSafe('social_instagram'),
                linkedin: getValueSafe('social_linkedin'),
                twitter: getValueSafe('social_twitter'),
                youtube: getValueSafe('social_youtube'),
                tiktok: getValueSafe('social_tiktok')
            },
            video_url: getValueSafe('video_url'),
            virtual_tour_url: getValueSafe('virtual_tour_url'),
            services: collectServices(),
            equipment: collectEquipment(),
            accepted_insurances: collectInsurances(),
            features: collectFeatures(),
            chatbot_instructions: getValueSafe('chatbot_instructions')
        };
        
        // Save
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch('/api/practice/profile/extended', {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            if (response.ok) {
                showAlert('success', 'Profil erfolgreich gespeichert!');
                loadExtendedProfile(); // Reload to update completeness
            } else {
                const errorData = await response.json();
                showAlert('danger', errorData.error || 'Fehler beim Speichern');
            }
        } catch (error) {
            console.error('Error:', error);
            showAlert('danger', 'Fehler beim Speichern: ' + error.message);
        }
    });
}

// Calculate profile completeness
function calculateCompleteness() {
    let score = 0;
    const maxScore = 11;
    
    if (collectGalleryPhotos().length >= 3) score++;
    if (document.getElementById('description').value) score++;
    if (collectServices().length >= 5) score++;
    if (practiceData.opening_hours) score++;
    if (collectInsurances().length > 0) score++;
    if (collectFeatures().length > 0) score++;
    if (collectFAQ().length >= 3) score++;
    if (document.getElementById('parking_info').value) score++;
    if (practiceData.public_transport) score++;
    if (document.getElementById('video_url').value) score++;
    if (document.getElementById('virtual_tour_url').value) score++;
    
    const percentage = Math.round((score / maxScore) * 100);
    
    const badge = document.getElementById('profile-completeness');
    badge.textContent = `${percentage}% vollständig`;
    badge.className = 'badge ' + (percentage >= 80 ? 'bg-success' : percentage >= 50 ? 'bg-warning' : 'bg-danger');
}

// Alert helper
function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container-fluid');
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => alertDiv.remove(), 5000);
}
