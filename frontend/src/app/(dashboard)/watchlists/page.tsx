"use client";

import { useState } from "react";
import { useWatchlists, useScreenEntity } from "@/hooks/use-watchlists";
import { DataTable } from "@/components/ui/data-table";
import { Pagination } from "@/components/ui/pagination";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SearchBar } from "@/components/shared/search-bar";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Select } from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import type { WatchlistEntry, WatchlistFilters, ScreeningMatch } from "@/types/watchlist";
import type { ColumnDef } from "@tanstack/react-table";

const columns: ColumnDef<WatchlistEntry, any>[] = [
  {
    accessorKey: "entity_name",
    header: "Entity Name",
    cell: ({ row }) => <span className="font-medium">{row.original.entity_name}</span>,
  },
  {
    accessorKey: "list_name",
    header: "List",
    cell: ({ row }) => <span className="text-sm text-gray-600">{row.original.list_name}</span>,
  },
  {
    accessorKey: "list_type",
    header: "Type",
    cell: ({ row }) => (
      <Badge
        variant={row.original.list_type === "sanctions" ? "danger" : row.original.list_type === "pep" ? "warning" : "default"}
        size="sm"
      >
        {row.original.list_type.replace(/_/g, " ")}
      </Badge>
    ),
  },
  {
    accessorKey: "source",
    header: "Source",
    cell: ({ row }) => <span className="text-sm text-gray-500">{row.original.source}</span>,
  },
  {
    accessorKey: "is_active",
    header: "Active",
    cell: ({ row }) =>
      row.original.is_active ? (
        <Badge variant="success" size="sm" dot>Active</Badge>
      ) : (
        <Badge variant="default" size="sm">Inactive</Badge>
      ),
  },
  {
    accessorKey: "created_at",
    header: "Added",
    cell: ({ row }) => (
      <span className="text-xs text-gray-500">{new Date(row.original.created_at).toLocaleDateString()}</span>
    ),
  },
];

const typeOptions = [
  { value: "", label: "All Types" },
  { value: "sanctions", label: "Sanctions" },
  { value: "pep", label: "PEP" },
  { value: "adverse_media", label: "Adverse Media" },
  { value: "internal_blacklist", label: "Internal Blacklist" },
  { value: "custom", label: "Custom" },
];

const matchColumns: ColumnDef<ScreeningMatch, any>[] = [
  {
    accessorKey: "entity_name",
    header: "Matched Name",
    cell: ({ row }) => <span className="font-medium">{row.original.entity_name}</span>,
  },
  {
    accessorKey: "list_name",
    header: "List",
  },
  {
    accessorKey: "list_type",
    header: "Type",
    cell: ({ row }) => <Badge variant="danger" size="sm">{row.original.list_type.replace(/_/g, " ")}</Badge>,
  },
  {
    accessorKey: "source",
    header: "Source",
  },
  {
    accessorKey: "match_score",
    header: "Match %",
    cell: ({ row }) => (
      <span className="font-semibold text-danger-600">{(row.original.match_score * 100).toFixed(0)}%</span>
    ),
  },
];

export default function WatchlistsPage() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<WatchlistFilters>({});
  const [screenName, setScreenName] = useState("");

  const { data, isLoading } = useWatchlists(page, 25, filters);
  const screenMutation = useScreenEntity();

  const updateFilter = (key: keyof WatchlistFilters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value || undefined }));
    setPage(1);
  };

  const handleScreen = () => {
    if (screenName.trim()) {
      screenMutation.mutate({ entity_name: screenName.trim() });
    }
  };

  return (
    <div className="space-y-6">
      <Breadcrumbs />
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Watchlists</h1>
        <p className="mt-1 text-sm text-gray-500">
          Sanctions, PEP, and internal watchlist screening
        </p>
      </div>

      <Tabs defaultValue="list">
        <TabsList>
          <TabsTrigger value="list">Watchlist Entries</TabsTrigger>
          <TabsTrigger value="screen">Screen Entity</TabsTrigger>
        </TabsList>

        <TabsContent value="list">
          <Card>
            <div className="mb-4 flex flex-wrap items-center gap-3">
              <SearchBar
                placeholder="Search by name..."
                onSearch={(q) => updateFilter("search", q)}
                className="w-64"
              />
              <Select
                options={typeOptions}
                value={filters.list_type || ""}
                onChange={(e) => updateFilter("list_type", e.target.value)}
                className="w-44"
              />
            </div>

            <DataTable
              columns={columns}
              data={data?.items ?? []}
              loading={isLoading}
              emptyMessage="No watchlist entries found"
            />

            {data && data.total_pages > 1 && (
              <div className="mt-4 flex justify-center">
                <Pagination page={page} totalPages={data.total_pages} onPageChange={setPage} />
              </div>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="screen">
          <Card>
            <CardHeader>
              <CardTitle>Screen an Entity</CardTitle>
            </CardHeader>
            <p className="mb-4 text-sm text-gray-500">
              Enter an entity name to check against all active watchlists using fuzzy matching.
            </p>
            <div className="flex gap-3">
              <Input
                placeholder="Entity name to screen..."
                value={screenName}
                onChange={(e) => setScreenName(e.target.value)}
                className="max-w-md"
              />
              <Button onClick={handleScreen} loading={screenMutation.isPending}>
                Screen
              </Button>
            </div>

            {screenMutation.data && (
              <div className="mt-6">
                <div className="mb-3 flex items-center gap-2">
                  <p className="font-medium text-gray-900">
                    Results for &quot;{screenMutation.data.query}&quot;
                  </p>
                  <Badge variant={screenMutation.data.total_matches > 0 ? "danger" : "success"}>
                    {screenMutation.data.total_matches} match{screenMutation.data.total_matches !== 1 && "es"}
                  </Badge>
                </div>
                <DataTable
                  columns={matchColumns}
                  data={screenMutation.data.matches}
                  emptyMessage="No matches found — entity is clear"
                />
              </div>
            )}
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
