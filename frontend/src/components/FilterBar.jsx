import React from 'react'

// Reusable filter bar. `fields` is an array of:
//   { key, label, type: 'text'|'select', options?: [{value,label}] }
// `values` holds current values; `onChange(key, value)` updates state.
export default function FilterBar({ fields, values, onChange, onReset }) {
  return (
    <div className="filters">
      {fields.map((f) => (
        <span key={f.key} style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
          <label>{f.label}</label>
          {f.type === 'select' ? (
            <select value={values[f.key] || ''} onChange={(e) => onChange(f.key, e.target.value)}>
              <option value="">全部</option>
              {f.options.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              placeholder={f.placeholder || ''}
              value={values[f.key] || ''}
              onChange={(e) => onChange(f.key, e.target.value)}
            />
          )}
        </span>
      ))}
      {onReset && (
        <button className="btn ghost sm" onClick={onReset}>重置</button>
      )}
    </div>
  )
}
