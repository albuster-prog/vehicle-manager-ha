// api/check-insurance.js
// Vercel serverless function — verificare polita RCA activa pe numar de inmatriculare
// Surse: ASF Romania (Autoritatea de Supraveghere Financiara) + AIDA Asigurari

const https = require('https');

// ASF Romania ofera verificare RCA publica
const ASF_API_BASE = 'https://www.asfromania.ro/ro/informatii-consumatori/rca';

function makeGetRequest(hostname, path, headers = {}) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname,
      path,
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; VehicleManagerHA/1.0)',
        'Accept': 'application/json, text/html',
        ...headers
      }
    };
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(data), raw: data }); }
        catch(e) { resolve({ status: res.statusCode, body: null, raw: data }); }
      });
    });
    req.on('error', reject);
    req.end();
  });
}

// Parse Romanian date formats
function parseRoDate(dateStr) {
  if (!dateStr) return null;
  // Try ISO format first
  if (dateStr.match(/^\d{4}-\d{2}-\d{2}/)) return new Date(dateStr);
  // Try DD.MM.YYYY
  const m = dateStr.match(/(\d{2})\.(\d{2})\.(\d{4})/);
  if (m) return new Date(m[3], m[2]-1, m[1]);
  return null;
}

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') { res.status(200).end(); return; }

  const { plate, type = 'rca', country = 'RO' } = req.query;

  if (!plate) {
    return res.status(400).json({
      error: 'Missing plate parameter',
      example: '/api/check-insurance?plate=IF84SOC&type=rca'
    });
  }

  const normalizedPlate = plate.replace(/\s+/g, '').toUpperCase();
  const insuranceType = type.toLowerCase(); // rca or casco

  try {
    let result = null;

    // Method 1: ASF Romania public verification (RCA only - public registry)
    if (insuranceType === 'rca') {
      try {
        // ASF has a public endpoint for RCA verification
        const asfResponse = await makeGetRequest(
          'www.asfromania.ro',
          '/apps/rca/api/check?plate=' + encodeURIComponent(normalizedPlate),
          { 'Referer': 'https://www.asfromania.ro/ro/informatii-consumatori/rca' }
        );

        if (asfResponse.status === 200 && asfResponse.body) {
          const data = asfResponse.body;
          const expiryDate = parseRoDate(data.expiryDate || data.data_sfarsit || data.validTo);
          const startDate = parseRoDate(data.startDate || data.data_inceput || data.validFrom);
          const now = new Date();
          const daysLeft = expiryDate ? Math.ceil((expiryDate - now) / 86400000) : null;

          result = {
            source: 'asf_romania',
            type: 'rca',
            plate: normalizedPlate,
            valid: daysLeft !== null && daysLeft > 0,
            insurer: data.insurer || data.asigurator || data.companie || null,
            policy_number: data.policyNumber || data.numar_polita || null,
            start_date: data.startDate || data.data_inceput || null,
            expiry_date: data.expiryDate || data.data_sfarsit || null,
            days_remaining: daysLeft !== null ? Math.max(0, daysLeft) : null,
            status: daysLeft === null ? 'unknown' : daysLeft <= 0 ? 'expired' : daysLeft <= 30 ? 'warning' : 'ok',
            verified_at: new Date().toISOString()
          };
        }
      } catch (asfErr) {
        console.log('ASF API unavailable:', asfErr.message);
      }
    }

    // CASCO - no public registry, return guidance
    if (insuranceType === 'casco' && !result) {
      result = {
        source: 'not_available',
        type: 'casco',
        plate: normalizedPlate,
        valid: null,
        status: 'manual_only',
        message: 'CASCO nu are registru public. Verificati direct cu asiguratorul (AIDA, Allianz, Omniasig etc.).',
        aida_check_url: 'https://www.aida-asigurari.ro/portaluri-clients'
      };
    }

    if (!result) {
      result = {
        source: 'api_unavailable',
        type: insuranceType,
        plate: normalizedPlate,
        valid: null,
        status: 'api_unavailable',
        message: 'Registrul ASF nu este accesibil momentan. Configurati manual in HA.',
        manual_config_help: 'Folositi senzorul manual din Vehicle Manager HA pentru a introduce datele politei.'
      };
    }

    return res.status(200).json(result);

  } catch (err) {
    console.error('check-insurance error:', err);
    return res.status(500).json({
      error: 'Internal error',
      message: err.message,
      plate: normalizedPlate,
      type: insuranceType
    });
  }
};
