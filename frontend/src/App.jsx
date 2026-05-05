import { useState } from 'react'
import CertificateForm from './components/CertificateForm'
import Result from './components/Result'

function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleAnalyze = async (formData) => {
    setLoading(true)
    setError(null)
    try {
      const resp = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })
      if (!resp.ok) {
        throw new Error(`Error del servidor: ${resp.status}`)
      }
      const data = await resp.json()
      setResult(data)
    } catch (err) {
      setError('Error al conectar con el servidor: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const [formKey, setFormKey] = useState(0)

  const handleBack = () => {
    setResult(null)
    setError(null)
  }

  const handleNewQuery = () => {
    setResult(null)
    setError(null)
    setFormKey(prev => prev + 1)
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-inner">
          <div className="header-logo">
            <span className="header-icon">⚕</span>
            <div>
              <h1>Sistema CIE-10</h1>
              <p>Determinación de Causa Básica de Defunción</p>
            </div>
          </div>
          <div className="header-badge">Vol. 2 · OMS</div>
        </div>
      </header>

      <main className="app-main">
        {result && (
          <Result result={result} onBack={handleBack} onNew={handleNewQuery} />
        )}
        <div style={{ display: result ? 'none' : 'block' }}>
          <CertificateForm
            key={formKey}
            onAnalyze={handleAnalyze}
            loading={loading}
            error={error}
          />
        </div>
      </main>

      <footer className="app-footer">
        <p>
          Basado en <strong>CIE-10 Volumen 2</strong> – Organización Mundial de la Salud.
          &nbsp;·&nbsp; Uso exclusivo para análisis estadístico de mortalidad.
        </p>
      </footer>
    </div>
  )
}

export default App
