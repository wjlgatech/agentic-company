import { useQuery } from '@tanstack/react-query';
import { api } from '../utils/api';

interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
  components: {
    llm: { status: string; provider: string };
    memory: { status: string; backend: string; entries: number };
    guardrails: { status: string };
    config_errors: string[];
  };
}

export function useHealthStatus() {
  return useQuery<HealthResponse>({
    queryKey: ['health'],
    queryFn: () => api.get('/health').then(r => r.data),
    refetchInterval: 30000, // Refresh every 30 seconds
    staleTime: 10000,
  });
}
