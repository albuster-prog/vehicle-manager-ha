/**
 * Vehicle Manager HA — License Verification API
  * Deployed on Vercel at: vehicle-manager-ha.vercel.app/api/verify-license
   *
    * POST /api/verify-license
     * Body: { "license_key": "VM-XXXX-XXXX-XXXX" }
      * Returns: { "valid": true/false, "tier": "pro"/"free", "message": "..." }
       */

// In-memory license store (replace with DB in production)
// Format: "VM-XXXX-XXXX-XXXX" => { tier, email, created_at, active }
const VALID_LICENSES = {
    // Add purchased licenses here manually until DB is implemented
  // "VM-DEMO-TEST-0001": { tier: "pro", email: "test@example.com", active: true },
};

/**
 * Validates license key format: VM-XXXX-XXXX-XXXX
  * where X is alphanumeric (uppercase)
   */
function isValidFormat(key) {
  if (!key || typeof key !== "string") return false;
  return /^VM-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/.test(key.trim().toUpperCase());
}

  export default function handler(req, res) {
      // CORS headers
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");

      // Handle preflight
    if (req.method === "OPTIONS") {
      return res.status(200).end();
    }

        // Only accept POST
      if (req.method !== "POST") {
        return res.status(405).json({
                valid: false,
                tier: "free",
                message: "Method not allowed",
        });
      }

        const { license_key } = req.body || {};

      // Check format first
    if (!isValidFormat(license_key)) {
      return res.status(200).json({
              valid: false,
              tier: "free",
              message: "Invalid license key format. Expected: VM-XXXX-XXXX-XXXX",
      });
    }

      const normalizedKey = license_key.trim().toUpperCase();

      // Check against license store
    const licenseData = VALID_LICENSES[normalizedKey];

    if (!licenseData) {
      return res.status(200).json({
              valid: false,
              tier: "free",
              message: "License key not found",
      });
    }

      if (!licenseData.active) {
        return res.status(200).json({
                valid: false,
                tier: "free",
                message: "License key has been deactivated",
        });
      }

          // Valid license!
        return res.status(200).json({
              valid: true,
              tier: licenseData.tier || "pro",
              message: "License verified successfully",
              // Don't expose email or sensitive data
        });
  }
    
