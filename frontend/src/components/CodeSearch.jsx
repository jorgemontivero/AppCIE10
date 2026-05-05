import { useState, useEffect, useRef, useCallback } from 'react'

/**
 * Buscador autocomplete de códigos CIE-10.
 *
 * Props:
 *   value       – código seleccionado actualmente
 *   description – descripción del código seleccionado
 *   onChange    – fn({ code, description }) llamada al seleccionar
 *   placeholder – texto placeholder del input
 *   disabled    – deshabilitar el input
 */
function CodeSearch({ value, description, onChange, placeholder, disabled }) {
  const [inputVal, setInputVal] = useState(value || '')
  const [suggestions, setSuggestions] = useState([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [activeIdx, setActiveIdx] = useState(-1)

  const debounceRef = useRef(null)
  const containerRef = useRef(null)
  const inputRef = useRef(null)

  // Sync input when external value changes (e.g., reset)
  useEffect(() => {
    setInputVal(value || '')
    if (!value) {
      setSuggestions([])
      setOpen(false)
    }
  }, [value])

  // Close on outside click
  useEffect(() => {
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const fetchSuggestions = useCallback(async (q) => {
    if (q.length < 2) {
      setSuggestions([])
      setOpen(false)
      return
    }
    setLoading(true)
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&limit=15`)
      if (!res.ok) throw new Error('Error de red')
      const data = await res.json()
      setSuggestions(data)
      setOpen(data.length > 0)
      setActiveIdx(-1)
    } catch {
      setSuggestions([])
      setOpen(false)
    } finally {
      setLoading(false)
    }
  }, [])

  const handleChange = (e) => {
    const val = e.target.value
    setInputVal(val)
    if (!val) {
      onChange({ code: '', description: '' })
      setSuggestions([])
      setOpen(false)
      return
    }
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => fetchSuggestions(val), 280)
  }

  const handleSelect = (item) => {
    const code = item.codigo_2 || item.codigo_1
    const desc = item.categoria_2 || item.categoria_1 || ''
    setInputVal(code)
    onChange({ code, description: desc })
    setSuggestions([])
    setOpen(false)
  }

  const handleClear = () => {
    setInputVal('')
    onChange({ code: '', description: '' })
    setSuggestions([])
    setOpen(false)
    inputRef.current?.focus()
  }

  const handleKeyDown = (e) => {
    if (!open || suggestions.length === 0) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIdx((i) => Math.min(i + 1, suggestions.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIdx((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter' && activeIdx >= 0) {
      e.preventDefault()
      handleSelect(suggestions[activeIdx])
    } else if (e.key === 'Escape') {
      setOpen(false)
    }
  }

  const hasSelection = Boolean(value)

  return (
    <div className="code-search" ref={containerRef}>
      <div className="code-search-input-row">
        <input
          ref={inputRef}
          type="text"
          className="code-search-input"
          value={inputVal}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (suggestions.length > 0) setOpen(true)
          }}
          placeholder={placeholder || 'Buscar código o descripción CIE-10...'}
          disabled={disabled}
          autoComplete="off"
          spellCheck="false"
        />
        {loading && <span className="code-search-spinner">↻</span>}
        {hasSelection && !loading && (
          <button
            type="button"
            className="code-search-clear"
            onClick={handleClear}
            title="Limpiar"
          >
            ✕
          </button>
        )}
      </div>

      {hasSelection && description && (
        <div className="code-search-selected">
          <span className="code-badge-selected">{value}</span>
          <span className="code-search-selected-desc">{description}</span>
        </div>
      )}

      {open && (
        <ul className="code-search-dropdown" role="listbox">
          {suggestions.length === 0 ? (
            <li className="code-search-empty">Sin resultados</li>
          ) : (
            suggestions.map((item, idx) => {
              const code = item.codigo_2 || item.codigo_1
              const desc = item.categoria_2 || item.categoria_1 || ''
              return (
                <li
                  key={code + idx}
                  className={`code-search-item${idx === activeIdx ? ' code-search-item--active' : ''}`}
                  role="option"
                  aria-selected={idx === activeIdx}
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => handleSelect(item)}
                  onMouseEnter={() => setActiveIdx(idx)}
                  style={idx === activeIdx ? { background: 'var(--blue-50)' } : undefined}
                >
                  <span className="code-badge">{code}</span>
                  <span className="code-item-desc">{desc}</span>
                </li>
              )
            })
          )}
        </ul>
      )}
    </div>
  )
}

export default CodeSearch
