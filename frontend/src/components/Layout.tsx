import { Outlet, Link, useLocation } from 'react-router-dom';
import { BookOpen, Home, List, Settings, User, Beaker } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';

export default function Layout() {
  const location = useLocation();
  const { user } = useAppStore();

  const navItems = [
    { name: 'Dashboard', path: '/', icon: Home },
    { name: 'Assessments', path: '/assessments', icon: BookOpen },
    { name: 'Questions', path: '/questions', icon: List },
    ...(user?.role === 'admin' ? [{ name: 'Research Metrics', path: '/research', icon: Beaker }] : []),
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <div className="flex h-screen bg-gray-50 font-sans text-gray-900">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-gray-200">
          <BookOpen className="w-8 h-8 text-blue-600 mr-3" />
          <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
            IntelliAssess
          </span>
        </div>
        <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.name}
                to={item.path}
                className={`flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
                  isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }`}
              >
                <Icon className={`w-5 h-5 mr-3 ${isActive ? 'text-blue-600' : 'text-gray-400'}`} />
                {item.name}
              </Link>
            );
          })}
        </nav>
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center px-4 py-3 text-sm font-medium rounded-xl text-gray-700 hover:bg-gray-100 cursor-pointer transition-colors">
            <User className="w-5 h-5 mr-3 text-gray-400" />
            Profile
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-8">
          <h2 className="text-xl font-semibold text-gray-800">
            {navItems.find((i) => i.path === location.pathname)?.name || 'IntelliAssess'}
          </h2>
          <div className="flex items-center space-x-4">
            <div className="w-8 h-8 bg-gradient-to-tr from-blue-500 to-indigo-500 rounded-full flex items-center justify-center text-white font-bold shadow-md">
              A
            </div>
          </div>
        </header>
        <div className="flex-1 overflow-y-auto p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
