import React, { useEffect, useState } from 'react';
import { Beaker, Search, AlertCircle, FileText, Target, Activity, Zap } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { getResearchMetrics } from '../services/analyticsService';
import { setAuthRole } from '../services/api';

export default function ResearchMetrics() {
  const { user } = useAppStore();
  const [metrics, setMetrics] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true);
        if (user?.role === 'admin') {
          setAuthRole('teacher', 'admin_user');
          const data = await getResearchMetrics();
          setMetrics(data);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to fetch research metrics');
      } finally {
        setLoading(false);
      }
    };
    fetchMetrics();
  }, [user]);

  if (user?.role !== 'admin') {
    return (
      <div className="p-8 text-center bg-white rounded-2xl shadow-sm border border-gray-100">
        <AlertCircle className="mx-auto h-12 w-12 text-red-500 mb-4" />
        <h2 className="text-xl font-bold text-gray-900">Access Denied</h2>
        <p className="mt-2 text-gray-500">You do not have permission to view research metrics.</p>
      </div>
    );
  }

  if (loading) {
    return <div className="p-8 text-center text-gray-500">Loading research metrics...</div>;
  }

  if (error) {
    return <div className="p-8 text-center text-red-500 bg-red-50 rounded-xl border border-red-100">Error: {error}</div>;
  }

  const renderMetricValue = (metric: any) => {
    if (metric.status === 'insufficient_data') {
      return (
        <div className="flex items-center text-sm text-amber-600 bg-amber-50 p-2 rounded-lg">
          <AlertCircle className="h-4 w-4 mr-2" />
          {metric.limitations || 'Insufficient data'}
        </div>
      );
    }
    
    return (
      <div className="text-2xl font-bold text-gray-900">
        {metric.value !== null ? `${metric.value.toFixed(1)}${metric.unit === '%' ? '%' : ' ' + (metric.unit || '')}` : 'N/A'}
      </div>
    );
  };

  const getMetricIcon = (type: string) => {
    switch (type) {
      case 'uniqueness': return <Search className="h-6 w-6 text-purple-600" />;
      case 'alignment': return <Target className="h-6 w-6 text-blue-600" />;
      case 'consistency': return <Activity className="h-6 w-6 text-green-600" />;
      case 'accuracy': return <Beaker className="h-6 w-6 text-red-600" />;
      case 'intervention': return <AlertCircle className="h-6 w-6 text-orange-600" />;
      case 'improvement': return <Zap className="h-6 w-6 text-yellow-600" />;
      default: return <FileText className="h-6 w-6 text-gray-600" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Research & Evaluation Metrics</h1>
          <p className="mt-1 text-sm text-gray-500">Scientific measurement of system performance based on actual platform data.</p>
        </div>
      </div>

      {metrics.length === 0 ? (
        <div className="bg-white p-12 text-center rounded-2xl shadow-sm border border-gray-100">
          <Beaker className="mx-auto h-12 w-12 text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900">No Research Data Available</h3>
          <p className="text-gray-500 mt-2">Metrics will appear here once assessments are generated and evaluated.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {metrics.map((metric) => (
            <div key={metric.id} className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="p-3 bg-gray-50 rounded-xl">
                    {getMetricIcon(metric.metric_type)}
                  </div>
                  <div>
                    <h3 className="font-bold text-gray-900">{metric.metric_name}</h3>
                    <p className="text-xs text-gray-500 uppercase tracking-wider">{metric.metric_type}</p>
                  </div>
                </div>
              </div>
              
              <div className="mb-6">
                {renderMetricValue(metric)}
              </div>
              
              <div className="pt-4 border-t border-gray-100 space-y-2">
                <div className="text-xs text-gray-500">
                  <span className="font-semibold text-gray-700">Methodology:</span> {metric.calculation_method}
                </div>
                {metric.sample_size > 0 && (
                  <div className="text-xs text-gray-500">
                    <span className="font-semibold text-gray-700">Sample Size:</span> n={metric.sample_size}
                  </div>
                )}
                {metric.assessment_id && (
                  <div className="text-xs text-gray-400">
                    Assessment ID: {metric.assessment_id}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      
      <div className="bg-blue-50 p-6 rounded-2xl border border-blue-100 mt-8">
        <h3 className="font-bold text-blue-900 mb-2 flex items-center">
          <AlertCircle className="h-5 w-5 mr-2" /> Research Methodology Transparency
        </h3>
        <p className="text-sm text-blue-800">
          In adherence to strict academic and project specifications, this dashboard only displays mathematically derived metrics 
          based on actual data generated within the platform. If a specific dataset (e.g., human-reference baseline marks) is unavailable, 
          the corresponding metric will explicitly report "Insufficient data" rather than presenting fabricated statistics.
        </p>
      </div>
    </div>
  );
}
