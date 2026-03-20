"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useRule, useUpdateRule, useTestRule } from "@/hooks/use-rules";
import type { Rule } from "@/types/rule";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useToast } from "@/components/ui/toast";

const categoryOptions = [
  { value: "velocity", label: "Velocity" },
  { value: "amount", label: "Amount" },
  { value: "geography", label: "Geography" },
  { value: "pattern", label: "Pattern" },
  { value: "device", label: "Device" },
  { value: "custom", label: "Custom" },
];

const severityOptions = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
  { value: "critical", label: "Critical" },
];

export default function RuleDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const ruleId = params.id as string;
  const { data: rule, isLoading } = useRule(ruleId);
  const updateMut = useUpdateRule(ruleId);
  const testMut = useTestRule(ruleId);

  const [editMode, setEditMode] = useState(false);
  const [form, setForm] = useState<Record<string, any>>({});
  const [testTxn, setTestTxn] = useState('{\n  "amount": 15000,\n  "country_code": "US",\n  "channel": "online"\n}');

  const startEdit = () => {
    if (!rule) return;
    setForm({
      name: rule.name,
      description: rule.description || "",
      category: rule.category,
      severity: rule.severity,
      priority: rule.priority,
      conditions: JSON.stringify(rule.conditions, null, 2),
      actions: JSON.stringify(rule.actions, null, 2),
    });
    setEditMode(true);
  };

  const handleSave = () => {
    try {
      updateMut.mutate(
        {
          name: form.name,
          description: form.description || null,
          category: form.category as Rule["category"],
          severity: form.severity as Rule["severity"],
          priority: form.priority,
          conditions: JSON.parse(form.conditions),
          actions: JSON.parse(form.actions),
        },
        {
          onSuccess: () => {
            toast("Rule updated", "success");
            setEditMode(false);
          },
          onError: () => toast("Failed to update rule", "error"),
        },
      );
    } catch {
      toast("Invalid JSON", "error");
    }
  };

  const handleTest = () => {
    try {
      testMut.mutate(JSON.parse(testTxn));
    } catch {
      toast("Invalid JSON in test transaction", "error");
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!rule) return null;

  return (
    <div className="space-y-6">
      <Breadcrumbs />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{rule.name}</h1>
          <p className="mt-1 text-sm text-gray-500">{rule.description || "No description"}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => router.back()}>Back</Button>
          {!editMode && <Button onClick={startEdit}>Edit</Button>}
        </div>
      </div>

      <Tabs defaultValue="details">
        <TabsList>
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="test">Test Rule</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
        </TabsList>

        {/* Details Tab */}
        <TabsContent value="details">
          <Card>
            {editMode ? (
              <div className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <Input label="Name" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
                  <Input label="Description" value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} />
                  <Select label="Category" options={categoryOptions} value={form.category} onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))} />
                  <Select label="Severity" options={severityOptions} value={form.severity} onChange={(e) => setForm((f) => ({ ...f, severity: e.target.value }))} />
                  <Input label="Priority" type="number" value={form.priority} onChange={(e) => setForm((f) => ({ ...f, priority: Number(e.target.value) }))} />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">Conditions (JSON)</label>
                  <textarea value={form.conditions} onChange={(e) => setForm((f) => ({ ...f, conditions: e.target.value }))} rows={8} className="w-full rounded-lg border border-gray-300 bg-white px-3.5 py-2 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">Actions (JSON)</label>
                  <textarea value={form.actions} onChange={(e) => setForm((f) => ({ ...f, actions: e.target.value }))} rows={4} className="w-full rounded-lg border border-gray-300 bg-white px-3.5 py-2 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
                </div>
                <div className="flex justify-end gap-3">
                  <Button variant="secondary" onClick={() => setEditMode(false)}>Cancel</Button>
                  <Button onClick={handleSave} loading={updateMut.isPending}>Save</Button>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  {[
                    { label: "Category", value: <Badge variant="outline">{rule.category}</Badge> },
                    { label: "Severity", value: <Badge variant={rule.severity === "critical" || rule.severity === "high" ? "danger" : "warning"}>{rule.severity}</Badge> },
                    { label: "Priority", value: rule.priority },
                    { label: "Status", value: <Badge variant={rule.is_active ? "success" : "default"} dot>{rule.is_active ? "Active" : "Inactive"}</Badge> },
                  ].map((d) => (
                    <div key={d.label}>
                      <p className="text-xs font-medium uppercase tracking-wider text-gray-400">{d.label}</p>
                      <div className="mt-1 text-sm text-gray-900">{d.value}</div>
                    </div>
                  ))}
                </div>
                <div>
                  <p className="mb-2 text-sm font-medium text-gray-700">Conditions</p>
                  <pre className="rounded-lg bg-gray-50 p-4 font-mono text-xs text-gray-800 overflow-auto">
                    {JSON.stringify(rule.conditions, null, 2)}
                  </pre>
                </div>
                <div>
                  <p className="mb-2 text-sm font-medium text-gray-700">Actions</p>
                  <pre className="rounded-lg bg-gray-50 p-4 font-mono text-xs text-gray-800 overflow-auto">
                    {JSON.stringify(rule.actions, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </Card>
        </TabsContent>

        {/* Test Tab */}
        <TabsContent value="test">
          <Card>
            <CardHeader><CardTitle>Dry-Run Test</CardTitle></CardHeader>
            <p className="mb-4 text-sm text-gray-500">
              Provide sample transaction data to test this rule without side effects.
            </p>
            <textarea
              value={testTxn}
              onChange={(e) => setTestTxn(e.target.value)}
              rows={6}
              className="w-full rounded-lg border border-gray-300 bg-white px-3.5 py-2 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <div className="mt-3">
              <Button onClick={handleTest} loading={testMut.isPending}>Run Test</Button>
            </div>

            {testMut.data && (
              <div className="mt-6 rounded-lg border p-4">
                <div className="mb-3 flex items-center gap-3">
                  <Badge variant={testMut.data.matched ? "danger" : "success"} size="lg">
                    {testMut.data.matched ? "MATCHED" : "NO MATCH"}
                  </Badge>
                  <span className="text-sm text-gray-500">{testMut.data.rule_name}</span>
                </div>

                <p className="mb-2 text-sm font-medium text-gray-700">Condition Results</p>
                <div className="space-y-1">
                  {testMut.data.conditions.map((c, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm">
                      <span className={c.passed ? "text-success-600" : "text-danger-600"}>
                        {c.passed ? "✓" : "✗"}
                      </span>
                      <span className="font-mono text-gray-700">
                        {c.field} {c.operator} {JSON.stringify(c.value)}
                      </span>
                    </div>
                  ))}
                </div>

                {testMut.data.actions.length > 0 && (
                  <>
                    <p className="mb-2 mt-4 text-sm font-medium text-gray-700">Actions (would fire)</p>
                    <div className="space-y-1">
                      {testMut.data.actions.map((a, i) => (
                        <div key={i} className="text-sm">
                          <Badge variant="outline" size="sm">{a.type}</Badge>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </div>
            )}
          </Card>
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance">
          <Card>
            <CardHeader><CardTitle>Performance Stats</CardTitle></CardHeader>
            <div className="grid gap-6 sm:grid-cols-3">
              <div className="text-center">
                <p className="text-3xl font-bold text-gray-900">{rule.hit_count.toLocaleString()}</p>
                <p className="text-sm text-gray-500">Total Hits</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-gray-900">
                  {rule.false_positive_rate !== null ? `${(rule.false_positive_rate * 100).toFixed(1)}%` : "N/A"}
                </p>
                <p className="text-sm text-gray-500">False Positive Rate</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-gray-900">{rule.priority}</p>
                <p className="text-sm text-gray-500">Priority</p>
              </div>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
