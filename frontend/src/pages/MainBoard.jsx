import React, { useState, useEffect, useCallback } from 'react'
import client from '../api/client.js'
import FilterBar from '../components/FilterBar.jsx'

const COLS = [
  { key: 'site_id', label: '网点ID' },
  { key: 'site_name', label: '网点名称' },
  { key: 'property_name', label: '物业' },
  { key: 'city', label: '城市' },
  { key: 'last_meter_reading', label: '电表度数', editable: true },
  { key: 'settle_amount', label: '电费金额', editable: true },
  { key: 'settle_method', label: '结算方式', editable: true },
  { key: 'next_settle_date', label: '下次结算时间' },
  { key: 'need_settle', label: '是否要结算' },
  { key: 'pay_status', label: '付款/发票状态' },
  { key: 'pending_flag', label: '待提单' },
  { key: 'cancel_flag', label: '注销' },
]

export default function MainBoard() {
  const [filters, setFilters] = useState({ city: '', property: '', need_settle: '', is_paid: '', source: '', diff_only: '', q: '' })
  const [rows, setRows] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [editBuf, setEditBuf] = useState({})
  const [toast, setToast] = useState('')

  const load = useCallback(async (p = page) => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ page: p, page_size: 50 })
      Object.entries(filters).forEach(([k, v]) => { if (v) params.set(k, v) })
      const res = await client.get('/dashboard?' + params.toString())
      setRows(res.data.data.rows)
      setTotal(res.data.data.total)
    } catch (e) {
      setToast('加载失败: ' + e.message)
    } finally {
      setLoading(false)
    }
  }, [filters, page])

  useEffect(() => { load(1); setPage(1) }, [filters])
  useEffect(() => { load(page) }, [page])

  const onChange = (k, v) => setFilters((f) => ({ ...f, [k]: v }))
  const onReset = () => setFilters({ city: '', property: '', need_settle: '', is_paid: '', source: '', diff_only: '', q: '' })

  const startEdit = (row) => {
    setEditingId(row.site_id)
    setEditBuf({
      settle_method: row.settle_method ?? '',
      last_meter_reading: row.last_meter_reading ?? '',
      settle_amount: row.settle_amount ?? '',
    })
  }

  const saveEdit = async (row) => {
    const fields = ['settle_method', 'last_meter_reading', 'settle_amount']
    let okCount = 0
    for (const f of fields) {
      const nv = String(editBuf[f] ?? '')
      const ov = String(row[f] ?? '')
      if (nv !== ov) {
        try {
          await client.post('/admin/writeback', {
            site_id: row.site_id, field_name: f, new_value: nv, old_value: ov, operator: 'admin',
          })
          okCount++
        } catch (e) {
          setToast('写回失败 ' + f + ': ' + e.message)
        }
      }
    }
    setEditingId(null)
    if (okCount) { setToast('已提交 ' + okCount + ' 项写回（待DBA授权）'); load(page) }
  }

  const srcBadge = (row, field) => {
    const diff = row.diff_fields || []
    if (!diff.includes(field)) return null
    const src = (row.source_flag && row.source_flag[field]) || ''
    return <span className={'badge src-' + (src || 'A')} title={'来源:' + src + ' 不一致'}>{src}</span>
  }

  const filterFields = [
    { key: 'city', label: '城市', type: 'text', placeholder: '如 深圳' },
    { key: 'property', label: '物业', type: 'text', placeholder: '物业名称' },
    { key: 'need_settle', label: '要结算', type: 'select', options: [{ value: '是', label: '是' }, { value: '否', label: '否' }] },
    { key: 'is_paid', label: '已付款', type: 'select', options: [{ value: '是', label: '是' }, { value: '否', label: '否' }] },
    { key: 'source', label: '来源', type: 'select', options: [{ value: 'A', label: '来自A' }, { value: 'B', label: '来自B' }] },
    { key: 'diff_only', label: '仅差异', type: 'select', options: [{ value: '1', label: '是' }] },
    { key: 'q', label: '搜索', type: 'text', placeholder: '名称/ID' },
  ]

  return (
    <div>
      <div className="topbar"><h1>数据整合主看板</h1>
        <button className="btn ghost sm" onClick={() => { if (window.confirm('确认从 Excel 重新同步？')) client.post('/import/excel').then(() => { setToast('同步完成'); load(1) }).catch(e => setToast('同步失败:' + e.message)) }}>从 Excel 同步</button>
      </div>
      <FilterBar fields={filterFields} values={filters} onChange={onChange} onReset={onReset} />
      <div className="panel" style={{ overflowX: 'auto' }}>
        {loading && <div className="spinner">加载中…</div>}
        <table>
          <thead><tr>{COLS.map(c => <th key={c.key}>{c.label}</th>)}<th>操作</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.site_id} className={r.diff_fields && r.diff_fields.length ? '' : ''}>
                {COLS.map(c => {
                  if (c.key === 'pay_status') {
                    return <td key={c.key}>付款:{r.is_paid || '-'} / 发票:{r.is_invoiced || '-'}</td>
                  }
                  if (c.editable && editingId === r.site_id) {
                    return <td key={c.key} className="cell-diff">{srcBadge(r, c.key)}
                      <input value={editBuf[c.key]} onChange={(e) => setEditBuf(b => ({ ...b, [c.key]: e.target.value }))} style={{ width: 90 }} /></td>
                  }
                  let content = r[c.key]
                  if (c.key === 'pending_flag' || c.key === 'cancel_flag') {
                    content = r[c.key] === '是' ? <span className="badge danger">是</span> : <span className="badge muted">否</span>
                  } else if (c.key === 'need_settle') {
                    content = r.need_settle === '是' ? <span className="badge ok">是</span> : <span className="badge muted">否</span>
                  }
                  const cls = (r.diff_fields || []).includes(c.key) ? 'cell-diff' : ''
                  return <td key={c.key} className={cls}>{srcBadge(r, c.key)}{content}</td>
                })}
                <td>{editingId === r.site_id
                  ? <><button className="btn sm" onClick={() => saveEdit(r)}>保存</button> <button className="btn ghost sm" onClick={() => setEditingId(null)}>取消</button></>
                  : <button className="btn ghost sm" onClick={() => startEdit(r)}>编辑写回</button>}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="pagination">
          <button className="btn ghost sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>上一页</button>
          <span className="muted">第 {page} 页 / 共 {total} 条</span>
          <button className="btn ghost sm" disabled={page * 50 >= total} onClick={() => setPage(p => p + 1)}>下一页</button>
        </div>
        <div className="muted" style={{ marginTop: 8 }}>黄色高亮 = A/B 数据不一致；徽标 A/B = 字段主来源。编辑后进入写回队列，需 DBA 授权落库。</div>
      </div>
      {toast && <div className="toast" onClick={() => setToast('')}>{toast}</div>}
    </div>
  )
}
