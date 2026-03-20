"use client";

import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownItem } from "@/components/ui/dropdown-menu";

interface ExportButtonProps {
  onExport: (format: "csv" | "json" | "pdf") => void;
  loading?: boolean;
}

export function ExportButton({ onExport, loading }: ExportButtonProps) {
  return (
    <DropdownMenu
      trigger={
        <Button variant="secondary" size="sm" loading={loading}>
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
          </svg>
          Export
        </Button>
      }
    >
      <DropdownItem onClick={() => onExport("csv")}>Export as CSV</DropdownItem>
      <DropdownItem onClick={() => onExport("json")}>Export as JSON</DropdownItem>
      <DropdownItem onClick={() => onExport("pdf")}>Export as PDF</DropdownItem>
    </DropdownMenu>
  );
}
