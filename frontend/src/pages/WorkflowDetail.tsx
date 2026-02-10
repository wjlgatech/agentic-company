import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  Play,
  Clock,
  CheckCircle,
  XCircle,
  Activity
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../utils/api';

export function WorkflowDetail() {
  const { id } = useParams<{ id: string }>();

  const { data: workflow } = useQuery({
    queryKey: ['workflow', id],
    queryFn: () => api.get(`/workflows/${id}`).then(r => r.data),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link
          to="/workflows"
          className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{id}</h1>
          <p className="mt-1 text-gray-600">Workflow details and history</p>
        </div>
      </div>

      {/* Status Card */}
      <div className="p-6 bg-white rounded-xl border border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-green-50 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Status</p>
              <p className="text-lg font-semibold text-gray-900 capitalize">
                {workflow?.status || 'Unknown'}
              </p>
            </div>
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
            <Play className="w-4 h-4" />
            Run Again
          </button>
        </div>
      </div>

      {/* Workflow Info */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-6 bg-white rounded-xl border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Details
          </h3>
          <dl className="space-y-3">
            <div className="flex justify-between">
              <dt className="text-gray-500">Workflow ID</dt>
              <dd className="text-gray-900 font-mono text-sm">{workflow?.workflow_id || id}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Created</dt>
              <dd className="text-gray-900">{workflow?.created_at || 'N/A'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Progress</dt>
              <dd className="text-gray-900">{workflow?.progress || 100}%</dd>
            </div>
          </dl>
        </div>

        <div className="p-6 bg-white rounded-xl border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Execution Timeline
          </h3>
          <div className="space-y-4">
            <TimelineItem
              status="completed"
              title="Input Received"
              time="0ms"
            />
            <TimelineItem
              status="completed"
              title="Guardrails Check"
              time="12ms"
            />
            <TimelineItem
              status="completed"
              title="Processing"
              time="245ms"
            />
            <TimelineItem
              status="completed"
              title="Evaluation"
              time="89ms"
            />
            <TimelineItem
              status="completed"
              title="Output Generated"
              time="15ms"
            />
          </div>
        </div>
      </div>

      {/* Output */}
      <div className="p-6 bg-white rounded-xl border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Output
        </h3>
        <pre className="p-4 bg-gray-50 rounded-lg overflow-auto text-sm text-gray-800 max-h-64">
          {JSON.stringify(workflow?.result || { message: "No output available" }, null, 2)}
        </pre>
      </div>
    </div>
  );
}

function TimelineItem({
  status,
  title,
  time,
}: {
  status: 'completed' | 'pending' | 'error';
  title: string;
  time: string;
}) {
  const statusConfig = {
    completed: { icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-50' },
    pending: { icon: Clock, color: 'text-yellow-500', bg: 'bg-yellow-50' },
    error: { icon: XCircle, color: 'text-red-500', bg: 'bg-red-50' },
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <div className="flex items-center gap-3">
      <div className={`p-1.5 rounded-full ${config.bg}`}>
        <Icon className={`w-4 h-4 ${config.color}`} />
      </div>
      <div className="flex-1">
        <span className="text-sm text-gray-900">{title}</span>
      </div>
      <span className="text-xs text-gray-400">{time}</span>
    </div>
  );
}
