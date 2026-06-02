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

    // ---- Submit via AJAX — overlay stays visible with live steps ----
    const uploadForm = document.getElementById("uploadForm");
    if (uploadForm) {
        uploadForm.addEventListener("submit", function (e) {
            e.preventDefault(); // stop normal form submit

            if (!fileInput.files || !fileInput.files[0]) return;

            const overlay = document.getElementById("analysisOverlay");
            const subEl   = document.getElementById("analysisStep");

            const stepEls = ["step1","step2","step3","step4"]
                .map(function (id) { return document.getElementById(id); });

            function activateStep(i) {
                stepEls.forEach(function (el, j) {
                    if (!el) return;
                    const dot = el.querySelector(".step-dot");
                    if (!dot) return;
                    if (j < i) {
                        dot.classList.remove("step-dot--active");
                        dot.classList.add("step-dot--done");
                        el.classList.add("active");
                    } else if (j === i) {
                        dot.classList.add("step-dot--active");
                        el.classList.add("active");
                    }
                });
                const labels = [
                    "Uploading image...",
                    "Running AI vision model...",
                    "Generating recommendations...",
                    "Preparing report..."
                ];
                if (subEl) subEl.textContent = labels[i] || "";
            }

            // Show overlay
            if (overlay) overlay.style.display = "flex";
            submitBtn.disabled = true;
            activateStep(0);

            // Step 1 → Step 2 after short delay (upload usually fast)
            const t1 = setTimeout(function () { activateStep(1); }, 1500);
            const t2 = setTimeout(function () { activateStep(2); }, 5000);

            // Build FormData and POST via AJAX
            const formData = new FormData();
            formData.append("crop_image", fileInput.files[0]);

            fetch("/upload/ajax", {
                method: "POST",
                body: formData
            })
            .then(function (resp) { return resp.json(); })
            .then(function (data) {
                clearTimeout(t1);
                clearTimeout(t2);
                if (data.error) {
                    // Hide overlay and show error
                    if (overlay) overlay.style.display = "none";
                    submitBtn.disabled = false;
                    alert("Error: " + data.error);
                    return;
                }
                // Step 3 and 4 briefly before redirect
                activateStep(2);
                setTimeout(function () {
                    activateStep(3);
                    setTimeout(function () {
                        window.location.href = data.redirect;
                    }, 600);
                }, 600);
            })
            .catch(function (err) {
                clearTimeout(t1);
                clearTimeout(t2);
                if (overlay) overlay.style.display = "none";
                submitBtn.disabled = false;
                alert("Network error. Please check your connection and try again.");
            });
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

/* ============================================================
   Mobile Menu
   ============================================================ */
(function () {
    const btn = document.getElementById("mobileMenuBtn");
    const nav = document.getElementById("mobileNav");
    if (!btn || !nav) return;

    btn.addEventListener("click", function () {
        const open = !nav.hidden;
        nav.hidden = open;
        btn.setAttribute("aria-expanded", String(!open));
    });

    // Close on outside click
    document.addEventListener("click", function (e) {
        if (!btn.contains(e.target) && !nav.contains(e.target)) {
            nav.hidden = true;
        }
    });
})();

/* ============================================================
   AI Agronomist Chat
   ============================================================ */

(function () {
    const messagesEl = document.getElementById("chatMessages");
    const inputEl    = document.getElementById("chatInput");
    const sendBtn    = document.getElementById("chatSendBtn");

    if (!messagesEl || !inputEl) return;

    // Conversation history for context
    const history = [];

    function scrollToBottom() {
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function addMessage(role, text) {
        // Remove suggestions after first user message
        if (role === "user") {
            const sugg = document.getElementById("chatSuggestions");
            if (sugg) sugg.remove();
        }

        const wrapper = document.createElement("div");
        wrapper.className = "chat-msg chat-msg--" + role;
        const bubble = document.createElement("div");
        bubble.className = "chat-msg-bubble";
        bubble.textContent = text;
        wrapper.appendChild(bubble);
        messagesEl.appendChild(wrapper);
        scrollToBottom();
        return bubble;
    }

    function showTyping() {
        const wrapper = document.createElement("div");
        wrapper.className = "chat-msg chat-msg--ai";
        wrapper.id = "typingIndicator";
        wrapper.innerHTML =
            '<div class="chat-typing">' +
            '<div class="chat-typing-dot"></div>' +
            '<div class="chat-typing-dot"></div>' +
            '<div class="chat-typing-dot"></div>' +
            '</div>';
        messagesEl.appendChild(wrapper);
        scrollToBottom();
    }

    function removeTyping() {
        const el = document.getElementById("typingIndicator");
        if (el) el.remove();
    }

    async function sendMessage(text) {
        text = text.trim();
        if (!text) return;

        inputEl.value = "";
        sendBtn.disabled = true;
        inputEl.disabled = true;

        addMessage("user", text);
        history.push({ role: "user", content: text });
        showTyping();

        try {
            const resp = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: text,
                    context: window.CROP_CONTEXT || {},
                    history: history.slice(-10),
                }),
            });
            const data = await resp.json();
            removeTyping();

            if (data.error) {
                addMessage("ai", "Sorry, I could not answer right now: " + data.error);
            } else {
                addMessage("ai", data.reply);
                history.push({ role: "model", content: data.reply });
            }
        } catch (err) {
            removeTyping();
            addMessage("ai", "Network error. Please check your connection and try again.");
        } finally {
            sendBtn.disabled = false;
            inputEl.disabled = false;
            inputEl.focus();
        }
    }

    // Send on button click
    sendBtn.addEventListener("click", function () {
        sendMessage(inputEl.value);
    });

    // Send on Enter key
    inputEl.addEventListener("keydown", function (e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage(inputEl.value);
        }
    });

    // Global function for suggestion buttons
    window.askSuggestion = function (btn) {
        sendMessage(btn.textContent);
    };

    scrollToBottom();
})();

/* ============================================================
   User Menu Dropdown
   ============================================================ */
(function () {
    const btn      = document.getElementById("userMenuBtn");
    const dropdown = document.getElementById("userDropdown");
    if (!btn || !dropdown) return;

    btn.addEventListener("click", function (e) {
        e.stopPropagation();
        dropdown.hidden = !dropdown.hidden;
    });

    document.addEventListener("click", function (e) {
        if (!btn.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.hidden = true;
        }
    });
})();
