import React, { useState, useEffect } from 'react'
import client from '../api/client.js'

export default function Pending() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const res = await client.get('/pending')
      setRows(res.data.data.rows)
    } catch (e) {
      console.error(e)
    } finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  return (
    <div>
      <div className="topbar"><h1>待提单管理</h1><span className="muted">共 {rows.length} 条</span></div>
      <div className="panel" style={{ overflowX: 'auto' }}>
        {loading && <div className="spinner">加载中…</div>}
        <table>
          <thead><tr><th>网点ID</th><th>网点名称</th><th>说明</th><th>状态</th></tr></thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={r.id || i}>
                <td>{r.site_id || '-'}</td>
                <td>{r.site_name || '-'}</td>
                <td>{r.note}</td>
                <td>{r.status ? <span className="badge warn">{r.status}</span> : '-'}</td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={4} className="muted">暂无待提单数据</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
