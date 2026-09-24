import React, { useState, useEffect, useCallback } from 'react'
import ReactECharts from 'echarts-for-react'
import client from '../api/client.js'
import FilterBar from '../components/FilterBar.jsx'

export default function Expense() {
  const [filters, setFilters] = useState({ city: '', property: '', settle_method: '', need_settle: '', is_paid: '' })
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      Object.entries(filters).forEach(([k, v]) => { if (v) params.set(k, v) })
      const res = await client.get('/expense?' + params.toString())
      setReport(res.data.data)
    } catch (e) {
      console.error(e)
    } finally { setLoading(false) }
  }, [filters])

  useEffect(() => { load() }, [load])

  const onChange = (k, v) => setFilters((f) => ({ ...f, [k]: v }))
  const onReset = () => setFilters({ city: '', property: '', settle_method: '', need_settle: '', is_paid: '' })

  const exportUrl = () => {
    const params = new URLSearchParams()
    Object.entries(filters).forEach(([k, v]) => { if (v) params.set(k, v) })
    return (client.defaults.baseURL || '/api') + '/expense/export?' + params.toString()
  }

  const m = report?.metrics || {}
  const pieOption = {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie', radius: ['40%', '70%'],
      data: (report?.categories || []).map(c => ({ name: c.name, value: c.value })),
      label: { formatter: '{b}: {c}' },
    }],
  }
  const barOption = {
    tooltip: { trigger: 'axis' },
    grid: { left: 120, right: 20 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: (report?.by_property || []).map(p => p.name).reverse() },
    series: [{ type: 'bar', data: (report?.by_property || []).map(p => p.value).reverse() }],
  }
  const trendOption = {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: (report?.trend || []).map(t => t.month) },
    yAxis: { type: 'value' },
    series: [{ type: 'line', smooth: true, data: (report?.trend || []).map(t => t.value), areaStyle: {} }],
  }

  const filterFields = [
    { key: 'city', label: '城市', type: 'text' },
    { key: 'property', label: '物业', type: 'text' },
    { key: 'settle_method', label: '结算方式', type: 'text', placeholder: '如 线上结算' },
    { key: 'need_settle', label: '要结算', type: 'select', options: [{ value: '是', label: '是' }] },
    { key: 'is_paid', label: '已付款', type: 'select', options: [{ value: '是', label: '是' }, { value: '否', label: '否' }] },
  ]

  return (
    <div>
      <div className="topbar"><h1>费用支出看板</h1>
        <a className="btn" href={exportUrl()}>导出 Excel</a>
      </div>
      <FilterBar fields={filterFields} values={filters} onChange={onChange} onReset={onReset} />
      {loading && <div className="spinner">加载中…</div>}
      {report && (
        <>
          <div className="metrics">
            <div className="metric"><div className="label">总支出(元)</div><div className="value">{m.total}</div></div>
            <div className="metric"><div className="label">电费(元)</div><div className="value">{m.电费}</div></div>
            <div className="metric"><div className="label">场地费(元)</div><div className="value">{m.场地费}</div></div>
            <div className="metric"><div className="label">押金(元)</div><div className="value">{m.押金}</div></div>
            <div className="metric"><div className="label">分成(元)</div><div className="value">{m.分成}</div></div>
            <div className="metric"><div className="label">环比</div><div className="value">{m.环比 == null ? '—' : m.环比}</div></div>
            <div className="metric"><div className="label">网点数</div><div className="value">{m.site_count}</div></div>
          </div>
          <div className="panel"><h3>费用类型占比</h3><ReactECharts option={pieOption} style={{ height: 300 }} /></div>
          <div className="panel"><h3>按物业支出</h3><ReactECharts option={barOption} style={{ height: 360 }} /></div>
          <div className="panel"><h3>按月趋势（下次结算月份）</h3><ReactECharts option={trendOption} style={{ height: 300 }} /></div>
        </>
      )}
    </div>
  )
}
