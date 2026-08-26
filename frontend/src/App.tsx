import { Navigate, Route, Routes } from 'react-router-dom'
import { RequireAuth } from './auth/RequireAuth'
import { AppLayout } from './components/layout/AppLayout'
import { FaturamentoPage } from './features/faturamento/FaturamentoPage'
import { CargasPage } from './pages/CargasPage'
import { EstoquePage } from './pages/EstoquePage'
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
