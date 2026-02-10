import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  CheckCircle,
  Clock,
  AlertTriangle,
  TrendingUp,
  Database,
  Zap
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import { api } from '../utils/api';
import { StatCard } from '../components/StatCard';
import { RecentActivity } from '../components/RecentActivity';

export function Dashboard() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.get('/health').then(r => r.data),
    refetchInterval: 10000,
  });

  const { data: metrics } = useQuery({
    queryKey: ['metrics'],
    queryFn: () => api.get('/metrics').then(r => r.data),
    refetchInterval: 5000,
  });

  const { data: workflows } = useQuery({
    queryKey: ['workflows'],
    queryFn: () => api.get('/workflows').then(r => r.data),
  });

  const { data: approvals } = useQuery({
    queryKey: ['approvals'],
    queryFn: () => api.get('/approvals').then(r => r.data),
  });

  // Mock chart data - in production, this would come from metrics
  const chartData = Array.from({ length: 24 }, (_, i) => ({
    time: `${i}:00`,
    requests: Math.floor(Math.random() * 100) + 20,
    latency: Math.floor(Math.random() * 50) + 10,
  }));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-gray-600">
          Overview of your AI orchestration system
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Active Workflows"
          value={workflows?.count || 0}
          icon={Activity}
          trend="+12%"
          trendUp
        />
        <StatCard
          title="Pending Approvals"
          value={approvals?.count || 0}
          icon={Clock}
          trend={approvals?.count > 0 ? 'Action needed' : 'All clear'}
          trendUp={approvals?.count === 0}
        />
        <StatCard
          title="Memory Entries"
          value={health?.components?.memory?.entries || 0}
          icon={Database}
          trend="+23 today"
          trendUp
        />
        <StatCard
          title="System Status"
          value={health?.status === 'healthy' ? 'Healthy' : 'Degraded'}
          icon={health?.status === 'healthy' ? CheckCircle : AlertTriangle}
          iconColor={health?.status === 'healthy' ? 'text-green-500' : 'text-yellow-500'}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Requests Chart */}
        <div className="p-6 bg-white rounded-xl border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Requests (24h)
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="time" stroke="#9ca3af" fontSize={12} />
                <YAxis stroke="#9ca3af" fontSize={12} />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="requests"
                  stroke="#6366f1"
                  fill="#eef2ff"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Latency Chart */}
        <div className="p-6 bg-white rounded-xl border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Latency (ms)
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="time" stroke="#9ca3af" fontSize={12} />
                <YAxis stroke="#9ca3af" fontSize={12} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="latency"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Activity & Quick Actions */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Recent Activity */}
        <div className="lg:col-span-2">
          <RecentActivity />
        </div>

        {/* Quick Actions */}
        <div className="p-6 bg-white rounded-xl border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Quick Actions
          </h3>
          <div className="space-y-3">
            <button className="w-full flex items-center gap-3 px-4 py-3 bg-indigo-50 text-indigo-700 rounded-lg hover:bg-indigo-100 transition-colors">
              <Zap className="w-5 h-5" />
              <span>New Workflow</span>
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-3 bg-gray-50 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors">
              <Database className="w-5 h-5" />
              <span>Store Memory</span>
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-3 bg-gray-50 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors">
              <TrendingUp className="w-5 h-5" />
              <span>View Full Metrics</span>
            </button>
          </div>
        </div>
      </div>

      {/* System Components */}
      <div className="p-6 bg-white rounded-xl border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          System Components
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <ComponentStatus
            name="LLM Provider"
            status={health?.components?.llm?.status}
            detail={health?.components?.llm?.provider}
          />
          <ComponentStatus
            name="Memory Backend"
            status={health?.components?.memory?.status}
            detail={health?.components?.memory?.backend}
          />
          <ComponentStatus
            name="Guardrails"
            status={health?.components?.guardrails?.status}
            detail="Content filtering enabled"
          />
          <ComponentStatus
            name="API Server"
            status="ok"
            detail={`Port 8000`}
          />
        </div>
      </div>
    </div>
  );
}

function ComponentStatus({
  name,
  status,
  detail,
}: {
  name: string;
  status?: string;
  detail?: string;
}) {
  const isOk = status === 'ok' || status === 'healthy';

  return (
    <div className="p-4 bg-gray-50 rounded-lg">
      <div className="flex items-center gap-2">
        <span
          className={`w-2 h-2 rounded-full ${
            isOk ? 'bg-green-500' : 'bg-yellow-500'
          }`}
        />
        <span className="font-medium text-gray-900">{name}</span>
      </div>
      <p className="mt-1 text-sm text-gray-500">{detail || status}</p>
    </div>
  );
}
