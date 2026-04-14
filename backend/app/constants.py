"""
Centralized constants for FinShield AI — eliminate magic numbers.
Use these instead of hardcoding values throughout the codebase.
"""

# ── Fraud Scoring Thresholds ──────────────────────────────────────────────
FRAUD_SCORE_PASS = 0.30  # Below = legitimate
FRAUD_SCORE_FLAG = 0.60  # Between PASS and FLAG = suspicious
FRAUD_SCORE_ALERT = 0.80  # Between FLAG and ALERT = high risk
# Above ALERT = critical / block

FRAUD_CATEGORY_LEGITIMATE = "legitimate"
FRAUD_CATEGORY_SUSPICIOUS = "suspicious"
FRAUD_CATEGORY_FRAUDULENT = "fraudulent"
FRAUD_CATEGORY_UNSCORED = "unscored"

FRAUD_RISK_LOW = "low"
FRAUD_RISK_MEDIUM = "medium"
FRAUD_RISK_HIGH = "high"
FRAUD_RISK_CRITICAL = "critical"

FRAUD_DECISION_PASS = "PASS"
FRAUD_DECISION_FLAG = "FLAG"
FRAUD_DECISION_ALERT = "ALERT"
FRAUD_DECISION_BLOCK = "BLOCK"

# ── Transaction Limits ────────────────────────────────────────────────────
MAX_TRANSACTION_AMOUNT = 10_000_000  # ₹10M max per transaction
MIN_TRANSACTION_AMOUNT = 1  # ₹1 min per transaction
STRUCTURING_THRESHOLD = 800_000  # ₹8L threshold for structuring detection
STRUCTURING_COUNT = 5  # 5+ transactions within threshold

# ── Time Windows ──────────────────────────────────────────────────────────
VELOCITY_WINDOW_MINUTES_SHORT = 10  # 10-min window for rapid velocity
VELOCITY_WINDOW_MINUTES_LONG = 60  # 1-hour window for daily velocity
VELOCITY_WINDOW_HOURS_DAY = 24  # 24-hour window for daily patterns
VELOCITY_SPIKE_MULTIPLIER = 5  # 5x above baseline = spike

# ── Geographic Limits ─────────────────────────────────────────────────────
IMPOSSIBLE_TRAVEL_KM_PER_HOUR = 900  # >900 km/h is impossible
SUSPICIOUS_TRAVEL_KM_PER_HOUR = 500  # 500-900 km/h is suspicious
IMPOSSIBLE_TRAVEL_MINUTES = 30  # Within 30 minutes

# ── Device & New User ─────────────────────────────────────────────────────
DEVICE_AGE_DAYS_NEW = 0  # First-time device
ACCOUNT_AGE_DAYS_NEW = 30  # Account < 30 days = new

# ── Pagination & Limits ───────────────────────────────────────────────────
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200
MIN_PAGE_SIZE = 1

# ── File Upload Limits ────────────────────────────────────────────────────
MAX_CSV_FILE_SIZE_MB = 50
MAX_CSV_FILE_SIZE_BYTES = MAX_CSV_FILE_SIZE_MB * 1024 * 1024
MAX_CSV_ROWS = 100_000
CSV_CHUNK_SIZE = 1000

# ── Request Timeouts ─────────────────────────────────────────────────────
DEFAULT_REQUEST_TIMEOUT_SECONDS = 30
BATCH_REQUEST_TIMEOUT_SECONDS = 120
ML_SCORING_TIMEOUT_SECONDS = 5

# ── WebSocket Configuration ───────────────────────────────────────────────
WS_MAX_MESSAGES_PER_CONNECTION = 100
WS_HEARTBEAT_INTERVAL_SECONDS = 30
WS_HEARTBEAT_TIMEOUT_SECONDS = 60

# ── OTP Configuration ─────────────────────────────────────────────────────
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5
OTP_MAX_ATTEMPTS = 3

# ── JWT Configuration ────────────────────────────────────────────────────
JWT_ACCESS_TOKEN_TYPE = "access"
JWT_REFRESH_TOKEN_TYPE = "refresh"
JWT_PASSWORD_RESET_TYPE = "password_reset"
RESET_TOKEN_EXPIRY_HOURS = 1

# ── Database Configuration ───────────────────────────────────────────────
DB_POOL_SIZE = 20
DB_POOL_MAX_OVERFLOW = 40
DB_ECHO_SQL = False  # Set to True in development for debugging
DB_POOL_RECYCLE_SECONDS = 3600

# ── Cache Configuration ──────────────────────────────────────────────────
CUSTOMER_HISTORY_CACHE_TTL_SECONDS = 300  # 5 minutes
FEATURE_CACHE_TTL_SECONDS = 600  # 10 minutes

# ── Logging ───────────────────────────────────────────────────────────────
LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "ERROR"
LOG_LEVEL_CRITICAL = "CRITICAL"

# ── HTTP Status Codes ────────────────────────────────────────────────────
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_400_BAD_REQUEST = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_409_CONFLICT = 409
HTTP_422_UNPROCESSABLE_ENTITY = 422
HTTP_500_INTERNAL_SERVER_ERROR = 500
HTTP_503_SERVICE_UNAVAILABLE = 503
