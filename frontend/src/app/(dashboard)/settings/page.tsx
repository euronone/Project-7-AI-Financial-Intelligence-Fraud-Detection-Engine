"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Modal, ModalHeader, ModalTitle, ModalFooter } from "@/components/ui/modal";
import { cn } from "@/lib/utils";
import { formatDate, formatRelativeTime } from "@/lib/formatters";
import { truncate } from "@/lib/utils";
import {
  useSystemSettings,
  useUpdateSettings,
  useTeamMembers,
  useWebhooks,
  useCreateWebhook,
  useDeleteWebhook,
  useApiKeys,
  useCreateApiKey,
} from "@/hooks/use-settings";
import type { SystemSettings } from "@/types/settings";

const WEBHOOK_EVENTS = [
  "transaction.created",
  "transaction.flagged",
  "alert.created",
  "alert.resolved",
  "case.created",
  "case.closed",
  "model.promoted",
  "rule.triggered",
];

const ROLE_BADGE_VARIANT: Record<string, { variant: "primary" | "default" | "warning" | "success"; className?: string }> = {
  admin: { variant: "primary", className: "bg-purple-100 text-purple-800" },
  analyst: { variant: "primary" },
  investigator: { variant: "warning" },
  viewer: { variant: "default" },
};

// ---------------------------------------------------------------------------
// General Tab
// ---------------------------------------------------------------------------

function GeneralTab() {
  const { data: settings, isLoading } = useSystemSettings();
  const updateSettings = useUpdateSettings();
  const [form, setForm] = useState<Partial<SystemSettings>>({});
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    if (settings) {
      setForm(settings);
      setDirty(false);
    }
  }, [settings]);

  function patch(field: keyof SystemSettings, value: string | number | boolean) {
    setForm((prev) => ({ ...prev, [field]: value }));
    setDirty(true);
  }

  function handleSave() {
    updateSettings.mutate(form);
    setDirty(false);
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i}>
            <Skeleton className="mb-3 h-4 w-1/4" />
            <Skeleton className="h-10 w-full" />
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-6">
      <Card>
        <h3 className="mb-4 text-base font-semibold text-gray-900">Application</h3>
        <div className="space-y-4">
          <Input
            label="Application Name"
            value={form.app_name ?? ""}
            onChange={(e) => patch("app_name", e.target.value)}
          />
          <Input
            label="Environment"
            value={form.app_env ?? ""}
            disabled
            hint="Controlled by deployment configuration"
          />
        </div>
      </Card>

      <Card>
        <h3 className="mb-4 text-base font-semibold text-gray-900">Fraud Detection Thresholds</h3>
        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label="Fraud Threshold"
            type="number"
            step="0.01"
            min="0"
            max="1"
            value={form.fraud_threshold ?? ""}
            onChange={(e) => patch("fraud_threshold", parseFloat(e.target.value))}
            hint="Score above this triggers a fraud alert (0–1)"
          />
          <Input
            label="Auto-Block Threshold"
            type="number"
            step="0.01"
            min="0"
            max="1"
            value={form.auto_block_threshold ?? ""}
            onChange={(e) => patch("auto_block_threshold", parseFloat(e.target.value))}
            hint="Transactions above this are automatically blocked"
          />
          <Input
            label="Alert Retention (days)"
            type="number"
            min="1"
            value={form.alert_retention_days ?? ""}
            onChange={(e) => patch("alert_retention_days", parseInt(e.target.value, 10))}
          />
          <Input
            label="Max Batch Size"
            type="number"
            min="1"
            value={form.max_batch_size ?? ""}
            onChange={(e) => patch("max_batch_size", parseInt(e.target.value, 10))}
          />
        </div>
      </Card>

      <Card>
        <h3 className="mb-4 text-base font-semibold text-gray-900">Real-Time Processing</h3>
        <Switch
          checked={form.enable_real_time ?? false}
          onChange={(v) => patch("enable_real_time", v)}
          label="Enable real-time transaction processing"
        />
      </Card>

      <div className="flex justify-end">
        <Button
          onClick={handleSave}
          disabled={!dirty}
          loading={updateSettings.isPending}
        >
          Save Changes
        </Button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Team Tab
// ---------------------------------------------------------------------------

function TeamTab() {
  const { data, isLoading } = useTeamMembers();

  if (isLoading) {
    return (
      <Card>
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      </Card>
    );
  }

  const members = data?.members ?? [];

  if (members.length === 0) {
    return (
      <Card>
        <div className="py-12 text-center text-sm text-gray-500">
          No team members found.
        </div>
      </Card>
    );
  }

  return (
    <Card padding={false}>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              <th className="px-6 py-3">Name</th>
              <th className="px-6 py-3">Email</th>
              <th className="px-6 py-3">Role</th>
              <th className="px-6 py-3">Status</th>
              <th className="px-6 py-3">Last Login</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {members.map((m) => {
              const roleCfg = ROLE_BADGE_VARIANT[m.role] ?? ROLE_BADGE_VARIANT.viewer;
              return (
                <tr key={m.id} className="hover:bg-gray-50">
                  <td className="whitespace-nowrap px-6 py-4 font-medium text-gray-900">
                    {m.first_name} {m.last_name}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-gray-600">{m.email}</td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <Badge variant={roleCfg.variant} className={roleCfg.className}>
                      {m.role}
                    </Badge>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <span className={cn("inline-flex items-center gap-1.5 text-xs font-medium", m.is_active ? "text-success-600" : "text-gray-400")}>
                      <span className={cn("h-2 w-2 rounded-full", m.is_active ? "bg-success-500" : "bg-gray-300")} />
                      {m.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-gray-500">
                    {m.last_login_at ? formatRelativeTime(m.last_login_at) : "Never"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Integrations (Webhooks) Tab
// ---------------------------------------------------------------------------

function IntegrationsTab() {
  const { data: webhooks, isLoading } = useWebhooks();
  const createWebhook = useCreateWebhook();
  const deleteWebhook = useDeleteWebhook();

  const [modalOpen, setModalOpen] = useState(false);
  const [newHook, setNewHook] = useState({ name: "", url: "", secret: "", events: [] as string[] });

  function toggleEvent(event: string) {
    setNewHook((prev) => ({
      ...prev,
      events: prev.events.includes(event)
        ? prev.events.filter((e) => e !== event)
        : [...prev.events, event],
    }));
  }

  function handleCreate() {
    createWebhook.mutate(newHook, {
      onSuccess: () => {
        setModalOpen(false);
        setNewHook({ name: "", url: "", secret: "", events: [] });
      },
    });
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i}>
            <Skeleton className="mb-2 h-4 w-1/3" />
            <Skeleton className="h-4 w-2/3" />
          </Card>
        ))}
      </div>
    );
  }

  return (
    <>
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-gray-500">
          Configure webhooks to notify external systems when events occur.
        </p>
        <Button size="sm" onClick={() => setModalOpen(true)}>
          Add Webhook
        </Button>
      </div>

      {(!webhooks || webhooks.length === 0) ? (
        <Card>
          <div className="py-12 text-center text-sm text-gray-500">
            No webhooks configured yet. Add one to get started.
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {webhooks.map((wh) => (
            <Card key={wh.id}>
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-semibold text-gray-900">{wh.name}</h4>
                    <span
                      className={cn(
                        "h-2 w-2 rounded-full",
                        wh.is_active ? "bg-success-500" : "bg-gray-300",
                      )}
                    />
                  </div>
                  <p className="mt-1 truncate text-xs text-gray-500" title={wh.url}>
                    {truncate(wh.url, 60)}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {wh.events.map((ev) => (
                      <Badge key={ev} size="sm" variant="outline">
                        {ev}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div className="flex shrink-0 items-center gap-3 text-xs text-gray-500">
                  {wh.failure_count > 0 && (
                    <Badge variant="danger" size="sm">
                      {wh.failure_count} failure{wh.failure_count > 1 ? "s" : ""}
                    </Badge>
                  )}
                  <Button
                    variant="danger"
                    size="sm"
                    loading={deleteWebhook.isPending}
                    onClick={() => deleteWebhook.mutate(wh.id)}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} size="lg">
        <ModalHeader>
          <ModalTitle>Add Webhook</ModalTitle>
        </ModalHeader>

        <div className="space-y-4">
          <Input
            label="Name"
            placeholder="e.g. Slack Alerts"
            value={newHook.name}
            onChange={(e) => setNewHook((p) => ({ ...p, name: e.target.value }))}
          />
          <Input
            label="URL"
            placeholder="https://example.com/webhook"
            value={newHook.url}
            onChange={(e) => setNewHook((p) => ({ ...p, url: e.target.value }))}
          />
          <Input
            label="Secret"
            placeholder="HMAC signing secret"
            type="password"
            value={newHook.secret}
            onChange={(e) => setNewHook((p) => ({ ...p, secret: e.target.value }))}
          />

          <div>
            <span className="mb-2 block text-sm font-medium text-gray-700">Events</span>
            <div className="grid grid-cols-2 gap-2">
              {WEBHOOK_EVENTS.map((ev) => (
                <label key={ev} className="flex items-center gap-2 text-sm text-gray-700">
                  <input
                    type="checkbox"
                    checked={newHook.events.includes(ev)}
                    onChange={() => toggleEvent(ev)}
                    className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  {ev}
                </label>
              ))}
            </div>
          </div>
        </div>

        <ModalFooter>
          <Button variant="secondary" onClick={() => setModalOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleCreate}
            loading={createWebhook.isPending}
            disabled={!newHook.name || !newHook.url || newHook.events.length === 0}
          >
            Create Webhook
          </Button>
        </ModalFooter>
      </Modal>
    </>
  );
}

// ---------------------------------------------------------------------------
// Notifications Tab
// ---------------------------------------------------------------------------

function NotificationsTab() {
  const { data: settings, isLoading } = useSystemSettings();
  const updateSettings = useUpdateSettings();
  const [email, setEmail] = useState(false);
  const [sms, setSms] = useState(false);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    if (settings) {
      setEmail(settings.enable_email_notifications);
      setSms(settings.enable_sms_notifications);
      setDirty(false);
    }
  }, [settings]);

  function handleSave() {
    updateSettings.mutate(
      { enable_email_notifications: email, enable_sms_notifications: sms },
    );
    setDirty(false);
  }

  if (isLoading) {
    return (
      <Card>
        <Skeleton className="mb-4 h-6 w-1/3" />
        <Skeleton className="mb-6 h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </Card>
    );
  }

  return (
    <div className="max-w-2xl space-y-6">
      <Card>
        <h3 className="mb-4 text-base font-semibold text-gray-900">Notification Channels</h3>
        <div className="space-y-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-gray-900">Email Notifications</p>
              <p className="mt-0.5 text-xs text-gray-500">
                Receive email alerts for critical and high-severity fraud events, case updates, and system notifications.
              </p>
            </div>
            <Switch
              checked={email}
              onChange={(v) => { setEmail(v); setDirty(true); }}
            />
          </div>

          <div className="border-t pt-6" />

          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-gray-900">SMS Notifications</p>
              <p className="mt-0.5 text-xs text-gray-500">
                Receive SMS messages for critical-severity alerts that require immediate attention. Standard messaging rates may apply.
              </p>
            </div>
            <Switch
              checked={sms}
              onChange={(v) => { setSms(v); setDirty(true); }}
            />
          </div>
        </div>
      </Card>

      <div className="flex justify-end">
        <Button
          onClick={handleSave}
          disabled={!dirty}
          loading={updateSettings.isPending}
        >
          Save Changes
        </Button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// API Keys Tab
// ---------------------------------------------------------------------------

function ApiKeysTab() {
  const { data: keys, isLoading } = useApiKeys();
  const createKey = useCreateApiKey();

  const [modalOpen, setModalOpen] = useState(false);
  const [newKey, setNewKey] = useState({ name: "", expires_in_days: 90 });
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);

  function handleCreate() {
    createKey.mutate(newKey, {
      onSuccess: (data) => {
        setGeneratedKey(data.full_key ?? null);
        setNewKey({ name: "", expires_in_days: 90 });
        if (!data.full_key) setModalOpen(false);
      },
    });
  }

  function handleCloseModal() {
    setModalOpen(false);
    setGeneratedKey(null);
  }

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i}>
            <Skeleton className="mb-2 h-4 w-1/4" />
            <Skeleton className="h-4 w-1/2" />
          </Card>
        ))}
      </div>
    );
  }

  return (
    <>
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-gray-500">
          Manage API keys for programmatic access to FinShield.
        </p>
        <Button size="sm" onClick={() => setModalOpen(true)}>
          Generate New Key
        </Button>
      </div>

      {(!keys || keys.length === 0) ? (
        <Card>
          <div className="py-12 text-center text-sm text-gray-500">
            No API keys have been created yet.
          </div>
        </Card>
      ) : (
        <Card padding={false}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  <th className="px-6 py-3">Name</th>
                  <th className="px-6 py-3">Key</th>
                  <th className="px-6 py-3">Created</th>
                  <th className="px-6 py-3">Expires</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {keys.map((k) => (
                  <tr key={k.id} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap px-6 py-4 font-medium text-gray-900">
                      {k.name}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 font-mono text-xs text-gray-500">
                      {k.key_prefix}••••••••
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-gray-500">
                      {formatDate(k.created_at)}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-gray-500">
                      {formatDate(k.expires_at)}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <Badge variant={k.is_active ? "success" : "default"} dot>
                        {k.is_active ? "Active" : "Revoked"}
                      </Badge>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-right">
                      {k.is_active && (
                        <Button variant="ghost" size="sm" className="text-danger-600 hover:text-danger-700">
                          Revoke
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      <Modal open={modalOpen} onClose={handleCloseModal} size="md">
        <ModalHeader>
          <ModalTitle>{generatedKey ? "API Key Created" : "Generate API Key"}</ModalTitle>
        </ModalHeader>

        {generatedKey ? (
          <div>
            <p className="mb-3 text-sm text-gray-600">
              Copy this key now — it will not be shown again.
            </p>
            <div className="rounded-lg border bg-gray-50 p-3 font-mono text-sm break-all select-all">
              {generatedKey}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <Input
              label="Key Name"
              placeholder="e.g. Production Integration"
              value={newKey.name}
              onChange={(e) => setNewKey((p) => ({ ...p, name: e.target.value }))}
            />
            <Input
              label="Expires In (days)"
              type="number"
              min="1"
              max="365"
              value={newKey.expires_in_days}
              onChange={(e) => setNewKey((p) => ({ ...p, expires_in_days: parseInt(e.target.value, 10) || 90 }))}
            />
          </div>
        )}

        <ModalFooter>
          {generatedKey ? (
            <Button onClick={handleCloseModal}>Done</Button>
          ) : (
            <>
              <Button variant="secondary" onClick={handleCloseModal}>
                Cancel
              </Button>
              <Button
                onClick={handleCreate}
                loading={createKey.isPending}
                disabled={!newKey.name}
              >
                Generate Key
              </Button>
            </>
          )}
        </ModalFooter>
      </Modal>
    </>
  );
}

// ---------------------------------------------------------------------------
// Settings Page
// ---------------------------------------------------------------------------

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage application configuration, team access, integrations, and API keys.
        </p>
      </div>

      <Tabs defaultValue="general">
        <TabsList>
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="team">Team</TabsTrigger>
          <TabsTrigger value="integrations">Integrations</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="api-keys">API Keys</TabsTrigger>
        </TabsList>

        <TabsContent value="general">
          <GeneralTab />
        </TabsContent>
        <TabsContent value="team">
          <TeamTab />
        </TabsContent>
        <TabsContent value="integrations">
          <IntegrationsTab />
        </TabsContent>
        <TabsContent value="notifications">
          <NotificationsTab />
        </TabsContent>
        <TabsContent value="api-keys">
          <ApiKeysTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
