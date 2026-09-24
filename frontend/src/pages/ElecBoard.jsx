import React, { useState, useEffect, useCallback } from 'react'
import client from '../api/client.js'
import FilterBar from '../components/FilterBar.jsx'

const COLS = [
  { key: 'site_id', label: '网点ID' },
  { key: 'site_name', label: '网点名称' },
  { key: 'property_name', label: '物业' },
  { key: 'city', label: '城市' },
  { key: 'settle_method', label: '结算方式' },
  { key: 'next_settle_date', label: '下次结算时间' },
  { key: 'need_settle', label: '要结算' },
  { key: 'is_settled', label: '已结算' },
  { key: 'is_paid', label: '付款' },
  { key: 'is_invoiced', label: '发票' },
  { key: 'days_left', label: '剩余天数' },
]

export default function ElecBoard() {
  const [filters, setFilters] = useState({ city: '', property: '', status: '', next_settle_month: '', q: '' })
  const [rows, setRows] = useState([])
  const [data, setData] = useState({ warn_list: [], summary: {} })
  const [loading, setLoading] = useState(false)
  const [detail, setDetail] = useState(null)
  const [toast, setToast] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      Object.entries(filters).forEach(([k, v]) => { if (v) params.set(k, v) })
      const res = await client.get('/board?' + params.toString())
      setRows(res.data.data.rows)
      setData(res.data.data)
    } catch (e) {
      setToast('加载失败: ' + e.message)
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => { load() }, [load])

  const onChange = (k, v) => setFilters((f) => ({ ...f, [k]: v }))
  const onReset = () => setFilters({ city: '', property: '', status: '', next_settle_month: '', q: '' })

  const openDetail = async (siteId) => {
    try {
      const res = await client.get('/board/' + siteId)
      setDetail(res.data.data)
    } catch (e) {
      setToast('详情加载失败: ' + e.message)
    }
  }

  const filterFields = [
    { key: 'city', label: '城市', type: 'text' },
    { key: 'property', label: '物业', type: 'text' },
    { key: 'status', label: '状态', type: 'select', options: [
      { value: 'warn', label: '预警中' }, { value: 'need', label: '要结算' },
      { value: 'unsettled', label: '未结算' }, { value: 'settled', label: '已结算' },
      { value: 'pending', label: '待提单' }, { value: 'cancel', label: '注销' },
    ] },
    { key: 'next_settle_month', label: '结算月份', type: 'text', placeholder: '2026-09' },
    { key: 'q', label: '搜索', type: 'text' },
  ]

  const warnCount = data.summary?.warn_count || 0

  return (
    <div>
      <div className="topbar"><h1>电费看板</h1>
        <span className="muted">提前预警天数 N={data.lead_days ?? 7}</span>
      </div>
      {warnCount > 0 && (
        <div className="warn-banner">⚠ 共有 {warnCount} 个网点需在 {data.lead_days ?? 7} 天内结算（未结算）。请尽快处理。</div>
      )}
      <FilterBar fields={filterFields} values={filters} onChange={onChange} onReset={onReset} />
      <div className="panel" style={{ overflowX: 'auto' }}>
        {loading && <div className="spinner">加载中…</div>}
        <table>
          <thead><tr>{COLS.map(c => <th key={c.key}>{c.label}</th>)}</tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.site_id} className={r.warn_flag === '是' ? 'row-warn' : ''} onClick={() => openDetail(r.site_id)} style={{ cursor: 'pointer' }}>
                {COLS.map(c => {
                  if (c.key === 'need_settle' || c.key === 'is_settled' || c.key === 'is_paid' || c.key === 'is_invoiced') {
                    const v = r[c.key]
                    return <td key={c.key}>{v === '是' ? <span className="badge ok">是</span> : <span className="badge muted">否</span>}</td>
                  }
                  if (c.key === 'days_left') {
                    return <td key={c.key}>{r.days_left == null ? '-' : r.days_left}</td>
                  }
                  return <td key={c.key}>{r[c.key]}</td>
                })}
              </tr>
            ))}
          </tbody>
        </table>
        <div className="muted" style={{ marginTop: 8 }}>点击任意行查看明细（合同/发票/抄表/商户提交/预警记录）。</div>
      </div>

      {detail && (
        <div className="drawer-mask" onClick={() => setDetail(null)}>
          <div className="drawer" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <h3>网点明细 · {detail.station?.site_id}</h3>
              <button className="btn ghost sm" onClick={() => setDetail(null)}>关闭</button>
            </div>
            <p className="muted">{detail.station?.site_name} / {detail.station?.property_name}</p>
            <div className="panel">
              <b>基础信息</b>
              <ul style={{ margin: '6px 0', paddingLeft: 18 }}>
                <li>城市/区域: {detail.station?.city} / {detail.station?.district}</li>
                <li>结算方式: {detail.station?.settle_method}（周期 {detail.station?.settle_cycle}）</li>
                <li>下次结算: {detail.station?.next_settle_date}（剩余 {detail.station?.days_left ?? '-'} 天）</li>
                <li>电表度数: {detail.station?.last_meter_reading}（{detail.station?.last_read_date}）</li>
                <li>结算金额: {detail.station?.settle_amount} / 总金额: {detail.station?.total_amount}</li>
                <li>合同期限: {detail.station?.contract_term}</li>
                <li>发票类型: {detail.station?.invoice_type} / 付款: {detail.station?.is_paid} / 发票: {detail.station?.is_invoiced}</li>
                <li>收款账户: {detail.station?.account_info}</li>
                <li>换电柜: {detail.station?.cabinet_count} 台 / {detail.station?.cabinet_type} / 状态 {detail.station?.meter_status}</li>
              </ul>
            </div>
            <div className="panel">
              <b>预警记录 ({detail.warn_records?.length || 0})</b>
              <ul style={{ margin: '6px 0', paddingLeft: 18 }}>
                {(detail.warn_records || []).map(w => (
                  <li key={w.id}>{w.warn_reason} · 等级{w.warn_level} · 到期 {w.due_date}</li>
                ))}
                {(detail.warn_records || []).length === 0 && <li className="muted">无</li>}
              </ul>
            </div>
            <div className="panel">
              <b>商户提交 ({detail.merchant_profiles?.length || 0})</b>
              <ul style={{ margin: '6px 0', paddingLeft: 18 }}>
                {(detail.merchant_profiles || []).map(m => (
                  <li key={m.id}>{m.submit_role} · {m.merchant_name} · {m.submit_time}</li>
                ))}
                {(detail.merchant_profiles || []).length === 0 && <li className="muted">无扫码提交</li>}
              </ul>
            </div>
            {detail.pending?.length > 0 && (
              <div className="panel"><b>待提单</b><p>{detail.pending[0].note}</p></div>
            )}
            {detail.cancel?.length > 0 && (
              <div className="panel"><b>注销</b><p>{detail.cancel[0].status} · 户编 {detail.cancel[0].account_no}</p></div>
            )}
          </div>
        </div>
      )}
      {toast && <div className="toast" onClick={() => setToast('')}>{toast}</div>}
    </div>
  )
}
