import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Eye
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { api } from '../utils/api';
import { cn } from '../utils/cn';
import { useState } from 'react';

interface ApprovalRequest {
  id: string;
  workflow_id: string;
  step_name: string;
  content: string;
  status: string;
  created_at: string;
  expires_at?: string;
  reason?: string;
}

export function Approvals() {
  const [selectedApproval, setSelectedApproval] = useState<ApprovalRequest | null>(null);
  const [decisionReason, setDecisionReason] = useState('');

  const queryClient = useQueryClient();

  const { data: approvals, isLoading } = useQuery({
    queryKey: ['approvals'],
    queryFn: () => api.get('/approvals').then(r => r.data),
    refetchInterval: 5000,
  });

  const decideApproval = useMutation({
    mutationFn: ({ id, approved, reason }: { id: string; approved: boolean; reason: string }) =>
      api.post(`/approvals/${id}/decide`, {
        approved,
        reason,
        decided_by: 'dashboard-user',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
      setSelectedApproval(null);
      setDecisionReason('');
    },
  });

  const pendingCount = approvals?.pending?.length || 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Approvals</h1>
          <p className="mt-1 text-gray-600">
            Review and approve workflow actions
          </p>
        </div>
        {pendingCount > 0 && (
          <div className="flex items-center gap-2 px-4 py-2 bg-yellow-50 text-yellow-800 rounded-lg">
            <AlertTriangle className="w-5 h-5" />
            <span>{pendingCount} pending approval{pendingCount !== 1 ? 's' : ''}</span>
          </div>
        )}
      </div>

      {/* Approval Queue */}
      <div className="bg-white rounded-xl border border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Pending Approvals</h2>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading...</div>
        ) : pendingCount === 0 ? (
          <div className="p-8 text-center">
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
            <p className="text-gray-600">All caught up! No pending approvals.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {approvals?.pending?.map((approval: ApprovalRequest) => (
              <ApprovalRow
                key={approval.id}
                approval={approval}
                onView={() => setSelectedApproval(approval)}
                onApprove={() =>
                  decideApproval.mutate({
                    id: approval.id,
                    approved: true,
                    reason: 'Quick approved',
                  })
                }
                onReject={() => setSelectedApproval(approval)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Approval Detail Modal */}
      {selectedApproval && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-2xl bg-white rounded-xl">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">
                Review Approval Request
              </h2>
              <p className="mt-1 text-gray-600">
                Workflow: {selectedApproval.workflow_id} • Step: {selectedApproval.step_name}
              </p>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Content</h3>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <pre className="whitespace-pre-wrap text-sm text-gray-800">
                    {selectedApproval.content}
                  </pre>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Decision Reason
                </label>
                <textarea
                  value={decisionReason}
                  onChange={(e) => setDecisionReason(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Add a reason for your decision..."
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 p-6 border-t border-gray-200">
              <button
                onClick={() => {
                  setSelectedApproval(null);
                  setDecisionReason('');
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-900"
              >
                Cancel
              </button>
              <button
                onClick={() =>
                  decideApproval.mutate({
                    id: selectedApproval.id,
                    approved: false,
                    reason: decisionReason || 'Rejected',
                  })
                }
                disabled={decideApproval.isPending}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                <XCircle className="w-4 h-4" />
                Reject
              </button>
              <button
                onClick={() =>
                  decideApproval.mutate({
                    id: selectedApproval.id,
                    approved: true,
                    reason: decisionReason || 'Approved',
                  })
                }
                disabled={decideApproval.isPending}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                <CheckCircle className="w-4 h-4" />
                Approve
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ApprovalRow({
  approval,
  onView,
  onApprove,
  onReject,
}: {
  approval: ApprovalRequest;
  onView: () => void;
  onApprove: () => void;
  onReject: () => void;
}) {
  const isExpiringSoon = approval.expires_at &&
    new Date(approval.expires_at).getTime() - Date.now() < 3600000; // 1 hour

  return (
    <div className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-center gap-4 flex-1">
        <div className="p-2 bg-yellow-50 rounded-lg">
          <Clock className="w-5 h-5 text-yellow-500" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-gray-900 truncate">
            {approval.step_name}
          </h3>
          <p className="text-sm text-gray-500 truncate">
            {approval.content.slice(0, 100)}...
          </p>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs text-gray-400">
              {formatDistanceToNow(new Date(approval.created_at), { addSuffix: true })}
            </span>
            {isExpiringSoon && (
              <span className="text-xs text-red-600 font-medium">
                Expiring soon
              </span>
            )}
          </div>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={onView}
          className="p-2 text-gray-400 hover:text-gray-600"
          title="View details"
        >
          <Eye className="w-5 h-5" />
        </button>
        <button
          onClick={onReject}
          className="p-2 text-red-400 hover:text-red-600"
          title="Reject"
        >
          <XCircle className="w-5 h-5" />
        </button>
        <button
          onClick={onApprove}
          className="p-2 text-green-400 hover:text-green-600"
          title="Approve"
        >
          <CheckCircle className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
