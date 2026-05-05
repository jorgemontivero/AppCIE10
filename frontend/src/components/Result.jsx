function Result({ result, onBack, onNew }) {
  const {
    selected_code: code,
    code_description: desc,
    step_determined: stepDet,
    steps_log: stepsLog = [],
    justification,
  } = result

  const handlePrint = () => window.print()

  const handleExport = () => {
    const now = new Date().toLocaleString('es-AR')
    const lines = [
      '══════════════════════════════════════════════════════════',
      '  CAUSA BÁSICA DE DEFUNCIÓN  –  CIE-10 Volumen 2',
      '══════════════════════════════════════════════════════════',
      '',
      `  Fecha de análisis : ${now}`,
      `  Código CIE-10     : ${code || 'No determinado'}`,
      `  Descripción       : ${desc || '—'}`,
      `  Paso determinante : ${stepDet || '—'}`,
      '',
      '──────────────────────────────────────────────────────────',
      '  PASOS APLICADOS',
      '──────────────────────────────────────────────────────────',
      ...(stepsLog.map((s) =>
        `  [${s.step.padEnd(4)}] ${s.description}`
      )),
      '',
      '──────────────────────────────────────────────────────────',
      '  NOTA',
      '──────────────────────────────────────────────────────────',
      '  Este resultado es una asistencia automatizada.',
      '  El analista debe verificar el código final.',
      '══════════════════════════════════════════════════════════',
    ]
    const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `causa_basica_${code || 'resultado'}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div>
      <div className="card">
        {/* Hero con resultado */}
        {code ? (
          <div className="result-hero">
            <div>
              <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 1, opacity: .6, marginBottom: 4 }}>
                Causa básica de defunción seleccionada
              </div>
              <div className="result-hero-code">{code}</div>
              <div className="result-hero-desc" style={{ marginTop: 8 }}>
                {desc || <em style={{ opacity: .65 }}>Descripción no disponible en la base de datos</em>}
              </div>
              <div className="result-step-tag" style={{ marginTop: 12 }}>
                ✓ Determinado en paso {stepDet}
              </div>
            </div>
          </div>
        ) : (
          <div className="result-no-code">
            <div style={{ fontSize: 40, marginBottom: 8 }}>⚠</div>
            <p style={{ fontWeight: 600, color: 'var(--gray-700)', marginBottom: 8 }}>
              No se pudo determinar la causa básica
            </p>
            <p style={{ fontSize: 13, color: 'var(--gray-500)' }}>
              {justification || 'Verifique los datos ingresados.'}
            </p>
          </div>
        )}

        {/* Pasos aplicados */}
        {stepsLog.length > 0 && (
          <div className="steps-container">
            <div className="steps-title">Pasos aplicados — CIE-10 Vol. 2</div>
            {stepsLog.map((step, i) => {
              const isKey = step.step === stepDet
              return (
                <div key={i} className={`step-item${isKey ? ' step-item--key' : ''}`}>
                  <div className="step-dot">{step.step}</div>
                  <div className="step-body">
                    <div className="step-label">
                      {step.step}
                      {isKey && ' — Paso determinante'}
                    </div>
                    <div className="step-desc">{step.description}</div>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Nota */}
        <div className="result-note">
          <strong>Nota:</strong> Este resultado es una asistencia automatizada basada en las reglas del
          CIE-10 Volumen 2. El analista debe revisar el certificado original y confirmar
          el código de causa básica antes de registrarlo.
        </div>

        {/* Acciones */}
        <div className="result-actions">
          <button className="btn btn-secondary" onClick={onBack}>
            ← Volver a los datos
          </button>
          <button className="btn btn-secondary" onClick={onNew}>
            Nueva consulta
          </button>
          {code && (
            <>
              <button className="btn btn-secondary" onClick={handlePrint}>
                🖨 Imprimir
              </button>
              <button className="btn btn-primary" onClick={handleExport}>
                ↓ Exportar TXT
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default Result
