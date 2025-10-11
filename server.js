// maps.js - Frontend code to integrate with the Maps Backend API

// Configuration
const API_BASE_URL = 'http://localhost:3001'; // Adjust to match your backend URL

// DOM Elements
const originInput = document.getElementById('origin');
const destinationInput = document.getElementById('destination');
const findRouteButton = document.getElementById('find-route');
const directionsPanel = document.getElementById('directions-panel');

// Map Variables
let map;
let directionsService;
let directionsRenderer;
let placesService;
let originAutocomplete;
let destinationAutocomplete;

// Initialize the map and related services
function initMap() {
  // Create map centered on a default location (can be adjusted)
  map = new google.maps.Map(document.getElementById('map'), {
    center: { lat: 40.7128, lng: -74.0060 }, // New York City as default
    zoom: 13,
    mapTypeControl: true,
    streetViewControl: true,
    fullscreenControl: true
  });

  // Initialize the directions service and renderer
  directionsService = new google.maps.DirectionsService();
  directionsRenderer = new google.maps.DirectionsRenderer({
    map: map,
    panel: directionsPanel,
    draggable: true, // Allow routes to be dragged
    suppressMarkers: false // Show default markers
  });

  // Set up autocomplete for origin and destination inputs
  setupAutocomplete();

  // Add event listeners
  findRouteButton.addEventListener('click', calculateAndDisplayRoute);

  // Add listener for the enter key in input fields
  originInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') calculateAndDisplayRoute();
  });
  
  destinationInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') calculateAndDisplayRoute();
  });
}

// Set up Google Places Autocomplete for input fields
function setupAutocomplete() {
  originAutocomplete = new google.maps.places.Autocomplete(originInput);
  destinationAutocomplete = new google.maps.places.Autocomplete(destinationInput);
  
  // Bias the autocomplete results to the map's viewport
  originAutocomplete.bindTo('bounds', map);
  destinationAutocomplete.bindTo('bounds', map);
}

// Calculate and display the route between origin and destination
async function calculateAndDisplayRoute() {
  const origin = originInput.value;
  const destination = destinationInput.value;
  
  if (!origin || !destination) {
    showError('Please enter both origin and destination');
    return;
  }
  
  // Show loading state
  showLoading(true);
  
  try {
    // Make API request to backend for directions
    const response = await fetch(`${API_BASE_URL}/api/directions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        origin: origin,
        destination: destination,
        travelMode: 'driving' // You could add UI to select different modes
      })
    });
    
    const data = await response.json();
    
    if (data.status !== 'OK') {
      showError('Could not calculate directions: ' + data.status);
      return;
    }
    
    // Display the route on the map
    displayRoute(data);
    
  } catch (error) {
    console.error('Error calculating route:', error);
    showError('Error calculating route. Please try again.');
  } finally {
    showLoading(false);
  }
}

// Display the route on the map using Google Maps DirectionsRenderer
function displayRoute(directionsResult) {
  // Clear previous directions
  directionsPanel.innerHTML = '';
  
  // Convert the backend API response to Google Maps DirectionsResult format
  const formattedResult = formatDirectionsResult(directionsResult);
  
  // Display the directions on the map
  directionsRenderer.setDirections(formattedResult);
  
  // Fit the map to the route bounds
  const bounds = new google.maps.LatLngBounds();
  const route = formattedResult.routes[0];
  
  // Add route waypoints to bounds
  route.legs.forEach(leg => {
    bounds.extend(leg.start_location);
    bounds.extend(leg.end_location);
  });
  
  map.fitBounds(bounds);
  
  // Show summary info above the directions panel
  displayRouteSummary(route);
}

// Format the directions result from our backend to match Google Maps expected format
function formatDirectionsResult(apiResponse) {
  // If the response is already in Google Maps format (which our API returns),
  // we can return it directly
  return apiResponse;
}

// Display route summary information
function displayRouteSummary(route) {
  const summaryDiv = document.createElement('div');
  summaryDiv.className = 'route-summary';
  
  // Calculate total distance and duration
  let totalDistance = 0;
  let totalDuration = 0;
  
  route.legs.forEach(leg => {
    totalDistance += leg.distance.value;
    totalDuration += leg.duration.value;
  });
  
  // Convert to readable format
  const distanceText = (totalDistance < 1000) 
    ? `${totalDistance} m` 
    : `${(totalDistance / 1000).toFixed(1)} km`;
    
  const durationMinutes = Math.round(totalDuration / 60);
  const durationText = (durationMinutes < 60)
    ? `${durationMinutes} min`
    : `${Math.floor(durationMinutes / 60)} hr ${durationMinutes % 60} min`;
  
  summaryDiv.innerHTML = `
    <div class="summary-title">Route Summary</div>
    <div class="summary-details">
      <div class="summary-item">
        <i class="fas fa-road"></i>
        <span>${distanceText}</span>
      </div>
      <div class="summary-item">
        <i class="fas fa-clock"></i>
        <span>${durationText}</span>
      </div>
    </div>
  `;
  
  // Insert at the top of directions panel
  directionsPanel.insertBefore(summaryDiv, directionsPanel.firstChild);
}

// Show loading indicator
function showLoading(isLoading) {
  if (isLoading) {
    findRouteButton.disabled = true;
    findRouteButton.textContent = 'Calculating...';
    // Could add a spinner here if desired
  } else {
    findRouteButton.disabled = false;
    findRouteButton.textContent = 'Find Route';
  }
}

// Show error message
function showError(message) {
  directionsPanel.innerHTML = `
    <div class="error-message">
      <i class="fas fa-exclamation-circle"></i>
      <p>${message}</p>
    </div>
  `;
}

// Geocode an address to coordinates using our backend API
async function geocodeAddress(address) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/geocode?address=${encodeURIComponent(address)}`);
    const data = await response.json();
    
    if (data.status === 'OK' && data.results && data.results.length > 0) {
      const location = data.results[0].geometry.location;
      return {
        lat: location.lat,
        lng: location.lng,
        formattedAddress: data.results[0].formatted_address
      };
    } else {
      console.error('Geocoding error:', data.status);
      return null;
    }
  } catch (error) {
    console.error('Error geocoding address:', error);
    return null;
  }
}

// Initialize when the page loads
document.addEventListener('DOMContentLoaded', function() {
  // We'll initialize the map from the HTML using a callback with the Google Maps script
  console.log('DOM fully loaded, waiting for Google Maps to initialize...');
});

// Function called by Google Maps API when loaded
function googleMapsCallback() {
  console.log('Google Maps API loaded, initializing map...');
  initMap();
}