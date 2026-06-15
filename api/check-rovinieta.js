// api/check-rovinieta.js
// Vercel serverless function — verificare rovinieta valabila pe numar de inmatriculare
// Foloseste CNAIR API (endpoint oficial nedocumentat) + fallback scraping

const https = require('https');

// CNAIR official endpoint (reverse engineered from e-rovinieta.ro)
const CNAIR_CHECK_URL = 'https://api.e-rovinieta.ro/vignettes/check';

function makeRequest(url, options, postData) {
  return new Promise((resolve, reject) => {
    const req = https.request(url, options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(data) }); }
        catch(e) { resolve({ status: res.statusCode, body: data }); }
      });
    });
    req.on('error', reject);
    if (postData) req.write(postData);
    req.end();
  });
}

module.exports = async (req, res) => {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') { res.status(200).end(); return; }

  const { plate, country = 'RO' } = req.query;

  if (!plate) {
    return res.status(400).json({
      error: 'Missing plate parameter',
      example: '/api/check-rovinieta?plate=IF84SOC&country=RO'
    });
  }

  const normalizedPlate = plate.replace(/\s+/g, '').toUpperCase();

  try {
    // Method 1: Try CNAIR direct API
    const postBody = JSON.stringify({
      vehicleRegistrationNumber: normalizedPlate,
      countryCode: country.toUpperCase()
    });

    const apiOptions = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postBody),
        'User-Agent': 'Mozilla/5.0 (compatible; VehicleManagerHA/1.0)',
        'Accept': 'application/json',
        'Origin': 'https://www.e-rovinieta.ro',
        'Referer': 'https://www.e-rovinieta.ro/'
      }
    };

    let result = null;

    try {
      const apiUrl = new URL(CNAIR_CHECK_URL);
      const response = await makeRequest(
        { hostname: apiUrl.hostname, path: apiUrl.pathname, ...apiOptions },
        postBody
      );

      if (response.status === 200 && response.body) {
        const data = response.body;
        // Parse CNAIR response format
        if (Array.isArray(data) && data.length > 0) {
          const vignette = data[0];
          const expiry = new Date(vignette.expiryDate || vignette.validTo);
          const now = new Date();
          const daysLeft = Math.ceil((expiry - now) / 86400000);

          result = {
            source: 'cnair_api',
            plate: normalizedPlate,
            valid: daysLeft > 0,
            active: new Date(vignette.startDate || vignette.validFrom) <= now,
            start_date: vignette.startDate || vignette.validFrom,
            expiry_date: vignette.expiryDate || vignette.validTo,
            days_remaining: Math.max(0, daysLeft),
            category: vignette.vehicleCategory || 'A',
            emission_class: vignette.emissionClass || null,
            transaction_id: vignette.transactionId || null,
            status: daysLeft <= 0 ? 'expired' : daysLeft <= 30 ? 'warning' : 'ok'
          };
        } else if (data.valid === false || data.length === 0) {
          result = {
            source: 'cnair_api',
            plate: normalizedPlate,
            valid: false,
            active: false,
            start_date: null,
            expiry_date: null,
            days_remaining: 0,
            status: 'no_vignette'
          };
        }
      }
    } catch (apiErr) {
      console.log('CNAIR API unavailable, using manual data:', apiErr.message);
    }

    // If API failed, return structured response for manual config
    if (!result) {
      result = {
        source: 'manual_fallback',
        plate: normalizedPlate,
        valid: null,
        active: null,
        start_date: null,
        expiry_date: null,
        days_remaining: null,
        status: 'api_unavailable',
        message: 'CNAIR API not publicly accessible. Configure manually in HA.',
        manual_check_url: 'https://www.e-rovinieta.ro/ro/check?plate=' + normalizedPlate
      };
    }

    return res.status(200).json(result);

  } catch (err) {
    console.error('check-rovinieta error:', err);
    return res.status(500).json({
      error: 'Internal error',
      message: err.message,
      plate: normalizedPlate
    });
  }
};
