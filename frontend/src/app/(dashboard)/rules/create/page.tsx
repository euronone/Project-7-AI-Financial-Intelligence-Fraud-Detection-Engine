"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useCreateRule, useRuleTemplates } from "@/hooks/use-rules";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { useToast } from "@/components/ui/toast";
import type { Rule, RuleTemplate } from "@/types/rule";

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

export default function CreateRulePage() {
  const router = useRouter();
  const { toast } = useToast();
  const createMut = useCreateRule();
  const { data: templates } = useRuleTemplates();

  const [form, setForm] = useState({
    name: "",
    description: "",
    category: "amount",
    severity: "medium",
    priority: 100,
    conditions: '{"logic":"and","rules":[{"field":"amount","operator":"gt","value":10000}]}',
    actions: '{"actions":[{"type":"create_alert"}]}',
  });

  const loadTemplate = (tpl: RuleTemplate) => {
    setForm({
      name: tpl.name,
      description: tpl.description,
      category: tpl.category,
      severity: tpl.severity,
      priority: tpl.priority,
      conditions: JSON.stringify(tpl.conditions, null, 2),
      actions: JSON.stringify(tpl.actions, null, 2),
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const parsed = {
        name: form.name,
        description: form.description || null,
        category: form.category as Rule["category"],
        severity: form.severity as Rule["severity"],
        priority: form.priority,
        conditions: JSON.parse(form.conditions),
        actions: JSON.parse(form.actions),
        is_active: true,
      };
      createMut.mutate(parsed, {
        onSuccess: () => {
          toast("Rule created successfully", "success");
          router.push("/rules");
        },
        onError: () => toast("Failed to create rule", "error"),
      });
    } catch {
      toast("Invalid JSON in conditions or actions", "error");
    }
  };

  return (
    <div className="space-y-6">
      <Breadcrumbs />
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Create Rule</h1>
        <Button variant="secondary" onClick={() => router.back()}>Cancel</Button>
      </div>

      {/* Templates */}
      {templates && templates.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Start from Template</CardTitle></CardHeader>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {templates.map((tpl) => (
              <button
                key={tpl.name}
                onClick={() => loadTemplate(tpl)}
                className="rounded-lg border p-3 text-left transition-colors hover:border-primary-300 hover:bg-primary-50"
              >
                <p className="font-medium text-gray-900">{tpl.name}</p>
                <p className="mt-0.5 text-xs text-gray-500">{tpl.description}</p>
                <div className="mt-2 flex gap-1">
                  <Badge variant="outline" size="sm">{tpl.category}</Badge>
                  <Badge
                    variant={tpl.severity === "critical" ? "danger" : tpl.severity === "high" ? "danger" : "warning"}
                    size="sm"
                  >
                    {tpl.severity}
                  </Badge>
                </div>
              </button>
            ))}
          </div>
        </Card>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader><CardTitle>Rule Details</CardTitle></CardHeader>
          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="Rule Name"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              required
            />
            <Input
              label="Description"
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
            />
            <Select
              label="Category"
              options={categoryOptions}
              value={form.category}
              onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
            />
            <Select
              label="Severity"
              options={severityOptions}
              value={form.severity}
              onChange={(e) => setForm((f) => ({ ...f, severity: e.target.value }))}
            />
            <Input
              label="Priority"
              type="number"
              value={form.priority}
              onChange={(e) => setForm((f) => ({ ...f, priority: Number(e.target.value) }))}
              hint="Lower number = higher priority"
            />
          </div>

          <div className="mt-6 space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">Conditions (JSON)</label>
              <textarea
                value={form.conditions}
                onChange={(e) => setForm((f) => ({ ...f, conditions: e.target.value }))}
                rows={6}
                className="w-full rounded-lg border border-gray-300 bg-white px-3.5 py-2 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">Actions (JSON)</label>
              <textarea
                value={form.actions}
                onChange={(e) => setForm((f) => ({ ...f, actions: e.target.value }))}
                rows={4}
                className="w-full rounded-lg border border-gray-300 bg-white px-3.5 py-2 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <div className="mt-6 flex justify-end gap-3">
            <Button variant="secondary" type="button" onClick={() => router.back()}>Cancel</Button>
            <Button type="submit" loading={createMut.isPending}>Create Rule</Button>
          </div>
        </Card>
      </form>
    </div>
  );
}
