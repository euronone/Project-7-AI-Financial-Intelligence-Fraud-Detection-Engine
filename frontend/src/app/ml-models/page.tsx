"use client";

import React, { useState, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';

interface Model {
  id: string;
  name: string;
  version: string;
  status: string;
  accuracy: number;
  type: string;
}

const MLModelsDashboard = () => {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/ml/models')
      .then(res => res.json())
      .then(data => {
        setModels(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch models', err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">ML Models Registry</h1>
        <button 
          onClick={() => {
            setLoading(true);
            fetch('http://localhost:8000/api/v1/ml/models')
              .then(res => res.json())
              .then(data => {
                setModels(data);
                setLoading(false);
              })
              .catch(err => {
                console.error('Failed to fetch models', err);
                setLoading(false);
              });
          }}
          className="flex items-center text-sm bg-gray-100 hover:bg-gray-200 text-gray-800 px-3 py-1.5 rounded-md transition-colors"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>
      
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {models.map(model => (
            <div key={model.id} className="bg-white rounded-lg shadow-md p-6 border border-gray-200 hover:shadow-lg transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-lg font-semibold text-gray-800 leading-tight">{model.name}</h2>
                <span className={`px-2 py-1 text-xs font-semibold rounded-full ${model.status === 'Active' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                  {model.status}
                </span>
              </div>
              <div className="space-y-2 mb-4">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Type</span>
                  <span className="text-sm font-medium text-gray-700">{model.type || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Version</span>
                  <span className="text-sm font-medium text-gray-700">{model.version}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Accuracy</span>
                  <span className="text-sm font-medium text-gray-700">{(model.accuracy * 100).toFixed(1)}%</span>
                </div>
              </div>
              
              <div className="w-full bg-gray-200 rounded-full h-1.5 mb-4">
                <div 
                  className={`h-1.5 rounded-full ${model.accuracy > 0.9 ? 'bg-green-500' : model.accuracy > 0.8 ? 'bg-yellow-500' : 'bg-red-500'}`} 
                  style={{ width: `${model.accuracy * 100}%` }}
                ></div>
              </div>
              
              <div className="mt-4 pt-4 border-t border-gray-100 flex justify-between items-center">
                <button className="text-blue-600 hover:text-blue-800 text-sm font-medium transition-colors">View Details</button>
                <button className="text-gray-500 hover:text-gray-800 text-sm font-medium transition-colors">Configure</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MLModelsDashboard;
