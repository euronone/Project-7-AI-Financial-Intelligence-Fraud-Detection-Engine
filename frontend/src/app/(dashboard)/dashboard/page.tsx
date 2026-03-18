/**
 * Overview dashboard — shows live transaction feed (F1.3) and summary stats.
 *
 * Server component — data fetching deferred to child client components.
 */
import { LiveActivityTicker } from "@/components/dashboard/live-activity-ticker";

export const metadata = {
  title: "Dashboard — FinShield AI",
};

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Overview</h2>
        <p className="text-sm text-gray-500 mt-1">
          Real-time transaction monitoring and fraud detection activity.
        </p>
      </div>

      {/* Live feed — F1.3 */}
      <section>
        <h3 className="text-sm font-medium text-gray-700 mb-3">
          Live Transaction Feed
        </h3>
        <LiveActivityTicker />
      </section>

      {/* Placeholder stat cards — analytics (F7) will populate these */}
      <section className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[
          { label: "Transactions Today", value: "—" },
          { label: "Fraud Rate", value: "—" },
          { label: "Open Alerts", value: "—" },
          { label: "Avg Fraud Score", value: "—" },
        ].map((stat) => (
          <div
            key={stat.label}
            className="bg-white border rounded-lg p-4 flex flex-col gap-1"
          >
            <span className="text-xs text-gray-500">{stat.label}</span>
            <span className="text-2xl font-bold text-gray-900">{stat.value}</span>
          </div>
        ))}
      </section>
    </div>
  );
}
