import React, { useEffect, useState } from 'react';
import { BookOpen, Users, Activity, Plus, TrendingUp, AlertTriangle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';
import { getTeacherOverview, getStudentOverview } from '../services/analyticsService';
import { setAuthRole } from '../services/api';

export default function Dashboard() {
  const { user } = useAppStore();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        if (user?.role === 'admin') {
          setAuthRole('teacher', 'admin_user');
          const result = await getTeacherOverview();
          setData(result);
        } else {
          setAuthRole('student', 'student_1');
          const result = await getStudentOverview();
          setData(result);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to fetch dashboard data');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [user]);

  if (loading) {
    return <div className="p-8 text-center text-gray-500">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="p-8 text-center text-red-500 bg-red-50 rounded-xl border border-red-100">Error: {error}</div>;
  }

  if (!data) return null;

  if (user?.role === 'admin') {
    const stats = [
      { name: 'Total Assessments', value: data.overview.total_assessments, icon: BookOpen, color: 'text-blue-600', bg: 'bg-blue-100' },
      { name: 'Total Attempts', value: data.overview.total_attempts, icon: Users, color: 'text-green-600', bg: 'bg-green-100' },
      { name: 'Avg. Score', value: `${data.overview.average_score_percentage.toFixed(1)}%`, icon: Activity, color: 'text-purple-600', bg: 'bg-purple-100' },
    ];

    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Welcome back, Admin</h1>
            <p className="mt-1 text-sm text-gray-500">Here's what's happening with your assessments today.</p>
          </div>
          <Link
            to="/assessments/new"
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-xl text-white bg-blue-600 hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <Plus className="-ml-1 mr-2 h-5 w-5" aria-hidden="true" />
            New Assessment
          </Link>
        </div>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {stats.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.name}
                className="relative bg-white pt-5 px-4 pb-12 sm:pt-6 sm:px-6 shadow-sm rounded-2xl border border-gray-100 overflow-hidden"
              >
                <dt>
                  <div className={`absolute rounded-xl p-3 ${item.bg}`}>
                    <Icon className={`h-6 w-6 ${item.color}`} aria-hidden="true" />
                  </div>
                  <p className="ml-16 text-sm font-medium text-gray-500 truncate">{item.name}</p>
                </dt>
                <dd className="ml-16 pb-6 flex items-baseline sm:pb-7">
                  <p className="text-2xl font-bold text-gray-900">{item.value}</p>
                </dd>
              </div>
            );
          })}
        </div>

        {/* Performance by Subject */}
        <div className="bg-white shadow-sm rounded-2xl border border-gray-100 overflow-hidden">
          <div className="px-4 py-5 sm:px-6 border-b border-gray-100">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Performance by Subject</h3>
          </div>
          <div className="p-6">
            {data.performance_by_subject.length === 0 ? (
              <p className="text-gray-500 text-sm">No performance data available.</p>
            ) : (
              <ul className="space-y-4">
                {data.performance_by_subject.map((sub: any) => (
                  <li key={sub.subject} className="border p-4 rounded-xl">
                    <div className="flex justify-between items-center font-semibold mb-2">
                      <span>{sub.subject}</span>
                      <span className="text-blue-600">{sub.overall_percentage.toFixed(1)}%</span>
                    </div>
                    <div className="text-sm text-gray-500 mb-2">Total Students: {sub.total_students}</div>
                    
                    {sub.topic_distribution.length > 0 && (
                      <div className="mt-4">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Topics Overview</h4>
                        <div className="space-y-2">
                          {sub.topic_distribution.map((topic: any) => (
                            <div key={topic.topic} className="flex justify-between text-sm items-center">
                              <span className="truncate w-1/3">{topic.topic}</span>
                              <div className="w-1/3 bg-gray-200 rounded-full h-2">
                                <div className="bg-blue-600 h-2 rounded-full" style={{width: `${topic.average_percentage}%`}}></div>
                              </div>
                              <span className="w-1/4 text-right">
                                {topic.weak_count > 0 ? (
                                  <span className="text-red-500 flex items-center justify-end"><AlertTriangle className="h-4 w-4 mr-1"/> {topic.weak_count} weak</span>
                                ) : (
                                  <span className="text-green-500">{topic.strong_count} strong</span>
                                )}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
        
        {/* Remedial Learning */}
        <div className="bg-white shadow-sm rounded-2xl border border-gray-100 overflow-hidden">
          <div className="px-4 py-5 sm:px-6 border-b border-gray-100">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Remedial Interventions</h3>
          </div>
          <div className="p-6 grid grid-cols-3 gap-4">
             <div className="text-center p-4 border rounded-xl bg-gray-50">
                <div className="text-2xl font-bold text-gray-900">{data.remedial_learning.total_generated}</div>
                <div className="text-sm text-gray-500">Tests Generated</div>
             </div>
             <div className="text-center p-4 border rounded-xl bg-gray-50">
                <div className="text-2xl font-bold text-gray-900">{data.remedial_learning.total_completed}</div>
                <div className="text-sm text-gray-500">Tests Completed</div>
             </div>
             <div className="text-center p-4 border rounded-xl bg-blue-50">
                <div className="text-2xl font-bold text-blue-600">
                  {data.remedial_learning.average_improvement_percentage !== null 
                    ? `+${data.remedial_learning.average_improvement_percentage.toFixed(1)}%` 
                    : 'N/A'}
                </div>
                <div className="text-sm text-gray-500 flex justify-center items-center"><TrendingUp className="h-4 w-4 mr-1"/> Avg Improvement</div>
             </div>
          </div>
        </div>
      </div>
    );
  } else {
    // Student Dashboard
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">My Performance Dashboard</h1>
            <p className="mt-1 text-sm text-gray-500">Overall Score: <span className="font-semibold text-blue-600">{data.overall_percentage.toFixed(1)}%</span></p>
          </div>
        </div>

        <div className="bg-white shadow-sm rounded-2xl border border-gray-100 overflow-hidden">
          <div className="px-4 py-5 sm:px-6 border-b border-gray-100">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Subject Performance</h3>
          </div>
          <div className="p-6">
            {data.subject_performance.length === 0 ? (
              <p className="text-gray-500 text-sm">You haven't taken any exams yet.</p>
            ) : (
              <div className="space-y-6">
                {data.subject_performance.map((sub: any) => (
                  <div key={sub.subject} className="border rounded-xl p-4">
                    <div className="flex justify-between font-bold mb-4">
                      <span>{sub.subject}</span>
                      <span>{sub.overall_percentage.toFixed(1)}%</span>
                    </div>
                    {sub.topic_distribution.map((topic: any) => (
                      <div key={topic.topic} className="flex justify-between text-sm items-center mb-2">
                        <span className="w-1/3 truncate">{topic.topic}</span>
                        <div className="w-1/3 bg-gray-200 rounded-full h-2 mx-4">
                          <div className={`h-2 rounded-full ${topic.weak_count > 0 ? 'bg-red-500' : 'bg-green-500'}`} style={{width: `${topic.average_percentage}%`}}></div>
                        </div>
                        <span className="w-1/4 text-right">
                           {topic.weak_count > 0 ? <span className="text-red-500 font-medium">Needs Review</span> : <span className="text-green-500">On Track</span>}
                        </span>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
        
        {/* Remedial Learning */}
        <div className="bg-white shadow-sm rounded-2xl border border-gray-100 overflow-hidden">
          <div className="px-4 py-5 sm:px-6 border-b border-gray-100">
            <h3 className="text-lg leading-6 font-medium text-gray-900">My Remedial Progress</h3>
          </div>
          <div className="p-6 grid grid-cols-2 gap-4">
             <div className="text-center p-4 border rounded-xl bg-gray-50">
                <div className="text-2xl font-bold text-gray-900">{data.remedial_learning.total_completed} / {data.remedial_learning.total_generated}</div>
                <div className="text-sm text-gray-500">Remedial Tests Completed</div>
             </div>
             <div className="text-center p-4 border rounded-xl bg-blue-50">
                <div className="text-2xl font-bold text-blue-600">
                  {data.remedial_learning.average_improvement_percentage !== null 
                    ? `+${data.remedial_learning.average_improvement_percentage.toFixed(1)}%` 
                    : 'N/A'}
                </div>
                <div className="text-sm text-gray-500 flex justify-center items-center"><TrendingUp className="h-4 w-4 mr-1"/> Avg Improvement</div>
             </div>
          </div>
        </div>

      </div>
    );
  }
}
