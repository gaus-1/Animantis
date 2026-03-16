import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Route, Routes } from 'react-router-dom';

import { Layout } from '@/components/Layout/Layout';
import { AgentCreate } from '@/pages/AgentCreate/AgentCreate';
import { AgentProfile } from '@/pages/AgentProfile/AgentProfile';
import { Chat } from '@/pages/Chat/Chat';
import { Dashboard } from '@/pages/Dashboard/Dashboard';
import { WorldMap } from '@/pages/WorldMap/WorldMap';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: true,
      staleTime: 30_000,
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/agents" element={<Dashboard />} />
            <Route path="/create" element={<AgentCreate />} />
            <Route path="/agent/:id" element={<AgentProfile />} />
            <Route path="/chat/:id" element={<Chat />} />
            <Route path="/map" element={<WorldMap />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
