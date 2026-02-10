import { useQuery } from '@tanstack/react-query';
import {
  BarChart3,
  TrendingUp,
  Clock,
  Zap,
  RefreshCw
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { api } from '../utils/api';

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

export function Metrics() {
  const { data: metrics, refetch } = useQuery({
    queryKey: ['metrics'],
    queryFn: () => api.get('/metrics').then(r => r.data),
    refetchInterval: 10000,
  });

  // Transform counters for chart
  const counterData = Object.entries(metrics?.counters || {}).map(([name, value]) => ({
    name: name.replace(/_/g, ' ').replace(/\{.*\}/g, ''),
    value: value as number,
  }));

  // Transform histograms for display
  const histogramData = Object.entries(metrics?.histograms || {}).map(([name, stats]: [string, any]) => ({
    name,
    ...stats,
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Metrics</h1>
          <p className="mt-1 text-gray-600">
            System performance and usage statistics
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Requests"
          value={metrics?.counters?.['api_workflow_run_total'] || 0}
          icon={Zap}
          color="indigo"
        />
        <MetricCard
          title="Memory Operations"
          value={
            (metrics?.counters?.['api_memory_store_total'] || 0) +
            (metrics?.counters?.['api_memory_search_total'] || 0)
          }
          icon={BarChart3}
          color="green"
        />
        <MetricCard
          title="Avg Latency"
          value={`${histogramData[0]?.avg?.toFixed(1) || 0}ms`}
          icon={Clock}
          color="yellow"
        />
        <MetricCard
          title="Error Rate"
          value={`${((metrics?.counters?.['errors_total'] || 0) / Math.max(metrics?.counters?.['requests_total'] || 1, 1) * 100).toFixed(2)}%`}
          icon={TrendingUp}
          color="red"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Counters Bar Chart */}
        <div className="p-6 bg-white rounded-xl border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Operation Counts
          </h3>
          {counterData.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={counterData.slice(0, 10)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" stroke="#9ca3af" fontSize={10} angle={-45} textAnchor="end" height={80} />
                  <YAxis stroke="#9ca3af" fontSize={12} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No counter data yet
            </div>
          )}
        </div>

        {/* Distribution Pie Chart */}
        <div className="p-6 bg-white rounded-xl border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Request Distribution
          </h3>
          {counterData.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={counterData.slice(0, 5)}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    dataKey="value"
                    nameKey="name"
                    label={({ name, percent }) => `${name.slice(0, 15)}... ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {counterData.slice(0, 5).map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No distribution data yet
            </div>
          )}
        </div>
      </div>

      {/* Histogram Details */}
      <div className="p-6 bg-white rounded-xl border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Latency Statistics
        </h3>
        {histogramData.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Metric</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Count</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Avg</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Min</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Max</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">P50</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">P95</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">P99</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {histogramData.map((hist) => (
                  <tr key={hist.name} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {hist.name.replace(/_/g, ' ')}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 text-right">{hist.count}</td>
                    <td className="px-4 py-3 text-sm text-gray-600 text-right">{hist.avg?.toFixed(2)}ms</td>
                    <td className="px-4 py-3 text-sm text-gray-600 text-right">{hist.min?.toFixed(2)}ms</td>
                    <td className="px-4 py-3 text-sm text-gray-600 text-right">{hist.max?.toFixed(2)}ms</td>
                    <td className="px-4 py-3 text-sm text-gray-600 text-right">{hist.p50?.toFixed(2)}ms</td>
                    <td className="px-4 py-3 text-sm text-gray-600 text-right">{hist.p95?.toFixed(2)}ms</td>
                    <td className="px-4 py-3 text-sm text-gray-600 text-right">{hist.p99?.toFixed(2)}ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-8 text-center text-gray-500">
            No histogram data yet
          </div>
        )}
      </div>

      {/* Raw Metrics */}
      <div className="p-6 bg-white rounded-xl border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Raw Metrics (JSON)
        </h3>
        <pre className="p-4 bg-gray-50 rounded-lg overflow-auto text-sm text-gray-800 max-h-64">
          {JSON.stringify(metrics, null, 2)}
        </pre>
      </div>
    </div>
  );
}

function MetricCard({
  title,
  value,
  icon: Icon,
  color,
}: {
  title: string;
  value: string | number;
  icon: React.ElementType;
  color: 'indigo' | 'green' | 'yellow' | 'red';
}) {
  const colorClasses = {
    indigo: 'bg-indigo-50 text-indigo-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    red: 'bg-red-50 text-red-600',
  };

  return (
    <div className="p-6 bg-white rounded-xl border border-gray-200">
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );
}
