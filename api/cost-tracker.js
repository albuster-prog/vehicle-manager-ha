// api/cost-tracker.js
// Vercel serverless function — Cost Tracker pentru Vehicle Manager HA v2
// Stocare: in-memory (demo) — productie: Vercel KV sau Supabase
//
// ENDPOINTS:
//   GET  ?action=categories           — lista categorii + grupuri
//   GET  ?action=stats&vehicle_id=x   — statistici generale
//   GET  ?action=monthly_by_category  — costuri lunare per categorie (12 luni)
//   GET  ?action=vehicles             — lista vehicule
//   GET  ?action=list&vehicle_id=x    — lista intrari
//   POST action=add_vehicle           — adauga vehicul
//   POST (body cu category/amount)    — adauga cost
//   DELETE ?id=xxx                    — sterge intrare

const COST_CATEGORIES = {
  // Intretinere
  spalare:    { label: 'Spalare auto',          icon: 'droplets',     color: '#38bdf8', group: 'intretinere' },
  detailing:  { label: 'Detailing',             icon: 'sparkles',     color: '#a78bfa', group: 'intretinere' },
  aspirare:   { label: 'Aspirare interior',     icon: 'wind',         color: '#67e8f9', group: 'intretinere' },
  // Anvelope
  anvelope:   { label: 'Anvelope',              icon: 'circle-dot',   color: '#fb923c', group: 'anvelope' },
  jante:      { label: 'Jante',                 icon: 'circle',       color: '#f59e0b', group: 'anvelope' },
  echilibrare:{ label: 'Echilibrare/Geometrie', icon: 'settings',     color: '#fbbf24', group: 'anvelope' },
  valve:      { label: 'Valve / Senzori TPMS',  icon: 'gauge',        color: '#fde68a', group: 'anvelope' },
  // Mecanica
  revizie:    { label: 'Revizie periodica',     icon: 'wrench',       color: '#4ade80', group: 'mecanica' },
  ulei:       { label: 'Schimb ulei + filtru',  icon: 'droplet',      color: '#86efac', group: 'mecanica' },
  distributie:{ label: 'Distributie / curea',  icon: 'settings-2',   color: '#6ee7b7', group: 'mecanica' },
  frane:      { label: 'Frane (placute/discuri)',icon: 'circle-x',    color: '#f87171', group: 'mecanica' },
  amortizoare:{ label: 'Amortizoare',           icon: 'arrow-down-up',color: '#fb923c', group: 'mecanica' },
  baterie:    { label: 'Baterie / acumulator',  icon: 'battery',      color: '#facc15', group: 'mecanica' },
  curea_acces:{ label: 'Curea accesorii',       icon: 'rotate-cw',    color: '#a3e635', group: 'mecanica' },
  kit_ambreiaj:{label: 'Kit ambreiaj',          icon: 'layers',       color: '#34d399', group: 'mecanica' },
  racire:     { label: 'Sistem racire',         icon: 'thermometer',  color: '#60a5fa', group: 'mecanica' },
  climatizare:{ label: 'Climatizare / AC',      icon: 'snowflake',    color: '#93c5fd', group: 'mecanica' },
  directie:   { label: 'Directie / servo',      icon: 'steering-wheel',color:'#c4b5fd', group: 'mecanica' },
  // EV
  baterie_hv: { label: 'Baterie HV (EV)',       icon: 'zap',          color: '#22d3ee', group: 'ev' },
  pompa_caldura:{label: 'Pompa de caldura',      icon: 'flame',        color: '#fb7185', group: 'ev' },
  incarcator: { label: 'Cablu / incarcator',    icon: 'plug-zap',     color: '#38bdf8', group: 'ev' },
  // Documente
  itp:        { label: 'ITP',                   icon: 'clipboard-check',color:'#4ade80',group: 'documente' },
  rca:        { label: 'RCA',                   icon: 'shield',       color: '#60a5fa', group: 'documente' },
  casco:      { label: 'CASCO',                 icon: 'credit-card',  color: '#a78bfa', group: 'documente' },
  rovinieta:  { label: 'Rovinieta',             icon: 'map',          color: '#fbbf24', group: 'documente' },
  taxa_drum:  { label: 'Taxa drum / pod',       icon: 'milestone',    color: '#f97316', group: 'documente' },
  // Energie
  combustibil:{ label: 'Combustibil',           icon: 'fuel',         color: '#ef4444', group: 'energie' },
  incarcare:  { label: 'Incarcare electrica',   icon: 'zap',          color: '#22d3ee', group: 'energie' },
  // Altele
  accesorii:  { label: 'Accesorii',             icon: 'package',      color: '#8b5cf6', group: 'altele' },
  vopsire:    { label: 'Vopsire / caroserie',   icon: 'paintbrush',   color: '#ec4899', group: 'altele' },
  geamuri:    { label: 'Geamuri / parbriz',     icon: 'square',       color: '#67e8f9', group: 'altele' },
  altele:     { label: 'Altele',                icon: 'more-horizontal',color:'#9ca3af',group: 'altele' }
};

// VEHICULE PREDEFINITE (fara licenta necesara — owner mode)
const DEFAULT_VEHICLES = [
  { id: 'kia',     name: 'Kia eNiro 2019',  plate: 'IF84SOC', type: 'car', fuel_type: 'ev',  year: 2019 },
  { id: 'avensis', name: 'Toyota Avensis',  plate: 'BX01ABC', type: 'car', fuel_type: 'ice', year: 2008 }
];

if (!global._costStore) {
  global._costStore = {
    entries: [],
    vehicles: [...DEFAULT_VEHICLES]
  };
}

function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
}

function getStats(entries, vehicleId = null) {
  const filtered = vehicleId ? entries.filter(e => e.vehicle_id === vehicleId) : entries;
  const now = new Date();
  const thisYear = now.getFullYear();
  const thisMonth = now.getMonth();

  const totalAll = filtered.reduce((s, e) => s + (e.amount || 0), 0);
  const thisYearTotal = filtered
    .filter(e => new Date(e.date).getFullYear() === thisYear)
    .reduce((s, e) => s + (e.amount || 0), 0);
  const thisMonthTotal = filtered
    .filter(e => {
      const d = new Date(e.date);
      return d.getFullYear() === thisYear && d.getMonth() === thisMonth;
    })
    .reduce((s, e) => s + (e.amount || 0), 0);

  const byCategory = {};
  filtered.forEach(e => {
    if (!byCategory[e.category]) byCategory[e.category] = {
      total: 0, count: 0,
      label: COST_CATEGORIES[e.category]?.label || e.category,
      color: COST_CATEGORIES[e.category]?.color || '#9ca3af'
    };
    byCategory[e.category].total += e.amount || 0;
    byCategory[e.category].count++;
  });

  const byGroup = {};
  filtered.forEach(e => {
    const group = COST_CATEGORIES[e.category]?.group || 'altele';
    if (!byGroup[group]) byGroup[group] = { total: 0, count: 0 };
    byGroup[group].total += e.amount || 0;
    byGroup[group].count++;
  });

  // Trend lunar 12 luni
  const monthlyTrend = [];
  for (let i = 11; i >= 0; i--) {
    const d = new Date(thisYear, thisMonth - i, 1);
    const total = filtered
      .filter(e => {
        const ed = new Date(e.date);
        return ed.getFullYear() === d.getFullYear() && ed.getMonth() === d.getMonth();
      })
      .reduce((s, e) => s + (e.amount || 0), 0);
    monthlyTrend.push({ month: d.toISOString().substr(0, 7), total: Math.round(total * 100) / 100 });
  }

  return {
    total_all_time:   Math.round(totalAll * 100) / 100,
    total_this_year:  Math.round(thisYearTotal * 100) / 100,
    total_this_month: Math.round(thisMonthTotal * 100) / 100,
    entries_count: filtered.length,
    by_category: byCategory,
    by_group: byGroup,
    monthly_trend: monthlyTrend,
    last_entry: filtered.sort((a, b) => new Date(b.date) - new Date(a.date))[0] || null
  };
}

// ── NEW: costuri lunare per categorie (12 luni) ────────────────────────────
function getMonthlyCategoryBreakdown(entries, vehicleId = null) {
  const filtered = vehicleId ? entries.filter(e => e.vehicle_id === vehicleId) : entries;
  const now = new Date();
  const thisYear = now.getFullYear();
  const thisMonth = now.getMonth();

  const months = [];
  for (let i = 11; i >= 0; i--) {
    const d = new Date(thisYear, thisMonth - i, 1);
    months.push(d.toISOString().substr(0, 7));
  }

  // Per luna, per categorie
  const result = months.map(month => {
    const monthEntries = filtered.filter(e => e.date.startsWith(month));
    const cats = {};
    monthEntries.forEach(e => {
      if (!cats[e.category]) cats[e.category] = 0;
      cats[e.category] += e.amount || 0;
    });
    // Round values
    Object.keys(cats).forEach(k => { cats[k] = Math.round(cats[k] * 100) / 100; });
    return {
      month,
      total: Math.round(monthEntries.reduce((s, e) => s + (e.amount || 0), 0) * 100) / 100,
      by_category: cats
    };
  });

  // Top categorii pe tot intervalul
  const topCats = {};
  filtered.forEach(e => {
    if (!topCats[e.category]) topCats[e.category] = {
      total: 0, label: COST_CATEGORIES[e.category]?.label || e.category,
      color: COST_CATEGORIES[e.category]?.color || '#9ca3af'
    };
    topCats[e.category].total += e.amount || 0;
  });
  const sortedCats = Object.entries(topCats)
    .sort((a, b) => b[1].total - a[1].total)
    .slice(0, 10)
    .reduce((obj, [k, v]) => ({ ...obj, [k]: { ...v, total: Math.round(v.total * 100) / 100 } }), {});

  return { months: result, top_categories: sortedCats };
}

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') { res.status(200).end(); return; }

  const store = global._costStore;
  const { action, vehicle_id } = req.query;

  // Asigura vehiculele default exista mereu
  if (store.vehicles.length === 0) {
    store.vehicles = [...DEFAULT_VEHICLES];
  }

  try {
    // ── GET categories ────────────────────────────────────────────────────
    if (req.method === 'GET' && action === 'categories') {
      return res.status(200).json({
        categories: COST_CATEGORIES,
        groups: {
          intretinere: 'Intretinere curenta',
          anvelope:    'Anvelope & roti',
          mecanica:    'Mecanica & revizie',
          ev:          'Electric (EV)',
          documente:   'Documente legale',
          energie:     'Combustibil / Incarcare',
          altele:      'Accesorii & altele'
        }
      });
    }

    // ── GET vehicles ──────────────────────────────────────────────────────
    if (req.method === 'GET' && action === 'vehicles') {
      return res.status(200).json({ vehicles: store.vehicles });
    }

    // ── GET stats ─────────────────────────────────────────────────────────
    if (req.method === 'GET' && action === 'stats') {
      const stats = getStats(store.entries, vehicle_id || null);
      // Stats per vehicul
      const perVehicle = {};
      store.vehicles.forEach(v => {
        perVehicle[v.id] = getStats(store.entries, v.id);
      });
      return res.status(200).json({
        vehicles: store.vehicles,
        stats,
        stats_per_vehicle: perVehicle,
        currency: 'RON'
      });
    }

    // ── GET monthly_by_category (NEW) ─────────────────────────────────────
    if (req.method === 'GET' && action === 'monthly_by_category') {
      const breakdown = getMonthlyCategoryBreakdown(store.entries, vehicle_id || null);
      return res.status(200).json({
        vehicle_id: vehicle_id || 'all',
        currency: 'RON',
        ...breakdown
      });
    }

    // ── GET list ──────────────────────────────────────────────────────────
    if (req.method === 'GET' && (!action || action === 'list')) {
      const limit = parseInt(req.query.limit) || 50;
      let entries = vehicle_id
        ? store.entries.filter(e => e.vehicle_id === vehicle_id)
        : store.entries;
      entries = entries
        .sort((a, b) => new Date(b.date) - new Date(a.date))
        .slice(0, limit);
      return res.status(200).json({ entries, total: store.entries.length });
    }

    // ── POST ──────────────────────────────────────────────────────────────
    if (req.method === 'POST') {
      const body = req.body || {};

      // Add vehicle
      if (action === 'add_vehicle') {
        const { name, plate, type = 'car', year, fuel_type = 'ev' } = body;
        if (!name || !plate) return res.status(400).json({ error: 'name and plate required' });
        const vehicle = {
          id: generateId(),
          name, plate: plate.toUpperCase(), type,
          year: parseInt(year) || null,
          fuel_type, created_at: new Date().toISOString()
        };
        store.vehicles.push(vehicle);
        return res.status(201).json({ success: true, vehicle });
      }

      // Add cost entry
      const { vehicle_id: vid, vehicle_name, category, amount, currency = 'RON', date, mileage, notes } = body;
      if (!category || !amount || !date) {
        return res.status(400).json({ error: 'category, amount and date required' });
      }
      if (!COST_CATEGORIES[category]) {
        return res.status(400).json({
          error: 'Unknown category: ' + category,
          valid_categories: Object.keys(COST_CATEGORIES)
        });
      }

      // Rezolva vehicle_name din vehicule
      const vehicleObj = store.vehicles.find(v => v.id === vid);
      const entry = {
        id: generateId(),
        vehicle_id:       vid || 'kia',
        vehicle_name:     vehicle_name || vehicleObj?.name || 'Kia eNiro 2019',
        category,
        category_label:   COST_CATEGORIES[category].label,
        category_group:   COST_CATEGORIES[category].group,
        category_color:   COST_CATEGORIES[category].color,
        amount:           parseFloat(amount),
        currency,
        date,
        mileage:          mileage ? parseInt(mileage) : null,
        notes:            notes || null,
        created_at:       new Date().toISOString()
      };

      store.entries.push(entry);
      return res.status(201).json({
        success: true, entry,
        stats: getStats(store.entries, vid),
        monthly_breakdown: getMonthlyCategoryBreakdown(store.entries, vid)
      });
    }

    // ── DELETE ────────────────────────────────────────────────────────────
    if (req.method === 'DELETE' && req.query.id) {
      const before = store.entries.length;
      store.entries = store.entries.filter(e => e.id !== req.query.id);
      return res.status(200).json({
        success: store.entries.length < before,
        deleted_id: req.query.id
      });
    }

    return res.status(400).json({ error: 'Unknown action or method' });

  } catch (err) {
    console.error('cost-tracker error:', err);
    return res.status(500).json({ error: 'Internal error', message: err.message });
  }
};
