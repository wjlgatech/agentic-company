import { useQuery } from '@tanstack/react-query';
import {
  Settings as SettingsIcon,
  Server,
  Shield,
  Database,
  Bell,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { api } from '../utils/api';

export function Settings() {
  const { data: config } = useQuery({
    queryKey: ['config'],
    queryFn: () => api.get('/config').then(r => r.data),
  });

  const { data: validation } = useQuery({
    queryKey: ['config-validate'],
    queryFn: () => api.get('/config/validate').then(r => r.data),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="mt-1 text-gray-600">
          System configuration and preferences
        </p>
      </div>

      {/* Validation Status */}
      <div className={`p-4 rounded-xl border ${validation?.valid ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'}`}>
        <div className="flex items-center gap-3">
          {validation?.valid ? (
            <CheckCircle className="w-5 h-5 text-green-600" />
          ) : (
            <XCircle className="w-5 h-5 text-yellow-600" />
          )}
          <div>
            <p className={`font-medium ${validation?.valid ? 'text-green-800' : 'text-yellow-800'}`}>
              {validation?.valid ? 'Configuration Valid' : 'Configuration Issues'}
            </p>
            {validation?.errors?.length > 0 && (
              <ul className="mt-1 text-sm text-yellow-700">
                {validation.errors.map((error: string, i: number) => (
                  <li key={i}>• {error}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>

      {/* Settings Sections */}
      <div className="space-y-6">
        {/* LLM Settings */}
        <SettingsSection
          title="LLM Provider"
          icon={Server}
          description="Configure your AI language model provider"
        >
          <SettingRow
            label="Provider"
            value={config?.llm?.provider || 'Not configured'}
          />
          <SettingRow
            label="Model"
            value={config?.llm?.model || 'Not configured'}
          />
          <SettingRow
            label="Max Tokens"
            value={config?.llm?.max_tokens?.toString() || '4096'}
          />
          <SettingRow
            label="Temperature"
            value={config?.llm?.temperature?.toString() || '0.7'}
          />
        </SettingsSection>

        {/* Guardrails Settings */}
        <SettingsSection
          title="Guardrails"
          icon={Shield}
          description="Content filtering and safety settings"
        >
          <SettingRow
            label="Enabled"
            value={config?.guardrails?.enabled ? 'Yes' : 'No'}
            isBoolean
            boolValue={config?.guardrails?.enabled}
          />
          <SettingRow
            label="Content Filter"
            value={config?.guardrails?.content_filter_enabled ? 'Yes' : 'No'}
            isBoolean
            boolValue={config?.guardrails?.content_filter_enabled}
          />
          <SettingRow
            label="Rate Limit"
            value={config?.guardrails?.rate_limit_enabled ? 'Yes' : 'No'}
            isBoolean
            boolValue={config?.guardrails?.rate_limit_enabled}
          />
          <SettingRow
            label="Max Requests/Min"
            value={config?.guardrails?.max_requests_per_minute?.toString() || '60'}
          />
        </SettingsSection>

        {/* Memory Settings */}
        <SettingsSection
          title="Memory System"
          icon={Database}
          description="Storage and retrieval configuration"
        >
          <SettingRow
            label="Backend"
            value={config?.memory?.backend || 'local'}
          />
          <SettingRow
            label="Max Entries"
            value={config?.memory?.max_entries?.toString() || '1000'}
          />
        </SettingsSection>

        {/* Server Settings */}
        <SettingsSection
          title="Server"
          icon={SettingsIcon}
          description="API server configuration"
        >
          <SettingRow
            label="Host"
            value={config?.server?.host || '0.0.0.0'}
          />
          <SettingRow
            label="Port"
            value={config?.server?.port?.toString() || '8000'}
          />
          <SettingRow
            label="Workers"
            value={config?.server?.workers?.toString() || '4'}
          />
          <SettingRow
            label="Debug Mode"
            value={config?.server?.debug ? 'Yes' : 'No'}
            isBoolean
            boolValue={config?.server?.debug}
          />
        </SettingsSection>

        {/* Observability Settings */}
        <SettingsSection
          title="Observability"
          icon={Bell}
          description="Logging and monitoring settings"
        >
          <SettingRow
            label="Log Level"
            value={config?.observability?.log_level || 'INFO'}
          />
          <SettingRow
            label="Tracing Enabled"
            value={config?.observability?.tracing_enabled ? 'Yes' : 'No'}
            isBoolean
            boolValue={config?.observability?.tracing_enabled}
          />
          <SettingRow
            label="Metrics Enabled"
            value={config?.observability?.metrics_enabled ? 'Yes' : 'No'}
            isBoolean
            boolValue={config?.observability?.metrics_enabled}
          />
        </SettingsSection>
      </div>

      {/* Raw Config */}
      <div className="p-6 bg-white rounded-xl border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Raw Configuration
        </h3>
        <pre className="p-4 bg-gray-50 rounded-lg overflow-auto text-sm text-gray-800 max-h-64">
          {JSON.stringify(config, null, 2)}
        </pre>
      </div>
    </div>
  );
}

function SettingsSection({
  title,
  icon: Icon,
  description,
  children,
}: {
  title: string;
  icon: React.ElementType;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="p-6 bg-white rounded-xl border border-gray-200">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-gray-100 rounded-lg">
          <Icon className="w-5 h-5 text-gray-600" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          <p className="text-sm text-gray-500">{description}</p>
        </div>
      </div>
      <div className="space-y-3">
        {children}
      </div>
    </div>
  );
}

function SettingRow({
  label,
  value,
  isBoolean = false,
  boolValue = false,
}: {
  label: string;
  value: string;
  isBoolean?: boolean;
  boolValue?: boolean;
}) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
      <span className="text-sm text-gray-600">{label}</span>
      {isBoolean ? (
        <span className={`text-sm font-medium ${boolValue ? 'text-green-600' : 'text-gray-400'}`}>
          {value}
        </span>
      ) : (
        <span className="text-sm font-medium text-gray-900">{value}</span>
      )}
    </div>
  );
}
