/**
 * PriceCraft AI - Frontend Application Controller
 * Handles user interactions, API orchestration, inventory management, and telemetry views.
 */

// Global State
let currentAnalysis = null;
let currentItemData = null;
let presetsList = [];
let elasticityChart = null;

document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) {
    lucide.createIcons();
  }
  setupEventListeners();
  loadPresets();
  loadInventory();
  refreshTraces();
});

// Setup Form & Slider Listeners
function setupEventListeners() {
  // Navigation tabs
  document.getElementById("nav-pricing-btn").addEventListener("click", () => switchView("pricing"));
  document.getElementById("nav-inventory-btn").addEventListener("click", () => switchView("inventory"));
  document.getElementById("nav-telemetry-btn").addEventListener("click", () => switchView("telemetry"));

  // CSV Export
  const exportBtn = document.getElementById("export-csv-btn");
  if (exportBtn) {
    exportBtn.addEventListener("click", () => {
      window.location.href = "/api/inventory/export";
      showToast("Downloading inventory CSV...");
    });
  }

  // Condition slider
  const condInput = document.getElementById("input-condition");
  const condVal = document.getElementById("condition-val");
  condInput.addEventListener("input", (e) => {
    const val = parseFloat(e.target.value);
    let desc = "Fair";
    if (val >= 9.5) desc = "Deadstock / NIB";
    else if (val >= 8.5) desc = "Very Good";
    else if (val >= 7.0) desc = "Good Pre-owned";
    else if (val >= 5.0) desc = "Fair";
    else desc = "Parts / Flawed";
    condVal.textContent = `${val.toFixed(1)} / 10 (${desc})`;
  });

  // Brand Tier slider
  const brandTierInput = document.getElementById("input-brand-tier");
  const brandTierVal = document.getElementById("brand-tier-val");
  brandTierInput.addEventListener("input", (e) => {
    const val = parseFloat(e.target.value);
    let label = "Mid-Tier";
    if (val >= 4.0) label = "Tier 4 (Luxury / Grail)";
    else if (val >= 3.0) label = "Tier 3 (Hype / Sought-After)";
    else if (val >= 2.0) label = "Tier 2 (Mall Brand)";
    else label = "Tier 1 (Budget / Generic)";
    brandTierVal.textContent = label;
  });

  // Rarity slider
  const rarityInput = document.getElementById("input-rarity");
  const rarityVal = document.getElementById("rarity-val");
  rarityInput.addEventListener("input", (e) => {
    const val = parseFloat(e.target.value);
    rarityVal.textContent = `${val.toFixed(1)} / 5 (${val >= 4 ? 'Ultra Rare' : val >= 3 ? 'Uncommon' : 'Common'})`;
  });

  // Demand slider
  const demandInput = document.getElementById("input-demand");
  const demandVal = document.getElementById("demand-val");
  demandInput.addEventListener("input", (e) => {
    const val = parseFloat(e.target.value);
    demandVal.textContent = `${val.toFixed(1)} / 5 (${val >= 4 ? 'High Surge' : val >= 3 ? 'Steady' : 'Slow'})`;
  });

  // Reset button
  document.getElementById("clear-form-btn").addEventListener("click", (e) => {
    e.preventDefault();
    document.getElementById("item-form").reset();
    document.getElementById("input-condition").dispatchEvent(new Event("input"));
    document.getElementById("input-brand-tier").dispatchEvent(new Event("input"));
    document.getElementById("input-rarity").dispatchEvent(new Event("input"));
    document.getElementById("input-demand").dispatchEvent(new Event("input"));
  });

  // Form submit
  document.getElementById("item-form").addEventListener("submit", handleFormSubmit);

  // ElevenLabs Voiceover Button
  document.getElementById("generate-voice-btn").addEventListener("click", handleVoiceoverGeneration);

  // Save to inventory button
  document.getElementById("save-inventory-btn").addEventListener("click", handleSaveInventory);
}

// Switch Active View
function switchView(viewName) {
  const views = {
    pricing: document.getElementById("pricing-view"),
    inventory: document.getElementById("inventory-view"),
    telemetry: document.getElementById("telemetry-view"),
  };
  const tabs = {
    pricing: document.getElementById("nav-pricing-btn"),
    inventory: document.getElementById("nav-inventory-btn"),
    telemetry: document.getElementById("nav-telemetry-btn"),
  };

  Object.keys(views).forEach((k) => {
    if (k === viewName) {
      views[k].classList.remove("hidden");
      tabs[k].classList.add("active");
      tabs[k].classList.remove("text-slate-400");
    } else {
      views[k].classList.add("hidden");
      tabs[k].classList.remove("active");
      tabs[k].classList.add("text-slate-400");
    }
  });

  if (viewName === "inventory") {
    loadInventory();
  } else if (viewName === "telemetry") {
    refreshTraces();
  }
}

// Load Preset Items
async function loadPresets() {
  try {
    const res = await fetch("/api/presets");
    presetsList = await res.json();
    const container = document.getElementById("presets-container");
    container.innerHTML = "";

    presetsList.forEach((preset) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "preset-btn group";
      btn.innerHTML = `
        <div class="flex items-center justify-between">
          <span class="text-[10px] font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">
            ${preset.category_badge}
          </span>
          <i data-lucide="chevron-right" class="w-3.5 h-3.5 text-slate-500 group-hover:text-emerald-400 group-hover:translate-x-0.5 transition-all"></i>
        </div>
        <div class="font-semibold text-xs text-slate-200 mt-1 truncate group-hover:text-white">
          ${preset.name}
        </div>
        <div class="text-[11px] text-slate-400 mt-0.5 flex justify-between">
          <span>Cost: $${preset.data.purchase_cost}</span>
          <span class="text-emerald-400 font-bold">1-Click Test</span>
        </div>
      `;
      btn.addEventListener("click", () => populatePreset(preset.data));
      container.appendChild(btn);
    });

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error("Failed to load presets:", err);
  }
}

// Populate Preset into Input Form
function populatePreset(data) {
  document.getElementById("input-title").value = data.title;
  document.getElementById("input-brand").value = data.brand;
  document.getElementById("input-category").value = data.category;
  document.getElementById("input-condition").value = data.condition_score;
  document.getElementById("input-purchase-cost").value = data.purchase_cost;
  document.getElementById("input-retail-cost").value = data.original_retail_usd;
  document.getElementById("input-brand-tier").value = data.brand_tier;
  document.getElementById("input-rarity").value = data.rarity_score;
  document.getElementById("input-age").value = data.age_years;
  document.getElementById("input-demand").value = data.demand_trend;
  document.getElementById("input-notes").value = data.condition_notes;
  document.getElementById("input-features").value = data.features;
  document.getElementById("input-shipping").checked = data.shipping_included;

  // Trigger input events for labels
  document.getElementById("input-condition").dispatchEvent(new Event("input"));
  document.getElementById("input-brand-tier").dispatchEvent(new Event("input"));
  document.getElementById("input-rarity").dispatchEvent(new Event("input"));
  document.getElementById("input-demand").dispatchEvent(new Event("input"));

  showToast(`Loaded "${data.title.substring(0, 30)}..." preset!`);
}

// Handle Form Submission & Run Multi-Agent Valuation
async function handleFormSubmit(e) {
  e.preventDefault();

  const itemData = {
    title: document.getElementById("input-title").value.trim(),
    brand: document.getElementById("input-brand").value.trim(),
    category: document.getElementById("input-category").value,
    condition_score: parseFloat(document.getElementById("input-condition").value),
    condition_notes: document.getElementById("input-notes").value.trim(),
    features: document.getElementById("input-features").value.trim(),
    original_retail_usd: parseFloat(document.getElementById("input-retail-cost").value) || 100.0,
    purchase_cost: parseFloat(document.getElementById("input-purchase-cost").value) || 0.0,
    brand_tier: parseFloat(document.getElementById("input-brand-tier").value),
    rarity_score: parseFloat(document.getElementById("input-rarity").value),
    age_years: parseFloat(document.getElementById("input-age").value) || 1.0,
    demand_trend: parseFloat(document.getElementById("input-demand").value),
    shipping_included: document.getElementById("input-shipping").checked,
  };

  currentItemData = itemData;

  // Toggle Loading State
  document.getElementById("empty-state-card").classList.add("hidden");
  document.getElementById("results-container").classList.add("hidden");
  document.getElementById("loading-card").classList.remove("hidden");

  const steps = [
    "Querying Prior Labs TabPFN-3.5 Tabular Model...",
    "Scanning SerpApi Live Market Radar for Comps...",
    "Executing Google Gemma 2 Copywriting Engine...",
    "Calculating Profit Margins & Unit Economics..."
  ];

  let stepIdx = 0;
  const stepInterval = setInterval(() => {
    stepIdx = (stepIdx + 1) % steps.length;
    document.getElementById("loading-step-text").textContent = steps[stepIdx];
  }, 700);

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(itemData),
    });

    clearInterval(stepInterval);

    if (!res.ok) {
      throw new Error(`Server returned HTTP ${res.status}`);
    }

    const data = await res.json();
    currentAnalysis = data;

    renderResults(data);
    showToast("Valuation & listing generated successfully!");
  } catch (err) {
    clearInterval(stepInterval);
    console.error("Valuation error:", err);
    alert(`Failed to complete analysis: ${err.message}`);
  } finally {
    document.getElementById("loading-card").classList.add("hidden");
  }
}

// Render Results Dashboard
function renderResults(res) {
  const { valuation, market_comps, listing, unit_economics } = res;

  // 1. TabPFN Valuation Box
  document.getElementById("tabpfn-confidence").textContent = `${valuation.confidence_score}%`;
  document.getElementById("res-optimal-price").textContent = `$${valuation.optimal_price.toFixed(2)}`;
  document.getElementById("res-quick-price").textContent = `$${valuation.quick_sale_price.toFixed(2)}`;
  document.getElementById("res-patient-price").textContent = `$${valuation.patient_price.toFixed(2)}`;
  document.getElementById("res-est-days").textContent = valuation.estimated_days_on_market;

  document.getElementById("res-prob-val").textContent = `${valuation.sale_probability_14d}%`;
  document.getElementById("res-prob-bar").style.width = `${valuation.sale_probability_14d}%`;

  // Render Factor Badges
  const factorsContainer = document.getElementById("res-factors-container");
  factorsContainer.innerHTML = "";
  valuation.factors.forEach((f) => {
    const badge = document.createElement("span");
    const isPos = f.sentiment === "positive";
    badge.className = `text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
      isPos ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-red-500/10 text-red-400 border-red-500/20"
    }`;
    badge.textContent = `${f.factor} (${f.impact})`;
    factorsContainer.appendChild(badge);
  });

  // Financial Unit Economics
  document.getElementById("res-cost").textContent = `$${unit_economics.purchase_cost.toFixed(2)}`;
  document.getElementById("res-fee").textContent = `$${unit_economics.platform_fee.toFixed(2)}`;
  document.getElementById("res-shipping").textContent = `$${unit_economics.est_shipping_cost.toFixed(2)}`;
  document.getElementById("res-net-profit").textContent = `+$${unit_economics.net_profit_usd.toFixed(2)}`;
  document.getElementById("res-roi").textContent = `(${unit_economics.roi_percent}% ROI)`;

  // 2. SerpApi Market Radar
  document.getElementById("res-comps-engine").textContent = market_comps.source_engine;
  document.getElementById("res-comp-min").textContent = `$${market_comps.min_competitor_price.toFixed(2)}`;
  document.getElementById("res-comp-avg").textContent = `$${market_comps.avg_competitor_price.toFixed(2)}`;
  document.getElementById("res-comp-max").textContent = `$${market_comps.max_competitor_price.toFixed(2)}`;

  const compsList = document.getElementById("res-competitors-list");
  compsList.innerHTML = "";
  market_comps.competitors.forEach((c) => {
    const div = document.createElement("div");
    div.className = "flex items-center justify-between p-2 bg-slate-950/60 rounded-lg border border-slate-800 text-xs";
    div.innerHTML = `
      <div class="truncate max-w-[280px]">
        <div class="font-medium text-slate-200 truncate">${c.title}</div>
        <div class="text-[10px] text-slate-400">${c.source} &bull; Rating: ⭐ ${c.rating}</div>
      </div>
      <div class="font-bold text-emerald-400 ml-2 whitespace-nowrap">$${c.price.toFixed(2)}</div>
    `;
    compsList.appendChild(div);
  });

  // 3. Google Gemma 2 Copywriting Box
  document.getElementById("res-gemma-badge").textContent = listing.engine;
  const ebayTitle = listing.ebay_title;
  document.getElementById("res-ebay-title").textContent = ebayTitle;
  document.getElementById("ebay-char-count").textContent = `${ebayTitle.length} / 80`;
  document.getElementById("res-etsy-title").textContent = listing.etsy_title;

  const specsList = document.getElementById("res-bullet-specs");
  specsList.innerHTML = "";
  listing.bullet_specs.forEach((spec) => {
    const li = document.createElement("li");
    li.textContent = spec;
    specsList.appendChild(li);
  });

  document.getElementById("res-description").textContent = listing.description_markdown;

  const tagsContainer = document.getElementById("res-tags-container");
  tagsContainer.innerHTML = "";
  listing.search_tags.forEach((tag) => {
    const span = document.createElement("span");
    span.className = "text-[11px] font-medium bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full border border-slate-700 cursor-pointer hover:border-emerald-500 transition-colors";
    span.textContent = `#${tag}`;
    span.onclick = () => copyTextToClipboard(tag, `Tag #${tag} copied!`);
    tagsContainer.appendChild(span);
  });

  // 4. ElevenLabs Voiceover Script Hook
  document.getElementById("res-social-hook").textContent = `"${listing.social_hook}"`;
  document.getElementById("audio-player-wrapper").classList.add("hidden");

  // Render Price Elasticity & Liquidity Curve Chart
  if (valuation.elasticity_curve && window.Chart) {
    renderElasticityChart(valuation.elasticity_curve);
  }

  // Show Results Container
  document.getElementById("results-container").classList.remove("hidden");

  if (window.lucide) lucide.createIcons();
}

// Render Price Elasticity Curve with Chart.js
function renderElasticityChart(curve) {
  const canvas = document.getElementById("elasticity-chart");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  if (elasticityChart) {
    elasticityChart.destroy();
  }

  const labels = curve.map(c => `$${c.price.toFixed(0)} (${c.label})`);
  const dataPoints = curve.map(c => c.probability);

  elasticityChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "14-Day Sale Probability (%)",
          data: dataPoints,
          borderColor: "#10b981",
          backgroundColor: "rgba(16, 185, 129, 0.12)",
          fill: true,
          tension: 0.35,
          pointBackgroundColor: "#10b981",
          pointBorderColor: "#ffffff",
          pointBorderWidth: 1.5,
          pointRadius: 4,
          pointHoverRadius: 6,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#0f172a",
          titleColor: "#f8fafc",
          bodyColor: "#34d399",
          borderColor: "#334155",
          borderWidth: 1,
          padding: 8,
          displayColors: false,
          callbacks: {
            label: (ctx) => `Liquidity Probability: ${ctx.parsed.y}%`
          }
        }
      },
      scales: {
        x: {
          grid: { color: "rgba(51, 65, 85, 0.3)" },
          ticks: { color: "#94a3b8", font: { size: 10 } }
        },
        y: {
          min: 0,
          max: 100,
          grid: { color: "rgba(51, 65, 85, 0.3)" },
          ticks: {
            color: "#94a3b8",
            font: { size: 10 },
            callback: (v) => `${v}%`
          }
        }
      }
    }
  });
}

// Generate Voiceover Promo
async function handleVoiceoverGeneration() {
  if (!currentAnalysis) return;
  const hook = currentAnalysis.listing.social_hook;
  const btn = document.getElementById("generate-voice-btn");
  const statusEl = document.getElementById("voice-status");

  btn.disabled = true;
  btn.innerHTML = `<span class="animate-pulse">Synthesizing audio...</span>`;

  try {
    const res = await fetch("/api/voiceover", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ script: hook }),
    });
    const data = await res.json();
    if (data.audio_base64) {
      const player = document.getElementById("promo-audio-player");
      player.src = data.audio_base64;
      document.getElementById("audio-player-wrapper").classList.remove("hidden");
      player.play();
      statusEl.textContent = `Voiced by ${data.voice}`;
      showToast("ElevenLabs audio clip generated!");
    } else {
      statusEl.textContent = "Audio synthesized (connect ELEVENLABS_API_KEY for live mp3 stream)";
      showToast("Voice script synthesized!");
    }
  } catch (err) {
    console.error("Voiceover error:", err);
    statusEl.textContent = "Generation failed";
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="volume-2" class="w-3.5 h-3.5"></i><span>Generate Voiceover Clip</span>`;
    if (window.lucide) lucide.createIcons();
  }
}

// Save Current Item to Inventory
async function handleSaveInventory() {
  if (!currentAnalysis || !currentItemData) return;

  try {
    const res = await fetch("/api/inventory", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        item_data: currentItemData,
        valuation: currentAnalysis.valuation,
        listing: currentAnalysis.listing,
      }),
    });

    if (res.ok) {
      showToast("Saved to Active Inventory!");
      loadInventory();
    }
  } catch (err) {
    console.error("Failed to save inventory:", err);
  }
}

// Load Inventory Items
async function loadInventory() {
  try {
    const res = await fetch("/api/inventory");
    const items = await res.json();

    document.getElementById("inv-count-badge").textContent = items.length;
    document.getElementById("stat-total-items").textContent = items.length;

    let totalCost = 0;
    let totalVal = 0;

    const tbody = document.getElementById("inventory-tbody");
    tbody.innerHTML = "";

    const emptyMsg = document.getElementById("inventory-empty-msg");
    if (items.length === 0) {
      emptyMsg.classList.remove("hidden");
    } else {
      emptyMsg.classList.add("hidden");
    }

    items.forEach((item) => {
      totalCost += item.purchase_cost || 0;
      totalVal += item.optimal_price || 0;
      const netProfit = (item.optimal_price || 0) - (item.purchase_cost || 0) - ((item.optimal_price || 0) * 0.1325 + 0.3) - 8.50;

      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-800/30 transition-colors";
      tr.innerHTML = `
        <td class="p-3.5 font-medium text-white">
          <div class="truncate max-w-[200px]">${item.title}</div>
          <div class="text-[10px] text-slate-400">${item.brand || 'Unbranded'}</div>
        </td>
        <td class="p-3.5 capitalize text-slate-300">${item.category}</td>
        <td class="p-3.5 text-slate-300 font-mono">$${(item.purchase_cost || 0).toFixed(2)}</td>
        <td class="p-3.5 font-bold text-emerald-400 font-mono text-sm">$${(item.optimal_price || 0).toFixed(2)}</td>
        <td class="p-3.5 text-slate-400 font-mono text-[11px]">$${(item.quick_sale_price || 0).toFixed(0)} - $${(item.patient_price || 0).toFixed(0)}</td>
        <td class="p-3.5 font-bold ${netProfit >= 0 ? 'text-emerald-400' : 'text-red-400'} font-mono">
          +$${netProfit.toFixed(2)}
        </td>
        <td class="p-3.5">
          <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            ${item.status}
          </span>
        </td>
        <td class="p-3.5 text-right">
          <button onclick="deleteInventoryItem(${item.id})" class="text-slate-500 hover:text-red-400 transition-colors p-1" title="Delete Item">
            <i data-lucide="trash-2" class="w-4 h-4"></i>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    document.getElementById("stat-total-cost").textContent = `$${totalCost.toFixed(2)}`;
    document.getElementById("stat-total-value").textContent = `$${totalVal.toFixed(2)}`;
    const totalProfit = totalVal - totalCost - (totalVal * 0.1325) - (items.length * 8.50);
    document.getElementById("stat-total-profit").textContent = `+$${Math.max(totalProfit, 0).toFixed(2)}`;

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error("Failed to load inventory:", err);
  }
}

// Delete Item from Inventory
async function deleteInventoryItem(id) {
  if (!confirm("Are you sure you want to remove this item from your catalog?")) return;
  try {
    const res = await fetch(`/api/inventory/${id}`, { method: "DELETE" });
    if (res.ok) {
      showToast("Item deleted from inventory");
      loadInventory();
    }
  } catch (err) {
    console.error("Delete failed:", err);
  }
}

// Refresh Sentry Agent Telemetry Traces
async function refreshTraces() {
  try {
    const res = await fetch("/api/sentry/traces");
    const data = await res.json();
    const tbody = document.getElementById("traces-tbody");
    tbody.innerHTML = "";

    let totalDuration = 0;
    data.traces.forEach((t) => {
      totalDuration += t.duration_ms || 0;
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="p-3 text-slate-500">${t.timestamp}</td>
        <td class="p-3 font-semibold text-white">${t.step}</td>
        <td class="p-3 text-emerald-400">${t.tool}</td>
        <td class="p-3 text-purple-300">${t.duration_ms} ms</td>
        <td class="p-3">
          <span class="text-[10px] px-1.5 py-0.5 rounded ${t.status === 'ok' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-red-500/20 text-red-300'}">
            ${t.status.toUpperCase()}
          </span>
        </td>
        <td class="p-3 text-slate-400 truncate max-w-[220px]">${JSON.stringify(t.metadata)}</td>
      `;
      tbody.appendChild(tr);
    });

    if (data.traces.length > 0) {
      const avg = Math.round(totalDuration / data.traces.length);
      document.getElementById("trace-avg-latency").textContent = `${avg} ms`;
    }
  } catch (err) {
    console.error("Trace refresh failed:", err);
  }
}

// Copy Helpers
function copyToClipboard(elementId, successMsg) {
  const text = document.getElementById(elementId).textContent.trim();
  copyTextToClipboard(text, successMsg);
}

function copySpecs() {
  if (!currentAnalysis) return;
  const specs = currentAnalysis.listing.bullet_specs.map(s => `• ${s}`).join("\n");
  copyTextToClipboard(specs, "All Specifications Copied!");
}

function copyTags() {
  if (!currentAnalysis) return;
  const tags = currentAnalysis.listing.search_tags.join(", ");
  copyTextToClipboard(tags, "Search Tags Copied (Comma-Separated)!");
}

function copyTextToClipboard(text, msg) {
  navigator.clipboard.writeText(text).then(() => {
    showToast(msg);
  }).catch(() => {
    // Fallback
    const textarea = document.createElement("textarea");
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);
    showToast(msg);
  });
}

// Toast Notification
function showToast(message) {
  const toast = document.getElementById("toast");
  const toastText = document.getElementById("toast-text");
  toastText.textContent = message;
  toast.classList.remove("translate-y-20", "opacity-0");
  toast.classList.add("translate-y-0", "opacity-100");

  setTimeout(() => {
    toast.classList.add("translate-y-20", "opacity-0");
    toast.classList.remove("translate-y-0", "opacity-100");
  }, 2400);
}
