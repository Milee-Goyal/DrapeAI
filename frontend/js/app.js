// DrapeAI Frontend Application Controller
const API_BASE = "";
let currentToken = localStorage.getItem("drapeai_token") || null;
let currentUser = null;
let currentOutfit = null;

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
    checkAuthStatus();
    loadUserStores();
});

// Toast notification helper
function showToast(message, duration = 3500) {
    const toast = document.getElementById("toast-notification");
    toast.textContent = message;
    toast.style.display = "block";
    setTimeout(() => {
        toast.style.display = "none";
    }, duration);
}

function authHeaders() {
    return currentToken ? { "Authorization": `Bearer ${currentToken}` } : {};
}

// ------------------------------------------------------------------------
// 1. AUTHENTICATION & SESSION MANAGEMENT
// ------------------------------------------------------------------------
async function checkAuthStatus() {
    if (!currentToken) {
        updateAuthDisplay(null);
        return;
    }
    try {
        const res = await fetch(`${API_BASE}/api/auth/me`, {
            headers: authHeaders()
        });
        if (res.ok) {
            const data = await res.json();
            currentUser = data.user;
            updateAuthDisplay(data);
            loadSavedWardrobe();
        } else {
            handleLogout();
        }
    } catch (e) {
        console.error("Auth verification failed:", e);
    }
}

function updateAuthDisplay(data) {
    const loggedInPill = document.getElementById("user-logged-in-pill");
    const loggedOutPill = document.getElementById("user-logged-out-pill");
    const navUsername = document.getElementById("nav-username");
    const authBanner = document.getElementById("auth-reminder-banner");

    if (data && data.user) {
        loggedInPill.style.display = "flex";
        loggedOutPill.style.display = "none";
        authBanner.style.display = "none";
        navUsername.textContent = `${data.user.username}`;

        // Restore portrait if saved in profile
        if (data.profile && data.profile.portrait_url) {
            const preview = document.getElementById("portrait-preview");
            const photoUrl = data.profile.portrait_url + `?t=${Date.now()}`;
            preview.src = photoUrl;
            preview.style.display = "block";
            document.getElementById("view-original-photo").src = photoUrl;
            document.getElementById("view-tryon-photo").src = photoUrl;
        }
    } else {
        loggedInPill.style.display = "none";
        loggedOutPill.style.display = "flex";
        authBanner.style.display = "block";
    }
}

function openAuthModal(tab = "login") {
    document.getElementById("auth-modal-overlay").style.display = "flex";
    switchAuthTab(tab);
}

function closeAuthModal() {
    document.getElementById("auth-modal-overlay").style.display = "none";
}

function switchAuthTab(tab) {
    const tabLogin = document.getElementById("auth-tab-login");
    const tabReg = document.getElementById("auth-tab-register");
    const formLogin = document.getElementById("form-login");
    const formReg = document.getElementById("form-register");

    if (tab === "login") {
        tabLogin.classList.add("active");
        tabReg.classList.remove("active");
        formLogin.style.display = "block";
        formReg.style.display = "none";
    } else {
        tabReg.classList.add("active");
        tabLogin.classList.remove("active");
        formReg.style.display = "block";
        formLogin.style.display = "none";
    }
}

async function submitLogin(e) {
    e.preventDefault();
    const u = document.getElementById("login-user-input").value.trim();
    const p = document.getElementById("login-pass-input").value;

    try {
        const res = await fetch(`${API_BASE}/api/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: u, password: p })
        });
        const data = await res.json();
        if (res.ok) {
            currentToken = data.access_token;
            localStorage.setItem("drapeai_token", currentToken);
            currentUser = data.user;
            closeAuthModal();
            showToast(`Welcome back, ${data.user.username}!`);
            checkAuthStatus();
            loadUserStores();
        } else {
            alert(data.detail || "Login failed. Check your username and password.");
        }
    } catch (err) {
        alert("Server communication error.");
    }
}

async function submitRegister(e) {
    e.preventDefault();
    const u = document.getElementById("reg-user-input").value.trim();
    const em = document.getElementById("reg-email-input").value.trim();
    const p = document.getElementById("reg-pass-input").value;

    try {
        const res = await fetch(`${API_BASE}/api/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: u, email: em, password: p })
        });
        const data = await res.json();
        if (res.ok) {
            currentToken = data.access_token;
            localStorage.setItem("drapeai_token", currentToken);
            currentUser = data.user;
            closeAuthModal();
            showToast(`Account created. Welcome, ${data.user.username}!`);
            checkAuthStatus();
            loadUserStores();
        } else {
            alert(data.detail || "Registration failed.");
        }
    } catch (err) {
        alert("Server communication error.");
    }
}

function handleLogout() {
    currentToken = null;
    currentUser = null;
    localStorage.removeItem("drapeai_token");
    updateAuthDisplay(null);
    showToast("Signed out. Private stores and wardrobe secured.");
    loadUserStores();
}

function updateBudgetSlider(val) {
    document.getElementById("budget-badge").textContent = `₹${Number(val).toLocaleString()}`;
}

// ------------------------------------------------------------------------
// 2. PHOTO UPLOAD & OPENCV COLORIMETRY ANALYSIS
// ------------------------------------------------------------------------
async function handlePhotoUpload(input) {
    if (!input.files || input.files.length === 0) return;
    
    if (!currentToken) {
        openAuthModal("login");
        showToast("Please sign in or register to analyze and save your photo.");
        return;
    }

    const file = input.files[0];
    const preview = document.getElementById("portrait-preview");
    const localBlobUrl = URL.createObjectURL(file);
    preview.src = localBlobUrl;
    preview.style.display = "block";
    document.getElementById("view-original-photo").src = localBlobUrl;
    document.getElementById("view-tryon-photo").src = localBlobUrl;

    const formData = new FormData();
    formData.append("file", file);

    showToast("Running OpenCV facial colorimetry analysis...");

    try {
        const res = await fetch(`${API_BASE}/api/profile/upload-portrait`, {
            method: "POST",
            headers: authHeaders(),
            body: formData
        });

        if (res.ok) {
            const data = await res.json();
            displayColorimetryResults(data.colorimetry);
            showToast("Complexion analyzed successfully.");
        } else {
            const err = await res.json();
            alert(err.detail || "Failed to analyze portrait.");
        }
    } catch (e) {
        console.error(e);
        alert("Server connection failed during photo analysis.");
    }
}

function displayColorimetryResults(c) {
    document.getElementById("colorimetry-result-card").style.display = "block";
    document.getElementById("undertone-title").textContent = `${c.undertone} Undertone (${c.skin_hex})`;
    document.getElementById("season-title").textContent = c.color_season;

    const swatchesBox = document.getElementById("palette-swatches-box");
    swatchesBox.innerHTML = "";

    c.recommended_palette.forEach(color => {
        const pill = document.createElement("span");
        pill.className = "color-pill";
        pill.innerHTML = `<span class="color-dot" style="background: ${color.hex}"></span> ${color.name}`;
        swatchesBox.appendChild(pill);
    });
}

// ------------------------------------------------------------------------
// 3. AI OUTFIT FORMULATION & CUSTOM STORE DISCOVERY
// ------------------------------------------------------------------------
async function generateOutfit() {
    if (!currentToken) {
        openAuthModal("login");
        showToast("Please sign in to generate outfits and search your personal stores.");
        return;
    }

    const btn = document.getElementById("generate-outfit-btn");
    btn.disabled = true;
    btn.textContent = "Formulating Outfit & Querying Stores...";

    const reqData = {
        event_type: document.getElementById("event-select").value,
        budget_limit: parseFloat(document.getElementById("budget-range").value),
        city: document.getElementById("city-input").value,
        temperature_c: 28.0,
        weather_condition: "Pleasant"
    };

    try {
        const res = await fetch(`${API_BASE}/api/stylist/generate`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...authHeaders()
            },
            body: JSON.stringify(reqData)
        });

        if (res.ok) {
            currentOutfit = await res.json();
            renderOutfitResults(currentOutfit);
            showToast("Coordinated outfit formulated across your active stores.");
            
            document.getElementById("results-panel").scrollIntoView({ behavior: "smooth" });

            // Automatically render Virtual Try-On onto user photo immediately
            setTimeout(() => {
                executeVirtualTryOn();
            }, 300);
        } else {
            const err = await res.json();
            alert(err.detail || "Error formulating outfit.");
        }
    } catch (e) {
        console.error(e);
        alert("Styling engine server error.");
    } finally {
        btn.disabled = false;
        btn.textContent = "Formulate Outfit & Search Stores";
    }
}

function renderOutfitResults(data) {
    document.getElementById("empty-state-box").style.display = "none";
    document.getElementById("results-panel").style.display = "block";

    document.getElementById("outfit-theme-title").textContent = data.theme;
    document.getElementById("outfit-palette-subtitle").textContent = `Color Theme: ${data.color_theme}`;
    document.getElementById("outfit-rationale-text").textContent = data.styling_notes;

    const summary = data.bundle_summary;
    document.getElementById("bundle-budget-badge").textContent = `Best Bundle: ₹${summary.best_optimized_price.toLocaleString()} (Within ₹${data.budget_limit.toLocaleString()} budget)`;

    const container = document.getElementById("garments-items-container");
    container.innerHTML = "";

    data.items.forEach(item => {
        const card = document.createElement("div");
        card.className = "garment-card";

        let storeRowsHtml = "";
        if (item.ecommerce_matches && item.ecommerce_matches.length > 0) {
            item.ecommerce_matches.forEach(m => {
                storeRowsHtml += `
                    <div class="store-product-row">
                        <div>
                            <span class="store-tag" style="background: ${m.badge_color};">${m.store_name}</span>
                            <div style="font-weight: 700; font-size: 11.5px; margin-top: 3px; color: var(--navy-dark);">${m.product_title.slice(0, 32)}...</div>
                            <div style="font-size: 10px; color: var(--text-muted);">Match: ${(m.similarity_score * 100).toFixed(0)}% | Rating: ${m.rating}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-weight: 800; font-size: 13px; color: var(--navy-dark);">₹${m.price_inr.toLocaleString()}</div>
                            <a href="${m.product_url}" target="_blank" class="btn btn-outline btn-sm" style="padding: 2px 8px; font-size: 10px; margin-top: 4px;">Buy Online</a>
                        </div>
                    </div>
                `;
            });
        } else {
            storeRowsHtml = `<div style="font-size: 11px; color: var(--text-muted); padding: 8px;">No matches found in your active stores. Try enabling more stores below.</div>`;
        }

        card.innerHTML = `
            <span style="font-size: 10px; font-weight: 800; background: #F1F5F9; color: var(--navy-light); padding: 2px 8px; border-radius: 4px; text-transform: uppercase;">${item.category}</span>
            <h4 style="font-size: 15px; font-weight: 700; color: var(--navy-dark); margin: 6px 0 2px 0;">${item.item_name}</h4>
            <div style="display: flex; align-items: center; gap: 6px; font-size: 12px; margin-bottom: 6px;">
                <span class="color-dot" style="background: ${item.color_hex};"></span>
                <span>${item.color_name} • ${item.fabric}</span>
            </div>
            <p style="font-size: 11px; color: var(--text-secondary); margin-bottom: 12px;">${item.style_tip}</p>
            <div style="font-size: 11px; font-weight: 700; color: var(--navy-dark); margin-bottom: 4px;">Price On Your Stores:</div>
            ${storeRowsHtml}
        `;
        container.appendChild(card);
    });

    const syncStrip = document.getElementById("cart-sync-buttons-strip");
    syncStrip.innerHTML = "";
    
    const presentStores = new Set();
    data.items.forEach(it => (it.ecommerce_matches || []).forEach(m => presentStores.add(m.store_name)));
    
    presentStores.forEach(sName => {
        const btn = document.createElement("button");
        btn.className = "btn btn-outline btn-sm";
        btn.textContent = `Sync to ${sName}`;
        btn.onclick = () => syncBundleToStoreCart(sName);
        syncStrip.appendChild(btn);
    });
}

// ------------------------------------------------------------------------
// 4. VIRTUAL TRY-ON ENGINE (Photorealistic Garment Draping)
// ------------------------------------------------------------------------
async function executeVirtualTryOn() {
    if (!currentToken) {
        openAuthModal("login");
        showToast("Please sign in or register to render Virtual Try-On.");
        return;
    }
    if (!currentOutfit) {
        showToast("Please formulate an outfit first.");
        return;
    }

    const btn = document.getElementById("trigger-tryon-btn");
    btn.disabled = true;
    btn.textContent = "Rendering Virtual Try-On...";

    try {
        const res = await fetch(`${API_BASE}/api/tryon/render/${currentOutfit.outfit_id}`, {
            method: "POST",
            headers: authHeaders()
        });

        if (res.ok) {
            const data = await res.json();
            const freshUrl = data.tryon_image_url + `?t=${Date.now()}`;
            document.getElementById("view-tryon-photo").src = freshUrl;
            document.getElementById("view-original-photo").src = data.original_photo_url + `?t=${Date.now()}`;
            showToast("Virtual Try-On completed successfully.");
        } else {
            alert("Failed to render Virtual Try-On.");
        }
    } catch (e) {
        console.error(e);
        alert("Virtual Try-On service error.");
    } finally {
        btn.disabled = false;
        btn.textContent = "Render Virtual Try-On";
    }
}

async function applyTryonColor(hex, name, btnElement) {
    if (!currentOutfit) {
        showToast("Please formulate an outfit first.");
        return;
    }
    if (!currentToken) {
        openAuthModal("login");
        showToast("Please sign in or register to render Virtual Try-On.");
        return;
    }

    if (btnElement) {
        document.querySelectorAll("#tryon-live-chips .palette-chip").forEach(el => el.classList.remove("active"));
        btnElement.classList.add("active");
    }

    const header = document.getElementById("tryon-view-header");
    if (header) header.textContent = `DrapeAI Virtual Fit (${name})`;

    showToast(`Draping ${name} onto your photo...`, 1500);

    try {
        const res = await fetch(`${API_BASE}/api/tryon/recolor/${currentOutfit.outfit_id}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...authHeaders()
            },
            body: JSON.stringify({ color_hex: hex, color_name: name })
        });

        if (res.ok) {
            const data = await res.json();
            const freshUrl = data.tryon_image_url + `?t=${Date.now()}`;
            document.getElementById("view-tryon-photo").src = freshUrl;
            document.getElementById("view-original-photo").src = data.original_photo_url + `?t=${Date.now()}`;
            showToast(`Virtual Try-On updated to ${name}!`);
        } else {
            const err = await res.json();
            alert(err.detail || "Failed to update garment color.");
        }
    } catch (e) {
        console.error("Recolor error:", e);
        showToast("Color drape service error.");
    }
}

// ------------------------------------------------------------------------
// 5. CUSTOM E-COMMERCE STORES MANAGER (ADD / REMOVE / TOGGLE)
// ------------------------------------------------------------------------
async function loadUserStores() {
    const list = document.getElementById("stores-manager-list");
    list.innerHTML = "";

    const defaultFallbackStores = [
        { id: 1, store_name: "Amazon", is_active: true, badge_color: "#FF9900", search_url_template: "https://www.amazon.in/s?k=" },
        { id: 2, store_name: "Myntra", is_active: true, badge_color: "#FF3E6C", search_url_template: "https://www.myntra.com/" },
        { id: 3, store_name: "Flipkart", is_active: true, badge_color: "#2874F0", search_url_template: "https://www.flipkart.com/search?q=" },
        { id: 4, store_name: "Meesho", is_active: true, badge_color: "#9C27B0", search_url_template: "https://www.meesho.com/search?q=" }
    ];

    if (!currentToken) {
        defaultFallbackStores.forEach(s => renderStoreCard(list, s, false));
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/api/stores`, { headers: authHeaders() });
        if (res.ok) {
            const data = await res.json();
            const stores = data.stores.length > 0 ? data.stores : defaultFallbackStores;
            stores.forEach(s => renderStoreCard(list, s, true));
        }
    } catch (e) {
        defaultFallbackStores.forEach(s => renderStoreCard(list, s, false));
    }
}

function renderStoreCard(container, s, isAuthed) {
    const card = document.createElement("div");
    card.className = "custom-store-card";

    card.innerHTML = `
        <div style="flex: 1;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span class="store-tag" style="background: ${s.badge_color || '#102C57'};">${s.store_name}</span>
                <span class="${s.is_active ? 'store-status-active' : 'store-status-inactive'}">
                    ${s.is_active ? 'Active' : 'Disabled'}
                </span>
            </div>
            <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 170px;">
                ${s.search_url_template || 'Auto-search enabled'}
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 6px;">
            <button class="btn btn-outline btn-sm" onclick="toggleStoreStatus(${s.id}, ${s.is_active})" title="Toggle Active/Disabled">
                ${s.is_active ? 'Disable' : 'Enable'}
            </button>
            <button class="btn btn-danger-outline btn-sm" onclick="deleteStore(${s.id}, '${s.store_name}')" title="Remove this store">
                Delete
            </button>
        </div>
    `;
    container.appendChild(card);
}

function openAddStoreModal() {
    if (!currentToken) {
        openAuthModal("login");
        showToast("Please sign in to customize your personal stores list.");
        return;
    }
    document.getElementById("add-store-modal-overlay").style.display = "flex";
}

function closeAddStoreModal() {
    document.getElementById("add-store-modal-overlay").style.display = "none";
}

function fillStorePreset(name, url, color) {
    document.getElementById("new-store-name").value = name;
    document.getElementById("new-store-url").value = url;
    document.getElementById("new-store-name").dataset.color = color;
}

async function submitAddCustomStore(e) {
    e.preventDefault();
    const name = document.getElementById("new-store-name").value.trim();
    const url = document.getElementById("new-store-url").value.trim();
    const color = document.getElementById("new-store-name").dataset.color || "#102C57";

    try {
        const res = await fetch(`${API_BASE}/api/stores/add`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...authHeaders()
            },
            body: JSON.stringify({
                store_name: name,
                search_url_template: url || null,
                badge_color: color
            })
        });

        if (res.ok) {
            closeAddStoreModal();
            showToast(`${name} added to your shopping stores.`);
            loadUserStores();
            document.getElementById("new-store-name").value = "";
            document.getElementById("new-store-url").value = "";
        } else {
            alert("Failed to add store.");
        }
    } catch (err) {
        alert("Server error adding store.");
    }
}

async function toggleStoreStatus(id, currentStatus) {
    if (!currentToken) {
        openAuthModal("login");
        return;
    }
    await fetch(`${API_BASE}/api/stores/${id}/toggle`, {
        method: "PUT",
        headers: authHeaders()
    });
    loadUserStores();
    showToast("Store status updated.");
}

async function deleteStore(id, name) {
    if (!confirm(`Are you sure you want to remove "${name}" from your store list?`)) return;
    if (!currentToken) {
        openAuthModal("login");
        return;
    }
    await fetch(`${API_BASE}/api/stores/${id}`, {
        method: "DELETE",
        headers: authHeaders()
    });
    loadUserStores();
    showToast(`${name} removed from your stores.`);
}

// ------------------------------------------------------------------------
// 6. SINGLE-CLICK CART SYNC & WARDROBE
// ------------------------------------------------------------------------
async function syncBundleToStoreCart(storeName) {
    if (!currentOutfit) return;
    try {
        const res = await fetch(`${API_BASE}/api/ecommerce/sync-bundle/${currentOutfit.outfit_id}?store_name=${storeName}`, {
            method: "POST",
            headers: authHeaders()
        });

        if (res.ok) {
            const data = await res.json();
            showToast(data.message, 4500);
            setTimeout(() => {
                if (confirm(`Open ${storeName} cart now?`)) {
                    window.open(data.direct_store_checkout_url, "_blank");
                }
            }, 600);
        }
    } catch (e) {
        alert("Failed to sync cart.");
    }
}

async function saveLookToWardrobe() {
    if (!currentOutfit) return;
    try {
        const res = await fetch(`${API_BASE}/api/wardrobe/save`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...authHeaders()
            },
            body: JSON.stringify({
                outfit_id: currentOutfit.outfit_id,
                title: `${currentOutfit.event_type} - ${currentOutfit.theme}`
            })
        });

        if (res.ok) {
            showToast("Look saved to Private Wardrobe.");
            loadSavedWardrobe();
        }
    } catch (e) {
        alert("Failed to save wardrobe look.");
    }
}

async function loadSavedWardrobe() {
    if (!currentToken) return;
    try {
        const res = await fetch(`${API_BASE}/api/wardrobe/my-looks`, {
            headers: authHeaders()
        });
        if (res.ok) {
            const data = await res.json();
            const grid = document.getElementById("wardrobe-cards-grid");
            if (data.saved_looks.length === 0) {
                grid.innerHTML = `<p style="color: var(--text-muted); font-size: 14px;">No saved looks yet. Formulate an outfit above and click "Save to Wardrobe".</p>`;
                return;
            }
            grid.innerHTML = "";
            data.saved_looks.forEach(look => {
                const card = document.createElement("div");
                card.className = "card-box";
                card.style.padding = "16px";
                card.innerHTML = `
                    <img src="${(look.tryon_preview || '/static/default_user.jpg') + '?t=' + Date.now()}" style="width: 100%; height: 220px; object-fit: cover; border-radius: 8px; margin-bottom: 10px; border: 1px solid var(--border);">
                    <h4 style="font-size: 14px; font-weight: 700; color: var(--navy-dark);">${look.title}</h4>
                    <div style="font-size: 12px; color: var(--gold); font-weight: 700; margin-top: 4px;">Total Look Cost: ₹${look.total_cost.toLocaleString()}</div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 12px;">
                        <span style="font-size: 11px; color: var(--success); font-weight: 700;">Saved Look</span>
                        <button class="btn btn-danger-outline btn-sm" onclick="deleteSavedLook(${look.id})">Delete</button>
                    </div>
                `;
                grid.appendChild(card);
            });
        }
    } catch (e) {
        console.error("Wardrobe loader error:", e);
    }
}

async function deleteSavedLook(id) {
    if (!confirm("Remove this look from wardrobe?")) return;
    await fetch(`${API_BASE}/api/wardrobe/${id}`, {
        method: "DELETE",
        headers: authHeaders()
    });
    loadSavedWardrobe();
    showToast("Look deleted from wardrobe.");
}
