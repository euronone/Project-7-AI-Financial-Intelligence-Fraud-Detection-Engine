# 🔒 API Key Encryption — Quick Start Guide

**Status**: ✅ **READY TO DEPLOY**  
**Time to Setup**: 5 minutes  
**Security Gain**: 🔒 All API keys now encrypted at rest

---

## 30-Second Overview

Your system now encrypts all API keys (Supabase, PostgreSQL passwords, AWS secrets, etc.) before storing in the database. Encryption/decryption is automatic and transparent.

**What's Protected**:
- ✅ Supabase API keys
- ✅ Database passwords
- ✅ AWS credentials
- ✅ Stripe/Razorpay tokens
- ✅ Twilio API keys
- ✅ All 20+ credential types

**How it Works**:
1. User provides API key via Settings API
2. System encrypts it using Fernet (AES-128)
3. Encrypted blob stored in database
4. When needed, decrypted in memory only
5. Decrypted credentials never logged/exposed

---

## 5-Minute Setup

### Step 1: Generate Encryption Key (1 min)

```bash
# Run this command:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Copy the output, e.g.:
# kXp2s5v8y/B?E(H+MbQeThWmZq3t6w9z$C&F)J@NcRfUjXnYpLsOvPqRsTuVwXyZ
```

### Step 2: Add to Environment (1 min)

Add to your `.env` file:

```env
ENCRYPTION_KEY=kXp2s5v8y/B?E(H+MbQeThWmZq3t6w9z$C&F)J@NcRfUjXnYpLsOvPqRsTuVwXyZ
```

**For production**: Use your secrets manager (AWS Secrets Manager, GCP, Azure Key Vault, etc.)

### Step 3: Deploy Code (1 min)

Files already created and integrated:
- ✅ `app/core/encryption.py` — Encryption module
- ✅ `app/api/v1/settings.py` — Settings API updated (encrypt on save, decrypt on retrieve)
- ✅ `app/services/data_sync_service.py` — Data sync updated (decrypt before connecting)

### Step 4: Test (2 min)

```bash
# Start backend
poetry run uvicorn app.main:app --reload

# Save a test credential
curl -X PUT http://localhost:8000/api/v1/settings/database \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "db_type": "supabase",
    "supabase_url": "https://proj.supabase.co",
    "supabase_anon_key": "test_key_12345"
  }'

# Verify it works (should return presence flags only)
curl -X GET http://localhost:8000/api/v1/settings/database \
  -H "Authorization: Bearer $JWT"

# Response should have: {"has_anon_key": true}
# (actual key is NOT returned)
```

Done! 🎉

---

## What Happens Automatically

### When Saving Credentials (Settings API)

```
User inputs: "supabase_anon_key": "eyJ0eXA..."
    ↓ (automatic encryption)
Database stores: "gAAAAABmXXX...encrypted blob..."
    ↓ (encrypted at rest)
Attacker sees: gAAAAABmXXX... (useless without key)
```

### When Using Credentials (Data Sync)

```
Retrieve from DB: "gAAAAABmXXX..."
    ↓ (automatic decryption)
In memory: "eyJ0eXA..." (plaintext, ephemeral)
    ↓ (use to connect)
Connect to Supabase: ✅ Success
    ↓ (delete from memory)
Memory cleared (never logged)
```

---

## What's Encrypted (20+ Fields)

| Category | Fields |
|----------|--------|
| **Supabase** | supabase_anon_key, supabase_service_key |
| **Database** | db_password, password |
| **AWS** | aws_secret_access_key, aws_access_key_id |
| **API Keys** | api_key, secret_key, access_token, refresh_token |
| **Twilio** | twilio_auth_token, twilio_account_sid |
| **Email** | resend_api_key, sendgrid_api_key, smtp_password |
| **Firebase** | firebase_service_account_json |
| **Payment** | stripe_secret_key, razorpay_secret |
| **Other** | webhook_secret, planetscale_password, mongodb_connection_string |

---

## File Changes

### Created
- `app/core/encryption.py` — Encryption/decryption logic (174 lines)
- `app/core/__init__.py` — Package initialization

### Modified
- `app/api/v1/settings.py` — Lines 1-48 (encrypt on PUT, decrypt on GET)
- `app/services/data_sync_service.py` — Lines 25, 467-475, 545-555 (decrypt before sync)

### No Changes Needed
- `app/services/fraud_detection_service.py` — Only reads notifications config (not secrets)
- `app/services/ml_training_service.py` — Only reads refresh config (not secrets)
- Database schema — No changes (transparent to database)

---

## Security Facts

| Aspect | Detail |
|--------|--------|
| **Algorithm** | Fernet (AES-128 CBC + HMAC-SHA256) |
| **Key Size** | 256-bit (base64 encoded) |
| **At Rest** | Encrypted in database |
| **In Transit** | HTTPS (TLS 1.3) |
| **In Memory** | Plaintext (ephemeral during use) |
| **Logging** | Never logged (module filters passwords) |
| **Backward Compat** | Yes (plaintext data still works) |

---

## Troubleshooting

### Error: "Invalid ENCRYPTION_KEY format"
```
Fix: Generate a new key with:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
Update .env and restart.
```

### Error: "Failed to decrypt — wrong encryption key?"
```
Fix: Make sure ENCRYPTION_KEY env var matches the key used to encrypt the data.
Possible causes:
1. Key was rotated and you're using old key
2. Key was changed when deploying
3. Key doesn't match prod/staging keys

Solution: Use the correct key for your environment.
```

### Warning: "may be plaintext from old data"
```
This is OK! Your data was created before encryption was enabled.
It still works (backward compatible).
Next time you save the credential, it will be encrypted.
```

---

## Next Steps (Optional)

After deployment, you might want to:

1. **[High Priority]** Monitor logs for 24-48 hours
   - Look for decryption errors (there shouldn't be any)
   - Confirm data sync still works

2. **[Medium Priority]** Set up key rotation
   - Schedule for 90 days from now
   - See `ENCRYPTION_SETUP.md` for key rotation process

3. **[Low Priority]** Re-encrypt old plaintext data
   - Automatic on next save (backward compatible)
   - Or manual re-encryption script available

4. **[Optional]** Add to compliance checklist
   - ✅ Encryption at rest: ISO 27001, SOC 2, PCI-DSS
   - ✅ Document: Store ENCRYPTION_KEY securely
   - ✅ Audit: Monitor credential access

---

## Files for More Info

| File | Read For |
|------|----------|
| `ENCRYPTION_SETUP.md` | Detailed setup instructions |
| `ENCRYPTION_IMPLEMENTATION.md` | Technical deep-dive |
| `API_KEY_MANAGEMENT.md` | Original feature documentation |

---

## Quick Test Script

Save as `test_encryption.py` and run:

```python
#!/usr/bin/env python3
"""Quick test of encryption setup."""
import os
from app.core.encryption import encryptor

# Test 1: Basic encryption/decryption
plaintext = "my_secret_api_key_12345"
encrypted = encryptor.encrypt(plaintext)
decrypted = encryptor.decrypt(encrypted)

assert plaintext == decrypted, "Encryption round-trip failed!"
assert plaintext not in encrypted, "Plaintext leaked in ciphertext!"
print("✅ Test 1: Encryption round-trip — PASS")

# Test 2: Config encryption (all sensitive fields)
config = {
    "supabase_url": "https://proj.supabase.co",  # Public
    "supabase_anon_key": "eyJ0eXA...",  # Secret
    "label": "Production",  # Public
}

encrypted_config = encryptor.encrypt_config(config)
assert encrypted_config["supabase_url"] == config["supabase_url"]
assert encrypted_config["supabase_anon_key"] != config["supabase_anon_key"]
assert encrypted_config["label"] == config["label"]

decrypted_config = encryptor.decrypt_config(encrypted_config)
assert decrypted_config == config
print("✅ Test 2: Config encryption — PASS")

# Test 3: Backward compat (plaintext still works)
plaintext_config = {
    "supabase_url": "https://proj.supabase.co",
    "supabase_anon_key": "plaintext_key",  # Not encrypted
}

result = encryptor.decrypt_config(plaintext_config)
assert result["supabase_anon_key"] == "plaintext_key"
print("✅ Test 3: Backward compatibility — PASS")

print("\n🎉 All tests passed! Encryption is working correctly.")
```

Run it:
```bash
cd backend
poetry run python test_encryption.py
```

---

## Summary

| Step | Status | Time |
|------|--------|------|
| Generate key | ✅ Ready | 1 min |
| Add to .env | ✅ Ready | 1 min |
| Deploy code | ✅ Ready | Already done |
| Test | ✅ Ready | 2 min |
| **Total** | **✅ READY** | **5 min** |

**You're all set!** 🎉

API keys are now encrypted at rest. Deployment is immediate once ENCRYPTION_KEY is added to your environment.

---

## Emergency: Lost ENCRYPTION_KEY

If you lose the encryption key and can't recover it:

⚠️ **All encrypted credentials will be inaccessible.**

**Recovery options**:
1. **Best**: Restore from backup with original key
2. **Alternative**: Ask users to re-provide their API keys (system will re-encrypt with new key)
3. **Last resort**: Manual key rotation process (see `ENCRYPTION_SETUP.md`)

**Prevention**: 
- Store key in secrets manager, not just `.env`
- Keep secure backup of encryption key
- Document key location/recovery procedure

---

**Questions?** See the detailed guides: `ENCRYPTION_SETUP.md` or `ENCRYPTION_IMPLEMENTATION.md`

**Deploy Status**: ✅ **READY FOR PRODUCTION**
