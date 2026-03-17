import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex h-screen flex-col items-center justify-center gap-4">
      <h1 className="text-6xl font-bold text-gray-300">404</h1>
      <p className="text-lg text-gray-500">Page not found</p>
      <Link
        href="/dashboard"
        className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 transition-colors"
      >
        Go to Dashboard
      </Link>
    </div>
  );
}
