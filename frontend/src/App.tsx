import { BrowserRouter, Route, Routes } from 'react-router-dom';

import { Layout } from '@/components/Layout/Layout';
import { AgentCreate } from '@/pages/AgentCreate/AgentCreate';
import { AgentProfile } from '@/pages/AgentProfile/AgentProfile';
import { Chat } from '@/pages/Chat/Chat';
import { Dashboard } from '@/pages/Dashboard/Dashboard';
import { WorldMap } from '@/pages/WorldMap/WorldMap';

export function App() {
  return (
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
  );
}
