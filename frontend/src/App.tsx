import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Exam from './pages/Exam';
import ResearchMetrics from './pages/ResearchMetrics';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="assessments" element={<div className="p-4 bg-white shadow rounded-2xl border border-gray-100">Assessments Page</div>} />
          <Route path="questions" element={<div className="p-4 bg-white shadow rounded-2xl border border-gray-100">Questions Page</div>} />
          <Route path="research" element={<ResearchMetrics />} />
          <Route path="settings" element={<div className="p-4 bg-white shadow rounded-2xl border border-gray-100">Settings Page</div>} />
        </Route>
        <Route path="/exam/:assessmentId" element={<Exam />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
