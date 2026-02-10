import { Outlet, NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Workflow,
  CheckCircle,
  Database,
  BarChart3,
  Settings,
  Activity,
  Bell
} from 'lucide-react';
import { useHealthStatus } from '../hooks/useHealthStatus';
import { useWebSocket } from '../hooks/useWebSocket';
import { cn } from '../utils/cn';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Workflows', href: '/workflows', icon: Workflow },
  { name: 'Approvals', href: '/approvals', icon: CheckCircle },
  { name: 'Memory', href: '/memory', icon: Database },
  { name: 'Metrics', href: '/metrics', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Layout() {
  const { data: health } = useHealthStatus();
  const { isConnected, notifications } = useWebSocket();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 w-64 bg-white border-r border-gray-200">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-2 px-6 py-4 border-b border-gray-200">
            <Activity className="w-8 h-8 text-indigo-600" />
            <span className="text-xl font-bold text-gray-900">EpiLoop</span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-4 space-y-1">
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-indigo-50 text-indigo-600'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  )
                }
              >
                <item.icon className="w-5 h-5" />
                {item.name}
              </NavLink>
            ))}
          </nav>

          {/* Status */}
          <div className="px-4 py-4 border-t border-gray-200">
            <div className="flex items-center gap-2 text-sm">
              <span
                className={cn(
                  'w-2 h-2 rounded-full',
                  health?.status === 'healthy' ? 'bg-green-500' : 'bg-yellow-500'
                )}
              />
              <span className="text-gray-600">
                {health?.status === 'healthy' ? 'All systems operational' : 'Degraded'}
              </span>
            </div>
            <div className="flex items-center gap-2 mt-2 text-sm text-gray-500">
              <span
                className={cn(
                  'w-2 h-2 rounded-full',
                  isConnected ? 'bg-green-500' : 'bg-red-500'
                )}
              />
              <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="pl-64">
        {/* Header */}
        <header className="sticky top-0 z-10 flex items-center justify-between px-8 py-4 bg-white border-b border-gray-200">
          <h1 className="text-2xl font-semibold text-gray-900">
            {/* Page title will be set by each page */}
          </h1>
          <div className="flex items-center gap-4">
            <button className="relative p-2 text-gray-400 hover:text-gray-600">
              <Bell className="w-5 h-5" />
              {notifications.length > 0 && (
                <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full" />
              )}
            </button>
            <div className="text-sm text-gray-600">
              v{health?.version || '0.0.0'}
            </div>
          </div>
        </header>

        {/* Page content */}
        <div className="p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
