import '@mantine/core/styles.css';

import { MantineProvider } from '@mantine/core';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Route, Routes } from 'react-router-dom';

import { Layout } from '@/components/Layout/Layout';
import { AgentCreate } from '@/pages/AgentCreate/AgentCreate';
import { AgentProfile } from '@/pages/AgentProfile/AgentProfile';
import { Chat } from '@/pages/Chat/Chat';
import { Clans } from '@/pages/Clans/Clans';
import { Dashboard } from '@/pages/Dashboard/Dashboard';
import { Feed } from '@/pages/Feed/Feed';
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

export function App() {
  return (
    <MantineProvider theme={animantisTheme} defaultColorScheme="dark">
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
              <Route path="/feed" element={<Feed />} />
              <Route path="/clans" element={<Clans />} />
              <Route path="/settings" element={<Settings />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </MantineProvider>
  );
}
