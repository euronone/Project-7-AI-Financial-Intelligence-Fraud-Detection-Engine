import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

const data = [
  { name: 'Jan', fraudRate: 0.12, anomalyRate: 0.08 },
  { name: 'Feb', fraudRate: 0.15, anomalyRate: 0.10 },
  { name: 'Mar', fraudRate: 0.11, anomalyRate: 0.09 },
  { name: 'Apr', fraudRate: 0.18, anomalyRate: 0.12 },
  { name: 'May', fraudRate: 0.14, anomalyRate: 0.11 },
  { name: 'Jun', fraudRate: 0.10, anomalyRate: 0.07 },
];

const MLCharts = () => {
  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">Model Performance Over Time</h2>
      <div className="bg-white p-4 rounded-lg shadow-md border border-gray-200" style={{ height: '400px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{
              top: 5,
              right: 30,
              left: 20,
              bottom: 5,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="fraudRate" stroke="#8884d8" activeDot={{ r: 8 }} name="Fraud Rate" />
            <Line type="monotone" dataKey="anomalyRate" stroke="#82ca9d" name="Anomaly Rate" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default MLCharts;
