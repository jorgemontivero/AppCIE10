import { useState } from 'react'
import CodeSearch from './CodeSearch'

const mkCode = () => ({ code: '', description: '' })
const mkPart1Line = (line) => ({ line, interval: '', codes: [mkCode()] })
const INITIAL_PART1 = ['a', 'b', 'c', 'd'].map((l) => mkPart1Line(l))
const mkPart2Row = () => ({ interval: '', codes: [mkCode()] })
const INITIAL_PART2 = [mkPart2Row(), mkPart2Row()]

function CertificateForm({ onAnalyze, loading, error }) {
  const [part1, setPart1] = useState(INITIAL_PART1)
  const [part2, setPart2] = useState(INITIAL_PART2)
  const [sex, setSex] = useState('M')
  const [age, setAge] = useState('')
  const [ageUnit, setAgeUnit] = useState('años')
  const [pregnancy, setPregnancy] = useState('N')
  const [violence, setViolence] = useState(false)
  const [violenceType, setViolenceType] = useState('')

  const updatePart1Code = (lineIdx, codeIdx, field, val) => {
    setPart1((prev) => {
      const next = [...prev]
      const row = { ...next[lineIdx], codes: [...next[lineIdx].codes] }
      row.codes[codeIdx] = { ...row.codes[codeIdx], [field]: val }
      next[lineIdx] = row
      return next
    })
  }

  const addPart1Code = (lineIdx) => {
    setPart1((prev) => {
      const next = [...prev]
      next[lineIdx] = { ...next[lineIdx], codes: [...next[lineIdx].codes, mkCode()] }
      return next
    })
  }

  const removePart1Code = (lineIdx, codeIdx) => {
    setPart1((prev) => {
      const next = [...prev]
      const codes = next[lineIdx].codes.filter((_, j) => j !== codeIdx)
      next[lineIdx] = { ...next[lineIdx], codes: codes.length ? codes : [mkCode()] }
      return next
    })
  }

  const updatePart2Code = (rowIdx, codeIdx, field, val) => {
    setPart2((prev) => {
      const next = [...prev]
      const row = { ...next[rowIdx], codes: [...next[rowIdx].codes] }
      row.codes[codeIdx] = { ...row.codes[codeIdx], [field]: val }
      next[rowIdx] = row
      return next
    })
  }

  const addPart2Code = (rowIdx) => {
    setPart2((prev) => {
      const next = [...prev]
      next[rowIdx] = { ...next[rowIdx], codes: [...next[rowIdx].codes, mkCode()] }
      return next
    })
  }

  const removePart2Code = (rowIdx, codeIdx) => {
    setPart2((prev) => {
      const next = [...prev]
      const codes = next[rowIdx].codes.filter((_, j) => j !== codeIdx)
      next[rowIdx] = { ...next[rowIdx], codes: codes.length ? codes : [mkCode()] }
      return next
    })
  }

  const handleReset = () => {
    setPart1(['a', 'b', 'c', 'd'].map((l) => mkPart1Line(l)))
    setPart2([mkPart2Row(), mkPart2Row()])
    setSex('M')
    setAge('')
    setAgeUnit('años')
    setPregnancy('N')
    setViolence(false)
    setViolenceType('')
  }

  const buildPayload = () => {
    const trimCodes = (arr) =>
      arr
        .map(({ code, description }) => ({
          code: code.trim().toUpperCase(),
          description: description || '',
        }))
        .filter((c) => c.code.length > 0)

    return {
      part1: part1
        .map(({ line, interval, codes }) => ({
          line,
          interval,
          codes: trimCodes(codes),
        }))
        .filter((row) => row.codes.length > 0),
      part2: part2
        .map(({ interval, codes }) => ({
          interval,
          codes: trimCodes(codes),
        }))
        .filter((row) => row.codes.length > 0),
      sex,
      age:
        age !== ''
          ? ageUnit === 'años'
            ? parseInt(age)
            : ageUnit === 'meses'
              ? Math.floor(parseInt(age) / 12)
              : 0
          : null,
      pregnancy,
      violence,
      violence_type: violence ? violenceType : '',
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    onAnalyze(buildPayload())
  }

  const lineAHasCode = part1[0]?.codes.some((c) => c.code.trim().length > 0)
  const canSubmit = lineAHasCode

  return (
    <form onSubmit={handleSubmit}>
      <div className="card">
        <div className="card-header">
          <span style={{ fontSize: '20px' }}>📋</span>
          <div>
            <h2>Certificado de Defunción — Pregunta 7</h2>
            <div className="card-subtitle">Causas de muerte según el certificado médico</div>
          </div>
        </div>

        <div className="card-body">
          <div className="form-section">
            <div className="section-title">
              <span>I</span> Parte I — Secuencia causal de eventos
            </div>
            <p className="section-hint">
              La línea <strong>(a)</strong> es la causa inmediata de muerte.
              Las líneas siguientes son causas previas que explican la condición inmediata,
              hasta <strong>(d)</strong> cuando corresponda.
              Complete de arriba hacia abajo según el certificado original.
              Puede cargar más de un código por línea cuando el certificado lo indique así.
            </p>

            <table className="cause-table">
              <thead>
                <tr>
                  <th style={{ width: 36 }}>Línea</th>
                  <th className="col-cause">Causa de muerte — condición, enfermedad o proceso</th>
                  <th className="col-interval">Intervalo aprox.</th>
                </tr>
              </thead>
              <tbody>
                {part1.map((row, lineIdx) => (
                  <tr key={row.line}>
                    <td className="line-label">{row.line.toUpperCase()}</td>
                    <td className="col-cause">
                      <div className="cause-line-codes">
                        {row.codes.map((slot, codeIdx) => (
                          <div key={codeIdx} className="cause-code-slot">
                            <CodeSearch
                              value={slot.code}
                              description={slot.description}
                              onChange={({ code, description }) => {
                                updatePart1Code(lineIdx, codeIdx, 'code', code)
                                updatePart1Code(lineIdx, codeIdx, 'description', description)
                              }}
                              placeholder={
                                codeIdx === 0
                                  ? lineIdx === 0
                                    ? 'Causa inmediata de muerte (obligatorio)...'
                                    : `Causa de (${part1[lineIdx - 1]?.line || '?'}) — opcional...`
                                  : 'Otra causa en la misma línea — opcional...'
                              }
                            />
                            {row.codes.length > 1 && (
                              <button
                                type="button"
                                className="btn-remove-code"
                                onClick={() => removePart1Code(lineIdx, codeIdx)}
                                title="Quitar esta causa"
                              >
                                −
                              </button>
                            )}
                          </div>
                        ))}
                        <button
                          type="button"
                          className="btn-add-code"
                          onClick={() => addPart1Code(lineIdx)}
                        >
                          + Causa en línea ({row.line})
                        </button>
                      </div>
                    </td>
                    <td className="col-interval">
                      <input
                        type="text"
                        className="interval-input"
                        value={row.interval}
                        onChange={(e) => {
                          const v = e.target.value
                          setPart1((p) => {
                            const next = [...p]
                            next[lineIdx] = { ...next[lineIdx], interval: v }
                            return next
                          })
                        }}
                        placeholder="ej: 2 horas"
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="form-section">
            <div className="section-title">
              <span>II</span> Parte II — Afecciones contribuyentes
            </div>
            <p className="section-hint">
              Otras afecciones significativas que contribuyeron a la muerte pero que no forman parte
              de la secuencia de la Parte I. Hasta dos bloques; dentro de cada bloque puede indicar varios códigos.
            </p>
            {part2.map((row, rowIdx) => (
              <div key={rowIdx} className="part2-block">
                <div className="part2-number">II — {rowIdx + 1}</div>
                <div className="part2-rows-inner">
                  {row.codes.map((slot, codeIdx) => (
                    <div key={codeIdx} className="part2-row">
                      <div className="cause-code-slot-inline">
                        <CodeSearch
                          value={slot.code}
                          description={slot.description}
                          onChange={({ code, description }) => {
                            updatePart2Code(rowIdx, codeIdx, 'code', code)
                            updatePart2Code(rowIdx, codeIdx, 'description', description)
                          }}
                          placeholder={`Código contribuyente — opcional...`}
                        />
                        {row.codes.length > 1 && (
                          <button
                            type="button"
                            className="btn-remove-code btn-remove-code--inline"
                            onClick={() => removePart2Code(rowIdx, codeIdx)}
                            title="Quitar esta causa"
                          >
                            −
                          </button>
                        )}
                      </div>
                      {codeIdx === 0 ? (
                        <input
                          type="text"
                          className="interval-input"
                          style={{ width: 130, flexShrink: 0 }}
                          value={row.interval}
                          onChange={(e) =>
                            setPart2((prev) => {
                              const next = [...prev]
                              next[rowIdx] = { ...next[rowIdx], interval: e.target.value }
                              return next
                            })
                          }
                          placeholder="Intervalo"
                        />
                      ) : (
                        <div style={{ width: 130, flexShrink: 0 }} aria-hidden />
                      )}
                    </div>
                  ))}
                  <button type="button" className="btn-add-code btn-add-code--part2" onClick={() => addPart2Code(rowIdx)}>
                    + Código en este bloque
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="form-section">
            <div className="section-title">
              <span>+</span> Datos adicionales del fallecido
            </div>

            <div className="additional-grid">
              <div className="field-group">
                <label>Sexo</label>
                <div className="radio-group">
                  {[
                    ['M', 'Masculino'],
                    ['F', 'Femenino'],
                  ].map(([val, label]) => (
                    <label key={val}>
                      <input
                        type="radio"
                        name="sex"
                        value={val}
                        checked={sex === val}
                        onChange={() => {
                          setSex(val)
                          if (val === 'M') setPregnancy('N')
                        }}
                      />
                      {label}
                    </label>
                  ))}
                </div>
              </div>

              <div className="field-group">
                <label>Edad</label>
                <div className="age-row">
                  <input
                    type="number"
                    min="0"
                    max="150"
                    className="age-input"
                    value={age}
                    onChange={(e) => setAge(e.target.value)}
                    placeholder="—"
                  />
                  <select
                    className="age-unit-select"
                    value={ageUnit}
                    onChange={(e) => setAgeUnit(e.target.value)}
                  >
                    <option value="días">días</option>
                    <option value="meses">meses</option>
                    <option value="años">años</option>
                  </select>
                </div>
              </div>

              {sex === 'F' && (
                <div className="field-group" style={{ gridColumn: '1 / -1' }}>
                  <label>¿Estuvo embarazada en los últimos 12 meses?</label>
                  <div className="radio-group">
                    {[
                      ['S', 'Sí'],
                      ['N', 'No'],
                      ['SE', 'Se ignora'],
                    ].map(([val, label]) => (
                      <label key={val}>
                        <input
                          type="radio"
                          name="pregnancy"
                          value={val}
                          checked={pregnancy === val}
                          onChange={() => setPregnancy(val)}
                        />
                        {label}
                      </label>
                    ))}
                  </div>
                </div>
              )}

              <div className="field-group" style={{ gridColumn: '1 / -1' }}>
                <label>¿Fue una muerte violenta?</label>
                <div className="radio-group">
                  <label>
                    <input
                      type="radio"
                      name="violence"
                      checked={!violence}
                      onChange={() => {
                        setViolence(false)
                        setViolenceType('')
                      }}
                    />
                    No
                  </label>
                  <label>
                    <input
                      type="radio"
                      name="violence"
                      checked={violence}
                      onChange={() => setViolence(true)}
                    />
                    Sí
                  </label>
                </div>
                {violence && (
                  <div className="violence-subgroup">
                    <div className="field-label">Tipo de muerte violenta:</div>
                    <div className="radio-group">
                      {[
                        ['A', 'Accidente'],
                        ['S', 'Suicidio'],
                        ['H', 'Homicidio'],
                      ].map(([val, label]) => (
                        <label key={val}>
                          <input
                            type="radio"
                            name="vtype"
                            value={val}
                            checked={violenceType === val}
                            onChange={() => setViolenceType(val)}
                          />
                          {label}
                        </label>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {error && <div className="error-alert">⚠ {error}</div>}

          <div className="form-actions">
            <button type="button" className="btn btn-secondary" onClick={handleReset} disabled={loading}>
              Limpiar
            </button>
            <button type="submit" className="btn btn-primary btn-lg" disabled={loading || !canSubmit}>
              {loading ? '⏳ Analizando...' : '▶ Determinar Causa Básica'}
            </button>
          </div>
        </div>
      </div>
    </form>
  )
}

export default CertificateForm
