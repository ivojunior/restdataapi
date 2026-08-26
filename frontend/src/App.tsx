import { Navigate, Route, Routes } from 'react-router-dom'
import { RequireAuth } from './auth/RequireAuth'
import { AppLayout } from './components/layout/AppLayout'
import { CargasPage } from './pages/CargasPage'
import { EstoquePage } from './pages/EstoquePage'
import { FaturamentoPage } from './pages/FaturamentoPage'
import { FinanceiroPage } from './pages/FinanceiroPage'

function App() {
  return (
    <RequireAuth>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Navigate to="/faturamento" replace />} />
          <Route path="/faturamento" element={<FaturamentoPage />} />
          <Route path="/cargas" element={<CargasPage />} />
          <Route path="/financeiro" element={<FinanceiroPage />} />
          <Route path="/estoque" element={<EstoquePage />} />
          <Route path="*" element={<Navigate to="/faturamento" replace />} />
        </Routes>
      </AppLayout>
    </RequireAuth>
  )
}

export default App
