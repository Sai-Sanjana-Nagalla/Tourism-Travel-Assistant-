// Global variables
let map;
let directionsService;
let directionsRenderer;
let contactMap;
let markers = [];

// Initialize when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Password validation setup
    setupPasswordValidation();
    
    // Navigation between pages
    setupNavigation();
    
    // Form submissions
    setupFormSubmissions();
    
    // User menu dropdown
    setupUserMenu();
    
    // Carousel controls
    setupCarousel();
});

// Password validation function
function validatePassword(password) {
    // Define password requirements
    const minLength = 8;
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumbers = /\d/.test(password);
    const hasSpecialChar = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);
    
    // Error messages
    const errors = [];
    
    if (password.length < minLength) {
        errors.push(`Password must be at least ${minLength} characters long`);
    }
    
    if (!hasUpperCase) {
        errors.push("Password must contain at least one uppercase letter");
    }
    
    if (!hasLowerCase) {
        errors.push("Password must contain at least one lowercase letter");
    }
    
    if (!hasNumbers) {
        errors.push("Password must contain at least one number");
    }
    
    if (!hasSpecialChar) {
        errors.push("Password must contain at least one special character");
    }
    
    return {
        isValid: errors.length === 0,
        errors: errors
    };
}

// Create password validation feedback element
function createPasswordFeedback() {
    const feedbackDiv = document.createElement('div');
    feedbackDiv.id = 'password-feedback';
    feedbackDiv.className = 'password-feedback';
    
    // Insert after password input
    const passwordInput = document.getElementById('password');
    const inputGroup = passwordInput.parentElement;
    inputGroup.insertAdjacentElement('afterend', feedbackDiv);
    
    return feedbackDiv;
}

// Show password validation feedback
function showPasswordFeedback(validationResult) {
    let feedbackDiv = document.getElementById('password-feedback');
    
    if (!feedbackDiv) {
        feedbackDiv = createPasswordFeedback();
    }
    
    // Clear previous feedback
    feedbackDiv.innerHTML = '';
    
    if (!validationResult.isValid) {
        feedbackDiv.style.display = 'block';
        const errorList = document.createElement('ul');
        
        validationResult.errors.forEach(error => {
            const listItem = document.createElement('li');
            listItem.textContent = error;
            errorList.appendChild(listItem);
        });
        
        feedbackDiv.appendChild(errorList);
    } else {
        feedbackDiv.style.display = 'none';
    }
}

// Setup password validation
function setupPasswordValidation() {
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        // Add input event listener for real-time password validation
        passwordInput.addEventListener('input', function() {
            const validationResult = validatePassword(this.value);
            showPasswordFeedback(validationResult);
            
            // Add visual indicator classes
            if (this.value.length > 0) {
                if (validationResult.isValid) {
                    this.classList.add('valid');
                    this.classList.remove('invalid');
                } else {
                    this.classList.add('invalid');
                    this.classList.remove('valid');
                }
            } else {
                this.classList.remove('valid');
                this.classList.remove('invalid');
            }
        });
    }
}

// Map initialization (called by Google Maps API callback)
function initMap() {
    // Initialize main map for route planning
    initRouteMap();
    
    // Initialize contact page map
    initContactMap();
}

function initRouteMap() {
    // Create a map centered on a default location
    map = new google.maps.Map(document.getElementById('map'), {
        center: { lat: 40.7128, lng: -74.0060 }, // New York
        zoom: 12,
        mapTypeControl: true,
        mapTypeControlOptions: {
            style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
            position: google.maps.ControlPosition.TOP_RIGHT
        },
        fullscreenControl: true,
        streetViewControl: true,
        zoomControl: true
    });
    
    // Initialize the directions service and renderer
    directionsService = new google.maps.DirectionsService();
    directionsRenderer = new google.maps.DirectionsRenderer({
        map: map,
        panel: document.getElementById('directions-panel'),
        draggable: true,
        hideRouteList: false
    });
    
    // Add autocomplete to origin and destination inputs
    const originInput = document.getElementById('origin');
    const destinationInput = document.getElementById('destination');
    
    const originAutocomplete = new google.maps.places.Autocomplete(originInput, {
        fields: ["formatted_address", "geometry", "name"],
        strictBounds: false
    });
    
    const destinationAutocomplete = new google.maps.places.Autocomplete(destinationInput, {
        fields: ["formatted_address", "geometry", "name"],
        strictBounds: false
    });
    
    // Bind autocomplete to the map
    originAutocomplete.bindTo("bounds", map);
    destinationAutocomplete.bindTo("bounds", map);
    
    // Add event listener for route finding
    document.getElementById('find-route').addEventListener('click', calculateRoute);
}

function initContactMap() {
    // Get the contact map container
    const contactMapElement = document.getElementById('contact-location-map');
    
    if (contactMapElement) {
        // Create a map centered on the office location
        contactMap = new google.maps.Map(contactMapElement, {
            center: { lat: 40.7128, lng: -74.0060 }, // Default location
            zoom: 15
        });
        
        // Add a marker for the office location
        const marker = new google.maps.Marker({
            position: { lat: 40.7128, lng: -74.0060 },
            map: contactMap,
            title: 'TravelPlanner Office',
            animation: google.maps.Animation.DROP
        });
        
        // Add info window
        const infoWindow = new google.maps.InfoWindow({
            content: '<div><strong>TravelPlanner Office</strong><br>123 Travel Street<br>Tourism City, TC 10001</div>'
        });
        
        marker.addListener('click', function() {
            infoWindow.open(contactMap, marker);
        });
    }
}

function calculateRoute() {
    const origin = document.getElementById('origin').value;
    const destination = document.getElementById('destination').value;
    
    console.log("Origin:", origin);
    console.log("Destination:", destination);
    
    if (!origin || !destination) {
        alert('Please enter both origin and destination');
        return;
    }
    
    // Clear previous route
    if (markers.length > 0) {
        for (let i = 0; i < markers.length; i++) {
            markers[i].setMap(null);
        }
        markers = [];
    }
    
    // Set up route request options
    const request = {
        origin: origin,
        destination: destination,
        travelMode: google.maps.TravelMode.DRIVING
    };
    
    console.log("Requesting route with:", request);
    
    // Request route from Google Maps Directions Service
    directionsService.route(request, function(result, status) {
        console.log("Direction service response status:", status);
        console.log("Result:", result);
        
        if (status === google.maps.DirectionsStatus.OK) {
            // Display the route on the map and in the directions panel
            directionsRenderer.setDirections(result);
            console.log("Route displayed successfully");
        } else {
            alert('Directions request failed due to ' + status);
        }
    });
}

function setupNavigation() {
    // Login page navigation
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Validate password before proceeding
            const passwordInput = document.getElementById('password');
            const validationResult = validatePassword(passwordInput.value);
            
            if (!validationResult.isValid) {
                showPasswordFeedback(validationResult);
                return;
            }
            
            // If validation passes, proceed with login
            console.log('Login successful');
            showPage('home-page');
        });
    }
    
    // Signup link
    const signupLink = document.getElementById('signup-link');
    if (signupLink) {
        signupLink.addEventListener('click', function(e) {
            e.preventDefault();
            alert('Sign up functionality will be implemented soon!');
        });
    }
    
    // Logout button
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            showPage('login-page');
        });
    }
    
    // Nav links
    const navHome = document.getElementById('nav-home');
    if (navHome) {
        navHome.addEventListener('click', function(e) {
            e.preventDefault();
            showPage('home-page');
        });
    }
    
    const navContact = document.getElementById('nav-contact');
    if (navContact) {
        navContact.addEventListener('click', function(e) {
            e.preventDefault();
            showPage('contact-page');
        });
    }
    
    // Contact page nav links
    const contactNavHome = document.getElementById('contact-nav-home');
    if (contactNavHome) {
        contactNavHome.addEventListener('click', function(e) {
            e.preventDefault();
            showPage('home-page');
        });
    }
    
    // Main action buttons
    const choosePlaceBtn = document.getElementById('choose-place');
    if (choosePlaceBtn) {
        choosePlaceBtn.addEventListener('click', function() {
            window.location.href = 'destination.html';
        });
    }
    
    const suggestPlaceBtn = document.getElementById('suggest-place');
    if (suggestPlaceBtn) {
        suggestPlaceBtn.addEventListener('click', function() {
            window.location.href = 'budget_manager.html';
        });
    }
}

function showPage(pageId) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    
    // Show the requested page
    document.getElementById(pageId).classList.add('active');
    
    // If we're showing the home page, resize the map to fix any display issues
    if (pageId === 'home-page' && map) {
        setTimeout(function() {
            google.maps.event.trigger(map, 'resize');
            // If we have a current route, fit bounds to it
            if (directionsRenderer && directionsRenderer.getDirections()) {
                const route = directionsRenderer.getDirections().routes[0];
                const bounds = new google.maps.LatLngBounds();
                route.legs.forEach(leg => {
                    bounds.extend(leg.start_location);
                    bounds.extend(leg.end_location);
                });
                map.fitBounds(bounds);
            }
        }, 100);
    }
    
    // If we're showing the contact page, resize the contact map
    if (pageId === 'contact-page' && contactMap) {
        setTimeout(function() {
            google.maps.event.trigger(contactMap, 'resize');
        }, 100);
    }
}

function setupFormSubmissions() {
    // Contact form submission
    const contactForm = document.getElementById('contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Collect form data
            const name = document.getElementById('name').value;
            const email = document.getElementById('contact-email').value;
            const subject = document.getElementById('subject').value;
            const message = document.getElementById('message').value;
            
            // In a real application, you would send this data to a server
            console.log('Contact form submitted:', { name, email, subject, message });
            
            // Show success message
            alert('Thank you for your message! We will get back to you soon.');
            
            // Reset the form
            contactForm.reset();
        });
    }
}

function setupUserMenu() {
    // Toggle dropdown when clicking on user profile
    const userProfile = document.querySelector('.user-profile');
    const dropdownMenu = document.querySelector('.dropdown-menu');
    
    if (userProfile && dropdownMenu) {
        userProfile.addEventListener('click', function() {
            dropdownMenu.style.display = dropdownMenu.style.display === 'block' ? 'none' : 'block';
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!userProfile.contains(e.target) && !dropdownMenu.contains(e.target)) {
                dropdownMenu.style.display = 'none';
            }
        });
    }
}

function setupCarousel() {
    const carousel = document.querySelector('.destination-carousel');
    const prevBtn = document.querySelector('.carousel-control.prev');
    const nextBtn = document.querySelector('.carousel-control.next');
    
    if (carousel && prevBtn && nextBtn) {
        const cardWidth = 320; // Card width + gap
        
        prevBtn.addEventListener('click', function() {
            carousel.scrollBy({ left: -cardWidth, behavior: 'smooth' });
        });
        
        nextBtn.addEventListener('click', function() {
            carousel.scrollBy({ left: cardWidth, behavior: 'smooth' });
        });
    }
}

// Additional functionality for place suggestions
function suggestPlace(preferences) {
    // This would typically connect to a backend service
    // For now, we'll just return some hardcoded suggestions based on interests
    const suggestions = {
        beach: ['Bali, Indonesia', 'Cancun, Mexico', 'Miami, USA'],
        mountain: ['Swiss Alps, Switzerland', 'Banff, Canada', 'Patagonia, Argentina'],
        city: ['Tokyo, Japan', 'Paris, France', 'New York, USA'],
        cultural: ['Kyoto, Japan', 'Rome, Italy', 'Marrakech, Morocco'],
        adventure: ['New Zealand', 'Costa Rica', 'Iceland']
    };
    
    // Return a random suggestion from the appropriate category
    const category = preferences.interest || 'beach';
    const options = suggestions[category] || suggestions.beach;
    return options[Math.floor(Math.random() * options.length)];
}

// Function to add a place to user's favorites
function addToFavorites(placeId, placeName) {
    // In a real application, this would send data to a server
    console.log(`Added ${placeName} to favorites`);
    alert(`${placeName} has been added to your favorites!`);
    
    // You would typically update the UI to show it's been favorited
    // For example, change a heart icon from empty to filled
}

// Function to save a trip plan
function saveTripPlan(tripData) {
    // In a real application, this would send data to a server
    console.log('Saving trip plan:', tripData);
    alert('Your trip has been saved successfully!');
    
    // Redirect to a trip details page or show a confirmation
    // For now, we'll just log the data
}

// Weather API integration (mock)
function getWeatherForecast(location) {
    // In a real application, this would fetch data from a weather API
    // For demonstration purposes, we'll return mock data
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({
                location: location,
                forecast: [
                    { day: 'Monday', temp: '75°F', condition: 'Sunny' },
                    { day: 'Tuesday', temp: '72°F', condition: 'Partly Cloudy' },
                    { day: 'Wednesday', temp: '68°F', condition: 'Cloudy' },
                    { day: 'Thursday', temp: '70°F', condition: 'Sunny' },
                    { day: 'Friday', temp: '74°F', condition: 'Sunny' }
                ]
            });
        }, 500);
    });
}

// Currency converter (mock)
function convertCurrency(amount, fromCurrency, toCurrency) {
    // In a real application, this would fetch current exchange rates
    // For demonstration purposes, we'll use fixed rates
    const rates = {
        USD: 1,
        EUR: 0.85,
        GBP: 0.75,
        JPY: 110.5,
        AUD: 1.35
    };
    
    const fromRate = rates[fromCurrency] || 1;
    const toRate = rates[toCurrency] || 1;
    
    return (amount / fromRate * toRate).toFixed(2);
}