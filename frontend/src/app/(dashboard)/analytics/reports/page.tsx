"use client";

import { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";

const REPORT_TYPES = [
  { value: "fraud_summary", label: "Fraud Summary" },
  { value: "transaction_analysis", label: "Transaction Analysis" },
  { value: "risk_assessment", label: "Risk Assessment" },
  { value: "compliance", label: "Compliance Report" },
];

interface GeneratedReport {
  id: string;
  type: string;
  date_from: string;
  date_to: string;
  status: "generating" | "completed" | "failed";
  created_at: string;
}

export default function ReportsPage() {
  const [reportType, setReportType] = useState("fraud_summary");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [generating, setGenerating] = useState(false);
  const [reports] = useState<GeneratedReport[]>([]);

  const handleGenerate = async () => {
    if (!dateFrom || !dateTo) return;
    setGenerating(true);
    setTimeout(() => setGenerating(false), 2000);
  };

  const typeLabel = (type: string) =>
    REPORT_TYPES.find((t) => t.value === type)?.label ?? type;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
        <p className="mt-1 text-sm text-gray-500">
          Generate and download custom analytics reports.
        </p>
      </div>

      {/* Report generator */}
      <Card>
        <CardHeader>
          <CardTitle>Generate Report</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Select
              label="Report Type"
              options={REPORT_TYPES}
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
            />
            <Input
              label="Start Date"
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
            <Input
              label="End Date"
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
            <div className="flex items-end">
              <Button
                onClick={handleGenerate}
                loading={generating}
                disabled={!dateFrom || !dateTo}
                className="w-full"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
                Generate Report
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Generated reports list */}
      <Card>
        <CardHeader>
          <CardTitle>Generated Reports</CardTitle>
        </CardHeader>
        <CardContent>
          {reports.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-xs font-medium uppercase tracking-wider text-gray-500">
                    <th className="py-3 pr-4">Report Type</th>
                    <th className="px-4 py-3">Date Range</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Created</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {reports.map((report) => (
                    <tr key={report.id} className="hover:bg-gray-50">
                      <td className="py-3 pr-4 font-medium text-gray-900">
                        {typeLabel(report.type)}
                      </td>
                      <td className="px-4 py-3 text-gray-700">
                        {report.date_from} to {report.date_to}
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          variant={
                            report.status === "completed"
                              ? "success"
                              : report.status === "failed"
                                ? "danger"
                                : "warning"
                          }
                        >
                          {report.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-gray-500">{report.created_at}</td>
                      <td className="px-4 py-3 text-right">
                        {report.status === "completed" && (
                          <Button variant="ghost" size="sm">
                            Download
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState
              title="No reports generated"
              description="Use the form above to generate your first report. Reports will appear here once created."
              icon={
                <svg className="h-12 w-12" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
              }
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
