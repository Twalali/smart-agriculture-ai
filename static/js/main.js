"use strict";

(function () {
    const dropZone       = document.getElementById("dropZone");
    const fileInput      = document.getElementById("cropImageInput");
    const previewContainer = document.getElementById("previewContainer");
    const previewImg     = document.getElementById("previewImg");
    const previewName    = document.getElementById("previewName");
    const clearBtn       = document.getElementById("clearFile");
    const submitBtn      = document.getElementById("submitBtn");
    const dropInner      = dropZone ? dropZone.querySelector(".drop-zone-inner") : null;

    if (!dropZone) return; // not on upload page

    // ---- File processing ----

    function processFile(file) {
        if (!file || !file.type.startsWith("image/")) {
            alert("Please select a valid image file.");
            return;
        }

        const maxBytes = 10 * 1024 * 1024;
        if (file.size > maxBytes) {
            alert("File exceeds the 10 MB limit.");
            return;
        }

        const reader = new FileReader();
        reader.onload = function (e) {
            previewImg.src  = e.target.result;
            previewName.textContent = file.name;
            previewContainer.hidden = false;
            dropInner.hidden = true;
            submitBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    function resetForm() {
        fileInput.value = "";
        previewImg.src  = "";
        previewName.textContent = "";
        previewContainer.hidden = true;
        dropInner.hidden = false;
        submitBtn.disabled = true;
    }

    // ---- File input change ----
    fileInput.addEventListener("change", function () {
        if (this.files && this.files[0]) {
            processFile(this.files[0]);
        }
    });

    // ---- Clear button ----
    clearBtn.addEventListener("click", function (e) {
        e.preventDefault();
        resetForm();
    });

    // ---- Drag and drop ----
    ["dragenter", "dragover"].forEach(function (evt) {
        dropZone.addEventListener(evt, function (e) {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add("drag-over");
        });
    });

    ["dragleave", "dragend", "drop"].forEach(function (evt) {
        dropZone.addEventListener(evt, function (e) {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove("drag-over");
        });
    });

    dropZone.addEventListener("drop", function (e) {
        const files = e.dataTransfer.files;
        if (files && files[0]) {
            // Assign to the file input for form submission
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(files[0]);
            fileInput.files = dataTransfer.files;
            processFile(files[0]);
        }
    });

    // ---- Click on drop zone activates file input ----
    dropZone.addEventListener("click", function (e) {
        if (
            e.target === clearBtn ||
            clearBtn.contains(e.target) ||
            e.target === previewImg ||
            e.target.closest(".btn--outline")
        ) return;
        if (previewContainer.hidden === false) return;
        fileInput.click();
    });

    dropZone.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            fileInput.click();
        }
    });

    // ---- Submit loading state ----
    const uploadForm = document.getElementById("uploadForm");
    if (uploadForm) {
        uploadForm.addEventListener("submit", function () {
            submitBtn.disabled = true;
            const label = submitBtn.querySelector(".btn-label");
            if (label) label.textContent = "Uploading...";
        });
    }
})();

/* ============================================================
   Weather Widget
   ============================================================ */

(function () {
    const input      = document.getElementById("weatherInput");
    const btn        = document.getElementById("weatherBtn");
    const loading    = document.getElementById("weatherLoading");
    const errorBox   = document.getElementById("weatherError");
    const result     = document.getElementById("weatherResult");

    if (!input) return; // not on home page

    const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

    function show(el)  { el.hidden = false; }
    function hide(el)  { el.hidden = true; }

    function setLoading(on) {
        if (on) { show(loading); hide(errorBox); hide(result); }
        else    { hide(loading); }
        btn.disabled = on;
    }

    function showError(msg) {
        errorBox.textContent = msg;
        show(errorBox);
    }

    function renderRisk(risk) {
        const dot   = document.getElementById("wRiskDot");
        const label = document.getElementById("wRiskLabel");
        const desc  = document.getElementById("wRiskDesc");
        dot.className   = `risk-dot risk-dot--${risk}`;
        label.className = `risk-label risk-label--${risk}`;
        label.textContent = risk === "low" ? "Low Risk"
                          : risk === "medium" ? "Medium Risk" : "High Risk";
        desc.textContent = risk === "low"
            ? "Current weather conditions are favourable for crops."
            : risk === "medium"
            ? "Some conditions may promote disease. Stay alert."
            : "High disease risk. Take preventive action now.";
    }

    function renderForecast(rain3, tMax, tMin) {
        const grid = document.getElementById("wForecast");
        grid.innerHTML = "";
        const today = new Date();
        rain3.forEach(function (rain, i) {
            const d = new Date(today);
            d.setDate(today.getDate() + i);
            const dayName = i === 0 ? "Today" : DAYS[d.getDay()];
            const row = document.createElement("div");
            row.className = "forecast-day";
            row.innerHTML =
                `<span class="forecast-day-name">${dayName}</span>` +
                `<span class="forecast-temps">${Math.round(tMin[i])}° – ${Math.round(tMax[i])}°C</span>` +
                `<span class="forecast-rain">${rain.toFixed(1)} mm</span>`;
            grid.appendChild(row);
        });
    }

    function renderAdvice(advice) {
        const list = document.getElementById("wAdviceList");
        list.innerHTML = "";
        advice.forEach(function (tip) {
            const li = document.createElement("li");
            li.className = "weather-advice-item";
            li.textContent = tip;
            list.appendChild(li);
        });
    }

    function renderWeather(data) {
        document.getElementById("wLocation").textContent  = data.location;
        document.getElementById("wCountry").textContent   = data.country;
        document.getElementById("wTemp").textContent      = `${data.temperature}°C`;
        document.getElementById("wCondition").textContent = data.condition;
        document.getElementById("wHumidity").textContent  = `${data.humidity}%`;
        document.getElementById("wRain").textContent      = `${data.precipitation} mm`;
        document.getElementById("wWind").textContent      = `${data.wind_speed} km/h`;

        renderForecast(data.rain_3days, data.temp_max, data.temp_min);
        renderRisk(data.farming_risk);
        renderAdvice(data.farming_advice);
        show(result);
    }

    async function fetchByCoords(lat, lon) {
        setLoading(true);
        try {
            const resp = await fetch(`/api/weather/coords?lat=${lat}&lon=${lon}`);
            const data = await resp.json();
            if (!resp.ok || data.error) {
                showError(data.error || "Failed to fetch weather.");
            } else {
                // Show detected location in the input field
                input.value = data.location + (data.country ? ", " + data.country : "");
                renderWeather(data);
            }
        } catch (err) {
            showError("Network error. Please check your connection.");
        } finally {
            setLoading(false);
        }
    }

    async function fetchByName() {
        const location = input.value.trim();
        if (!location) {
            showError("Please enter a location name.");
            return;
        }
        setLoading(true);
        try {
            const resp = await fetch(`/api/weather?location=${encodeURIComponent(location)}`);
            const data = await resp.json();
            if (!resp.ok || data.error) {
                showError(data.error || "Failed to fetch weather.");
            } else {
                renderWeather(data);
            }
        } catch (err) {
            showError("Network error. Please check your connection.");
        } finally {
            setLoading(false);
        }
    }

    function tryGeolocation() {
        if (!navigator.geolocation) {
            // Browser doesn't support geolocation — fall back to Gitega
            input.value = "Gitega, Burundi";
            fetchByName();
            return;
        }

        setLoading(true);
        navigator.geolocation.getCurrentPosition(
            function (pos) {
                // Success — use GPS coordinates
                fetchByCoords(pos.coords.latitude, pos.coords.longitude);
            },
            function (err) {
                // Denied or failed — fall back to manual input
                setLoading(false);
                if (err.code === err.PERMISSION_DENIED) {
                    input.placeholder = "Location access denied — type your city";
                    input.focus();
                } else {
                    // Timeout or unavailable — default to Gitega
                    input.value = "Gitega, Burundi";
                    fetchByName();
                }
            },
            { timeout: 8000, maximumAge: 300000 }
        );
    }

    btn.addEventListener("click", fetchByName);
    input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") fetchByName();
    });

    // On page load — try GPS first, fall back gracefully
    tryGeolocation();
})();
