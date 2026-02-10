import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Play,
  Clock,
  CheckCircle,
  XCircle,
  ChevronRight,
  Plus,
  Search,
  Filter
} from 'lucide-react';
import { api } from '../utils/api';
import { cn } from '../utils/cn';

interface Workflow {
  name: string;
  description: string;
  status: string;
}

interface WorkflowRun {
  workflow_id: string;
  workflow_name: string;
  status: string;
  created_at: string;
  result?: any;
}

export function Workflows() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);
  const [inputData, setInputData] = useState('');

  const queryClient = useQueryClient();

  const { data: workflows, isLoading } = useQuery({
    queryKey: ['workflows'],
    queryFn: () => api.get('/workflows').then(r => r.data),
  });

  const runWorkflow = useMutation({
    mutationFn: (data: { workflow_name: string; input_data: string }) =>
      api.post('/workflows/run', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      setSelectedWorkflow(null);
      setInputData('');
    },
  });

  const filteredWorkflows = workflows?.workflows?.filter((wf: Workflow) =>
    wf.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    wf.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Workflows</h1>
          <p className="mt-1 text-gray-600">
            Manage and run AI agent workflows
          </p>
        </div>
        <button
          onClick={() => setSelectedWorkflow('custom')}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Workflow
        </button>
      </div>

      {/* Search and Filter */}
      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search workflows..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <button className="flex items-center gap-2 px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50">
          <Filter className="w-4 h-4" />
          Filter
        </button>
      </div>

      {/* Workflow List */}
      <div className="bg-white rounded-xl border border-gray-200">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading...</div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredWorkflows?.map((workflow: Workflow) => (
              <WorkflowRow
                key={workflow.name}
                workflow={workflow}
                onRun={() => setSelectedWorkflow(workflow.name)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Run Workflow Modal */}
      {selectedWorkflow && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-lg bg-white rounded-xl p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Run Workflow: {selectedWorkflow}
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Input Data
                </label>
                <textarea
                  value={inputData}
                  onChange={(e) => setInputData(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Enter input data for the workflow..."
                />
              </div>

              <div className="flex justify-end gap-3">
                <button
                  onClick={() => {
                    setSelectedWorkflow(null);
                    setInputData('');
                  }}
                  className="px-4 py-2 text-gray-600 hover:text-gray-900"
                >
                  Cancel
                </button>
                <button
                  onClick={() =>
                    runWorkflow.mutate({
                      workflow_name: selectedWorkflow,
                      input_data: inputData,
                    })
                  }
                  disabled={runWorkflow.isPending}
                  className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                >
                  <Play className="w-4 h-4" />
                  {runWorkflow.isPending ? 'Running...' : 'Run'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function WorkflowRow({
  workflow,
  onRun,
}: {
  workflow: Workflow;
  onRun: () => void;
}) {
  const statusConfig = {
    active: { icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-50' },
    pending: { icon: Clock, color: 'text-yellow-500', bg: 'bg-yellow-50' },
    error: { icon: XCircle, color: 'text-red-500', bg: 'bg-red-50' },
  };

  const status = statusConfig[workflow.status as keyof typeof statusConfig] || statusConfig.active;
  const StatusIcon = status.icon;

  return (
    <div className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-center gap-4">
        <div className={cn('p-2 rounded-lg', status.bg)}>
          <StatusIcon className={cn('w-5 h-5', status.color)} />
        </div>
        <div>
          <h3 className="font-medium text-gray-900">{workflow.name}</h3>
          <p className="text-sm text-gray-500">{workflow.description}</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={onRun}
          className="flex items-center gap-1 px-3 py-1.5 text-sm bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100"
        >
          <Play className="w-4 h-4" />
          Run
        </button>
        <Link
          to={`/workflows/${workflow.name}`}
          className="p-2 text-gray-400 hover:text-gray-600"
        >
          <ChevronRight className="w-5 h-5" />
        </Link>
      </div>
    </div>
  );
}
