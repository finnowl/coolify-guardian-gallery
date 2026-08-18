(function() {
    var JSON_URL = 'latest_guardian_photos.json'; // Will be in the same folder
    var REFRESH_INTERVAL_MS = 6 * 60 * 60 * 1000; // 6 hours
    var SLIDE_DURATION_MS = 30000; // 30 seconds
    
    var photos = [];
    var currentIndex = 0;
    var activeSlideDivIndex = 0; // 0 or 1
    var slideWaitTimer = null;
    
    var slideDivs = [
        document.getElementById('slide0'),
        document.getElementById('slide1')
    ];
    
    var overlay = document.getElementById('overlay');
    var captionEl = document.getElementById('caption');
    var creditEl = document.getElementById('credit');
    
    // Toggle overlay visibility on click or touch
    var lastToggleTime = 0;
    function handleToggle(e) {
        // Prevent double firing from touchstart + click on same interaction
        var now = new Date().getTime();
        if (now - lastToggleTime < 300) return;
        lastToggleTime = now;
        
        if (overlay.className === 'visible') {
            overlay.className = '';
        } else {
            overlay.className = 'visible';
        }
    }
    
    document.addEventListener('click', handleToggle);
    document.addEventListener('touchstart', handleToggle);

    function fetchPhotos(callback) {
        var xhr = new XMLHttpRequest();
        // Add a cache buster so we don't get stuck on old cached json
        var cacheBuster = '?t=' + new Date().getTime();
        xhr.open('GET', JSON_URL + cacheBuster, true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                if (xhr.status === 200 || xhr.status === 0) { // status 0 is for local file://
                    try {
                        var data = JSON.parse(xhr.responseText);
                        if (data && data.length > 0) {
                            photos = data;
                            if (callback) callback();
                        }
                    } catch (e) {
                        console.error('Error parsing JSON:', e);
                    }
                } else {
                    console.error('Error fetching JSON, status:', xhr.status);
                }
            }
        };
        xhr.send(null);
    }

    function preloadImage(url) {
        var img = new Image();
        img.src = url;
    }

    function setSlideData(index) {
        var photo = photos[index];
        if (!photo) return;
        
        var nextSlideDivIndex = (activeSlideDivIndex + 1) % 2;
        var nextSlideDiv = slideDivs[nextSlideDivIndex];
        var currentSlideDiv = slideDivs[activeSlideDivIndex];
        
        // Update URL of the incoming slide
        nextSlideDiv.style.backgroundImage = 'url("' + photo.url + '")';
        
        // Update content for the overlay based on the incoming photo
        captionEl.textContent = photo.caption || '';
        creditEl.textContent = photo.credit ? 'Credit: ' + photo.credit : '';
        
        // Trigger fade
        nextSlideDiv.className = 'slide active';
        currentSlideDiv.className = 'slide';
        
        // Update active index
        activeSlideDivIndex = nextSlideDivIndex;
        
        // Preload next image dynamically
        var prefetchIndex = (index + 1) % photos.length;
        preloadImage(photos[prefetchIndex].url);
    }

    function nextSlide() {
        if (photos.length === 0) return;
        
        currentIndex = (currentIndex + 1) % photos.length;
        setSlideData(currentIndex);
    }

    function startSlideshow() {
        if (photos.length === 0) return;
        
        // Start first slide instantly
        currentIndex = 0;
        
        // Instead of typical transition for the very first frame, just set it
        var firstPhoto = photos[0];
        slideDivs[activeSlideDivIndex].style.backgroundImage = 'url("' + firstPhoto.url + '")';
        slideDivs[activeSlideDivIndex].className = 'slide active';
        captionEl.textContent = firstPhoto.caption || '';
        creditEl.textContent = firstPhoto.credit ? 'Credit: ' + firstPhoto.credit : '';
        
        // Preload second image
        if (photos.length > 1) {
            preloadImage(photos[1].url);
        }
        
        // Set timer for the next slide
        if (slideWaitTimer) clearInterval(slideWaitTimer);
        slideWaitTimer = setInterval(nextSlide, SLIDE_DURATION_MS);
    }

    // Initialize application
    function init() {
        fetchPhotos(startSlideshow);
        
        // Re-fetch data every 6 hours
        setInterval(function() {
            fetchPhotos(null); // Just update the photos array quietly
        }, REFRESH_INTERVAL_MS);
    }

    // Start
    init();

})();
