import React from 'react';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold mb-4">FinShield AI Dashboard</h1>
      <p className="text-xl">Welcome to the Fraud Detection Engine</p>
      <div className="mt-8 flex gap-4">
        <a href="/ml-models" className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
          View ML Models
        </a>
        <a href="/risk-scoring" className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700">
          Risk Scoring
        </a>
      </div>
    </main>
  );
}
