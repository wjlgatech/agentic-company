import {
  Activity,
  CheckCircle,
  Clock,
  XCircle,
  Database,
  Workflow
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { cn } from '../utils/cn';

interface ActivityItem {
  id: string;
  type: 'workflow' | 'approval' | 'memory' | 'error';
  title: string;
  description: string;
  timestamp: Date;
  status: 'success' | 'pending' | 'error';
}

// Mock data - in production, this would come from an API
const mockActivities: ActivityItem[] = [
  {
    id: '1',
    type: 'workflow',
    title: 'Content Research',
    description: 'Completed analysis of AI trends',
    timestamp: new Date(Date.now() - 5 * 60 * 1000),
    status: 'success',
  },
  {
    id: '2',
    type: 'approval',
    title: 'Publish Request',
    description: 'Awaiting approval for blog post',
    timestamp: new Date(Date.now() - 15 * 60 * 1000),
    status: 'pending',
  },
  {
    id: '3',
    type: 'memory',
    title: 'Memory Stored',
    description: 'New context saved: ML frameworks',
    timestamp: new Date(Date.now() - 30 * 60 * 1000),
    status: 'success',
  },
  {
    id: '4',
    type: 'workflow',
    title: 'Data Processing',
    description: 'Processed 150 records',
    timestamp: new Date(Date.now() - 45 * 60 * 1000),
    status: 'success',
  },
  {
    id: '5',
    type: 'error',
    title: 'Rate Limit',
    description: 'API rate limit exceeded',
    timestamp: new Date(Date.now() - 60 * 60 * 1000),
    status: 'error',
  },
];

const typeConfig = {
  workflow: { icon: Workflow, color: 'text-indigo-500', bg: 'bg-indigo-50' },
  approval: { icon: Clock, color: 'text-yellow-500', bg: 'bg-yellow-50' },
  memory: { icon: Database, color: 'text-green-500', bg: 'bg-green-50' },
  error: { icon: XCircle, color: 'text-red-500', bg: 'bg-red-50' },
};

const statusConfig = {
  success: { icon: CheckCircle, color: 'text-green-500' },
  pending: { icon: Clock, color: 'text-yellow-500' },
  error: { icon: XCircle, color: 'text-red-500' },
};

export function RecentActivity() {
  return (
    <div className="p-6 bg-white rounded-xl border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
        <button className="text-sm text-indigo-600 hover:text-indigo-700">
          View all
        </button>
      </div>
      <div className="space-y-4">
        {mockActivities.map((activity) => (
          <ActivityRow key={activity.id} activity={activity} />
        ))}
      </div>
    </div>
  );
}

function ActivityRow({ activity }: { activity: ActivityItem }) {
  const type = typeConfig[activity.type];
  const status = statusConfig[activity.status];
  const TypeIcon = type.icon;
  const StatusIcon = status.icon;

  return (
    <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
      <div className={cn('p-2 rounded-lg', type.bg)}>
        <TypeIcon className={cn('w-4 h-4', type.color)} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium text-gray-900">{activity.title}</p>
          <StatusIcon className={cn('w-4 h-4', status.color)} />
        </div>
        <p className="text-sm text-gray-500 truncate">{activity.description}</p>
        <p className="text-xs text-gray-400 mt-1">
          {formatDistanceToNow(activity.timestamp, { addSuffix: true })}
        </p>
      </div>
    </div>
  );
}
