export interface SystemSettings {
  app_name: string;
  app_env: string;
  fraud_threshold: number;
  auto_block_threshold: number;
  alert_retention_days: number;
  max_batch_size: number;
  enable_real_time: boolean;
  enable_email_notifications: boolean;
  enable_sms_notifications: boolean;
}

export interface TeamMember {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  is_active: boolean;
  last_login_at: string | null;
}

export interface TeamListResponse {
  members: TeamMember[];
  total: number;
}

export interface WebhookConfig {
  id: string;
  name: string;
  url: string;
  events: string[];
  is_active: boolean;
  last_triggered_at: string | null;
  failure_count: number;
  created_at: string;
}

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  expires_at: string;
  is_active: boolean;
}
