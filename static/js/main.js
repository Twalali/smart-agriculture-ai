"use strict";

/* ============================================================
   Upload — drag-and-drop, preview, AJAX submit with overlay
   ============================================================ */
(function () {
    var dropZone   = document.getElementById("dropZone");
    var fileInput  = document.getElementById("cropImageInput");
    var previewCon = document.getElementById("previewContainer");
    var previewImg = document.getElementById("previewImg");
    var previewNm  = document.getElementById("previewName");
    var clearBtn   = document.getElementById("clearFile");
    var submitBtn  = document.getElementById("submitBtn");
    var dropInner  = dropZone ? dropZone.querySelector(".drop-zone-inner") : null;

    if (!dropZone) return;

    function processFile(file) {
        if (!file || !file.type.startsWith("image/")) { alert("Please select a valid image file."); return; }
        if (file.size > 10 * 1024 * 1024) { alert("File exceeds 10 MB limit."); return; }
        var reader = new FileReader();
        reader.onload = function (e) {
            previewImg.src = e.target.result;
            previewNm.textContent = file.name;
            previewCon.style.display = "flex";
            dropInner.style.display  = "none";
            submitBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    function resetForm() {
        fileInput.value = ""; previewImg.src = ""; previewNm.textContent = "";
        previewCon.style.display = "none"; dropInner.style.display = ""; submitBtn.disabled = true;
    }

    fileInput.addEventListener("change", function () { if (this.files && this.files[0]) processFile(this.files[0]); });
    if (clearBtn) clearBtn.addEventListener("click", function (e) { e.preventDefault(); resetForm(); });

    ["dragenter","dragover"].forEach(function (ev) {
        dropZone.addEventListener(ev, function (e) { e.preventDefault(); e.stopPropagation(); dropZone.classList.add("drag-over"); });
    });
    ["dragleave","dragend","drop"].forEach(function (ev) {
        dropZone.addEventListener(ev, function (e) { e.preventDefault(); e.stopPropagation(); dropZone.classList.remove("drag-over"); });
    });
    dropZone.addEventListener("drop", function (e) {
        var files = e.dataTransfer.files;
        if (files && files[0]) {
            var dt = new DataTransfer(); dt.items.add(files[0]); fileInput.files = dt.files; processFile(files[0]);
        }
    });
    dropZone.addEventListener("click", function (e) {
        if (e.target === clearBtn || (clearBtn && clearBtn.contains(e.target))) return;
        if (previewCon.style.display !== "none") return;
        fileInput.click();
    });
    dropZone.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInput.click(); } });

    var uploadForm = document.getElementById("uploadForm");
    if (uploadForm) {
        uploadForm.addEventListener("submit", function (e) {
            e.preventDefault();
            if (!fileInput.files || !fileInput.files[0]) return;
            var overlay = document.getElementById("analysisOverlay");
            var subEl   = document.getElementById("analysisStep");
            var stepEls = ["step1","step2","step3","step4"].map(function (id) { return document.getElementById(id); });
            function activateStep(i) {
                stepEls.forEach(function (el, j) {
                    if (!el) return;
                    var dot = el.querySelector(".step-dot");
                    if (!dot) return;
                    if (j < i) { dot.classList.remove("step-dot--active"); dot.classList.add("step-dot--done"); el.classList.add("active"); }
                    else if (j === i) { dot.classList.add("step-dot--active"); el.classList.add("active"); }
                });
            }
            if (overlay) overlay.style.display = "flex";
            submitBtn.disabled = true; activateStep(0);
            var t1 = setTimeout(function () { activateStep(1); }, 1500);
            var t2 = setTimeout(function () { activateStep(2); }, 5000);
            var formData = new FormData(); formData.append("crop_image", fileInput.files[0]);
            fetch("/upload/ajax", { method: "POST", body: formData })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    clearTimeout(t1); clearTimeout(t2);
                    if (data.error) { if (overlay) overlay.style.display = "none"; submitBtn.disabled = false; alert("Error: " + data.error); return; }
                    activateStep(2);
                    setTimeout(function () { activateStep(3); setTimeout(function () { window.location.href = data.redirect; }, 600); }, 600);
                })
                .catch(function () { clearTimeout(t1); clearTimeout(t2); if (overlay) overlay.style.display = "none"; submitBtn.disabled = false; alert("Network error. Please try again."); });
        });
    }
})();

/* ============================================================
   Mobile menu
   ============================================================ */
(function () {
    var btn = document.getElementById("mobileMenuBtn");
    var nav = document.getElementById("mobileNav");
    if (!btn || !nav) return;
    btn.addEventListener("click", function (e) {
        e.stopPropagation();
        var open = nav.style.display !== "none" && nav.style.display !== "";
        nav.style.display = open ? "none" : "block";
        btn.setAttribute("aria-expanded", String(!open));
        btn.classList.toggle("open", !open);
    });
    document.addEventListener("click", function (e) {
        if (!btn.contains(e.target) && !nav.contains(e.target)) {
            nav.style.display = "none"; btn.setAttribute("aria-expanded", "false"); btn.classList.remove("open");
        }
    });
})();

/* ============================================================
   User dropdown menu
   ============================================================ */
(function () {
    var btn = document.getElementById("userMenuBtn");
    var dropdown = document.getElementById("userDropdown");
    if (!btn || !dropdown) return;
    btn.addEventListener("click", function (e) { e.stopPropagation(); dropdown.hidden = !dropdown.hidden; });
    document.addEventListener("click", function (e) { if (!btn.contains(e.target) && !dropdown.contains(e.target)) dropdown.hidden = true; });
})();

/* ============================================================
   Language switcher
   ============================================================ */
(function () {
    var btn = document.getElementById("langMenuBtn");
    var dropdown = document.getElementById("langDropdown");

    function applyLang(code) {
        fetch("/set-language/" + code, { method: "POST" })
            .then(function (r) { return r.json(); })
            .then(function (d) { if (d.success) window.location.reload(); })
            .catch(function () { window.location.reload(); });
    }

    if (btn && dropdown) {
        btn.addEventListener("click", function (e) { e.stopPropagation(); dropdown.hidden = !dropdown.hidden; });
        document.addEventListener("click", function (e) { if (!btn.contains(e.target) && !dropdown.contains(e.target)) dropdown.hidden = true; });
        document.querySelectorAll(".lang-option").forEach(function (opt) {
            opt.addEventListener("click", function () { applyLang(opt.dataset.lang); });
        });
    }
    document.querySelectorAll(".mobile-lang-btn").forEach(function (opt) {
        opt.addEventListener("click", function () { applyLang(opt.dataset.lang); });
    });
})();

/* ============================================================
   Weather widget
   ============================================================ */
(function () {
    var input = document.getElementById("weatherInput");
    var btn = document.getElementById("weatherBtn");
    var loading = document.getElementById("weatherLoading");
    var errBox = document.getElementById("weatherError");
    var result = document.getElementById("weatherResult");
    if (!input) return;
    var DAYS = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];

    function setLoading(on) {
        loading.style.display = on ? "flex" : "none";
        errBox.style.display = "none";
        if (on) result.style.display = "none";
        btn.disabled = on;
    }
    function showError(msg) { errBox.textContent = msg; errBox.style.display = "block"; }
    function renderRisk(risk) {
        var dot = document.getElementById("wRiskDot");
        var label = document.getElementById("wRiskLabel");
        var desc = document.getElementById("wRiskDesc");
        dot.className = "risk-dot risk-dot--" + risk;
        label.className = "risk-label risk-label--" + risk;
        label.textContent = risk === "low" ? "Low Risk" : risk === "medium" ? "Medium Risk" : "High Risk";
        desc.textContent = risk === "low" ? "Conditions are favourable for crops."
            : risk === "medium" ? "Some conditions may promote disease. Stay alert."
            : "High disease risk. Take preventive action now.";
    }
    function renderForecast(rain3, tMax, tMin) {
        var grid = document.getElementById("wForecast"); grid.innerHTML = "";
        var today = new Date();
        rain3.forEach(function (rain, i) {
            var d = new Date(today); d.setDate(today.getDate() + i);
            var dayName = i === 0 ? "Today" : DAYS[d.getDay()];
            var row = document.createElement("div"); row.className = "forecast-day";
            row.innerHTML = "<span class='forecast-day-name'>" + dayName + "</span>" +
                "<span class='forecast-temps'>" + Math.round(tMin[i]) + "° – " + Math.round(tMax[i]) + "°C</span>" +
                "<span class='forecast-rain'>" + rain.toFixed(1) + " mm</span>";
            grid.appendChild(row);
        });
    }
    function renderAdvice(advice) {
        var list = document.getElementById("wAdviceList"); list.innerHTML = "";
        advice.forEach(function (tip) { var li = document.createElement("li"); li.className = "weather-advice-item"; li.textContent = tip; list.appendChild(li); });
    }
    function renderWeather(data) {
        document.getElementById("wLocation").textContent = data.location;
        document.getElementById("wCountry").textContent = data.country;
        document.getElementById("wTemp").textContent = data.temperature + "°C";
        document.getElementById("wCondition").textContent = data.condition;
        document.getElementById("wHumidity").textContent = data.humidity + "%";
        document.getElementById("wRain").textContent = data.precipitation + " mm";
        document.getElementById("wWind").textContent = data.wind_speed + " km/h";
        renderForecast(data.rain_3days, data.temp_max, data.temp_min);
        renderRisk(data.farming_risk);
        renderAdvice(data.farming_advice);
        result.style.display = "block";
    }
    async function fetchByCoords(lat, lon) {
        setLoading(true);
        try {
            var resp = await fetch("/api/weather/coords?lat=" + lat + "&lon=" + lon);
            var data = await resp.json();
            if (data.error) showError(data.error);
            else { input.value = data.location + (data.country ? ", " + data.country : ""); renderWeather(data); }
        } catch (err) { showError("Network error. Please check your connection."); }
        finally { setLoading(false); }
    }
    async function fetchByName() {
        var location = input.value.trim();
        if (!location) { showError("Please enter a location name."); return; }
        setLoading(true);
        try {
            var resp = await fetch("/api/weather?location=" + encodeURIComponent(location));
            var data = await resp.json();
            if (data.error) showError(data.error); else renderWeather(data);
        } catch (err) { showError("Network error. Please check your connection."); }
        finally { setLoading(false); }
    }
    function tryGeolocation() {
        if (!navigator.geolocation) { input.value = "Gitega, Burundi"; fetchByName(); return; }
        setLoading(true);
        navigator.geolocation.getCurrentPosition(
            function (pos) { fetchByCoords(pos.coords.latitude, pos.coords.longitude); },
            function (err) {
                setLoading(false);
                if (err.code === err.PERMISSION_DENIED) { input.placeholder = "Location denied — type your city"; input.focus(); }
                else { input.value = "Gitega, Burundi"; fetchByName(); }
            },
            { enableHighAccuracy: true, timeout: 8000, maximumAge: 300000 }
        );
    }
    btn.addEventListener("click", fetchByName);
    input.addEventListener("keydown", function (e) { if (e.key === "Enter") fetchByName(); });
    tryGeolocation();
})();

/* ============================================================
   AI Agronomist Chat
   ============================================================ */
(function () {
    var messagesEl = document.getElementById("chatMessages");
    var inputEl = document.getElementById("chatInput");
    var sendBtn = document.getElementById("chatSendBtn");
    if (!messagesEl || !inputEl) return;
    var history = [];
    function scrollBottom() { messagesEl.scrollTop = messagesEl.scrollHeight; }
    function addMessage(role, text) {
        if (role === "user") { var sugg = document.getElementById("chatSuggestions"); if (sugg) sugg.remove(); }
        var wrapper = document.createElement("div"); wrapper.className = "chat-msg chat-msg--" + role;
        var bubble = document.createElement("div"); bubble.className = "chat-msg-bubble"; bubble.textContent = text;
        wrapper.appendChild(bubble); messagesEl.appendChild(wrapper); scrollBottom();
    }
    function showTyping() {
        var el = document.createElement("div"); el.className = "chat-msg chat-msg--ai"; el.id = "typingIndicator";
        el.innerHTML = '<div class="chat-typing"><div class="chat-typing-dot"></div><div class="chat-typing-dot"></div><div class="chat-typing-dot"></div></div>';
        messagesEl.appendChild(el); scrollBottom();
    }
    function removeTyping() { var el = document.getElementById("typingIndicator"); if (el) el.remove(); }
    async function sendMessage(text) {
        text = text.trim(); if (!text) return;
        inputEl.value = ""; sendBtn.disabled = true; inputEl.disabled = true;
        addMessage("user", text); history.push({ role: "user", content: text }); showTyping();
        try {
            var resp = await fetch("/api/chat", {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text, context: window.CROP_CONTEXT || {}, history: history.slice(-10), analysis_id: window.ANALYSIS_ID || null })
            });
            var data = await resp.json();
            removeTyping();
            if (data.error) { addMessage("ai", "Sorry: " + data.error); }
            else { addMessage("ai", data.reply); history.push({ role: "model", content: data.reply }); }
        } catch (err) { removeTyping(); addMessage("ai", "Network error. Please check your connection and try again."); }
        finally { sendBtn.disabled = false; inputEl.disabled = false; inputEl.focus(); }
    }
    sendBtn.addEventListener("click", function () { sendMessage(inputEl.value); });
    inputEl.addEventListener("keydown", function (e) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(inputEl.value); } });
    window.askSuggestion = function (btn) { sendMessage(btn.textContent); };
    window.sendChatMessage = function () { sendMessage(inputEl.value); };
    scrollBottom();
})();

/* ============================================================
   Unread message badge — polls every 30s
   ============================================================ */
(function () {
    var badge = document.getElementById("unreadBadge");
    if (!badge) return;
    function poll() {
        fetch("/community/api/unread")
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (d.unread > 0) {
                    badge.textContent = d.unread;
                    badge.style.display = "inline";
                } else {
                    badge.style.display = "none";
                }
            })
            .catch(function () {});
    }
    poll();
    setInterval(poll, 30000);
})();

/* ============================================================
   Theme toggle — light / dark
   ============================================================ */
function toggleTheme() {
    var html    = document.documentElement;
    var current = html.getAttribute('data-theme') || 'dark';
    var next    = current === 'dark' ? 'light' : 'dark';

    // Apply immediately — no page reload needed
    html.setAttribute('data-theme', next);

    // Update icons
    var icon       = document.getElementById('themeIcon');
    var mobileIcon = document.getElementById('mobileThemeIcon');
    if (icon)       icon.textContent       = next === 'light' ? '🌙' : '☀️';
    if (mobileIcon) mobileIcon.textContent = next === 'light' ? '🌙 Sombre' : '☀️ Clair';

    // Save to server (persists across sessions)
    fetch('/set-theme/' + next, { method: 'POST' }).catch(function(){});
}

/* ============================================================
   Notification bell badge — polls every 30s
   ============================================================ */
(function () {
    var badge = document.getElementById("notifBadge");
    if (!badge) return;
    function poll() {
        fetch("/api/notifications/unread")
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (d.unread > 0) {
                    badge.textContent = d.unread;
                    badge.style.display = "inline";
                } else {
                    badge.style.display = "none";
                }
            }).catch(function () {});
    }
    poll();
    setInterval(poll, 30000);
})();
