import '@mantine/core/styles.css';

import { MantineProvider } from '@mantine/core';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Route, Routes, Navigate } from 'react-router-dom';

import { ErrorBoundary } from '@/components/ErrorBoundary/ErrorBoundary';
import { Layout } from '@/components/Layout/Layout';
import { AuthProvider, useAuth } from '@/context/AuthContext';
import { AgentCreate } from '@/pages/AgentCreate/AgentCreate';
import { AgentProfile } from '@/pages/AgentProfile/AgentProfile';
import { Chat } from '@/pages/Chat/Chat';
import { Clans } from '@/pages/Clans/Clans';
import { Dashboard } from '@/pages/Dashboard/Dashboard';
import { Feed } from '@/pages/Feed/Feed';
import { Landing } from '@/pages/Landing/Landing';
import { Settings } from '@/pages/Settings/Settings';
import { WorldMap } from '@/pages/WorldMap/WorldMap';
import { animantisTheme } from '@/theme';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: true,
      staleTime: 30_000,
    },
  },
});

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  // If not authenticated, they can't access this route directly
  // We bounce them to the Landing page
  if (!isAuthenticated) {
    return <Navigate to="/welcome" replace />;
  }
  return <>{children}</>;
}

export function App() {
  return (
    <ErrorBoundary>
      <MantineProvider theme={animantisTheme} defaultColorScheme="dark">
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <BrowserRouter>
              <Routes>
                <Route element={<Layout />}>
                  <Route path="/welcome" element={<Landing />} />
                  <Route path="/map" element={<WorldMap />} />
                  <Route path="/feed" element={<Feed />} />
                  <Route path="/clans" element={<Clans />} />

                  {/* Protected Routes */}
                  <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
                  <Route path="/agents" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
                  <Route path="/create" element={<ProtectedRoute><AgentCreate /></ProtectedRoute>} />
                  <Route path="/agent/:id" element={<ProtectedRoute><AgentProfile /></ProtectedRoute>} />
                  <Route path="/chat/:id" element={<ProtectedRoute><Chat /></ProtectedRoute>} />
                  <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />

                  <Route path="*" element={<Navigate to="/" replace />} />
                </Route>
              </Routes>
            </BrowserRouter>
          </AuthProvider>
        </QueryClientProvider>
      </MantineProvider>
    </ErrorBoundary>
  );
}
