import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import client from '../api/client.js'

const ROLES = ['物业', '业务员', '商户']

export default function Scan() {
  const [params] = useSearchParams()
  const siteId = params.get('site_id') || ''
  const token = params.get('token') || ''
  const exp = params.get('exp') || ''

  const [valid, setValid] = useState(null)
  const [form, setForm] = useState({
    site_name: '', merchant_name: '', meter_reading: '', elec_amount: '',
    elec_price: '', service_price: '', share_ratio: '', next_settle_date: '',
    invoice_type: '', is_paid: '否', is_invoiced: '否', account_info: '',
    contact_name: '', contact_phone: '', submit_role: '物业', remark: '',
  })
  const [images, setImages] = useState([])
  const [msg, setMsg] = useState('')

  useEffect(() => {
    if (!siteId || !token || !exp) { setValid(false); return }
    client.get(`/scan/verify?site_id=${encodeURIComponent(siteId)}&token=${encodeURIComponent(token)}&exp=${encodeURIComponent(exp)}`)
      .then(r => setValid(r.data.data.valid))
      .catch(() => setValid(false))
  }, [siteId, token, exp])

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault()
    if (!valid) { setMsg('二维码无效或已过期'); return }
    const fd = new FormData()
    Object.entries(form).forEach(([k, v]) => fd.append(k, v))
    images.forEach(f => fd.append('images', f))
    try {
      const res = await client.post(`/scan/submit?site_id=${encodeURIComponent(siteId)}&token=${encodeURIComponent(token)}&exp=${encodeURIComponent(exp)}`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setMsg('提交成功！感谢您的录入。')
      setForm({ ...form, meter_reading: '', elec_amount: '', elec_price: '', service_price: '', share_ratio: '', next_settle_date: '', account_info: '', remark: '' })
      setImages([])
    } catch (err) {
      setMsg('提交失败: ' + (err.message || '未知错误'))
    }
  }

  if (valid === false) {
    return (
      <div className="scan-wrap">
        <h2>电费扫码录入</h2>
        <p className="muted">二维码无效或已过期，请重新扫描或由管理员生成新的二维码。</p>
      </div>
    )
  }

  return (
    <div className="scan-wrap">
      <h2>电费扫码录入</h2>
      <p className="muted">网点ID: {siteId}{valid === true && ' · 校验通过'}</p>
      <form onSubmit={submit}>
        <div className="field"><label>网点名称</label><input value={form.site_name} onChange={e => set('site_name', e.target.value)} /></div>
        <div className="field"><label>物业/商户名称</label><input value={form.merchant_name} onChange={e => set('merchant_name', e.target.value)} /></div>
        <div className="field"><label>本次抄表度数</label><input inputMode="decimal" value={form.meter_reading} onChange={e => set('meter_reading', e.target.value)} /></div>
        <div className="field"><label>电费/结算金额</label><input inputMode="decimal" value={form.elec_amount} onChange={e => set('elec_amount', e.target.value)} /></div>
        <div className="field"><label>电单价</label><input inputMode="decimal" value={form.elec_price} onChange={e => set('elec_price', e.target.value)} /></div>
        <div className="field"><label>服务费单价</label><input inputMode="decimal" value={form.service_price} onChange={e => set('service_price', e.target.value)} /></div>
        <div className="field"><label>分成比例</label><input value={form.share_ratio} onChange={e => set('share_ratio', e.target.value)} placeholder="如 30% 或 0.3" /></div>
        <div className="field"><label>下次结算时间</label><input value={form.next_settle_date} onChange={e => set('next_settle_date', e.target.value)} placeholder="YYYY-MM-DD" /></div>
        <div className="field"><label>发票类型</label><input value={form.invoice_type} onChange={e => set('invoice_type', e.target.value)} placeholder="普票/专票" /></div>
        <div className="field"><label>是否付款</label>
          <select value={form.is_paid} onChange={e => set('is_paid', e.target.value)}><option>是</option><option>否</option></select></div>
        <div className="field"><label>是否已开发票/收据</label>
          <select value={form.is_invoiced} onChange={e => set('is_invoiced', e.target.value)}><option>是</option><option>否</option></select></div>
        <div className="field"><label>收款账户信息</label><input value={form.account_info} onChange={e => set('account_info', e.target.value)} /></div>
        <div className="field"><label>联系人</label><input value={form.contact_name} onChange={e => set('contact_name', e.target.value)} /></div>
        <div className="field"><label>联系电话</label><input inputMode="tel" value={form.contact_phone} onChange={e => set('contact_phone', e.target.value)} /></div>
        <div className="field"><label>提交人角色</label>
          <select value={form.submit_role} onChange={e => set('submit_role', e.target.value)}>
            {ROLES.map(r => <option key={r}>{r}</option>)}
          </select></div>
        <div className="field"><label>备注</label><input value={form.remark} onChange={e => set('remark', e.target.value)} /></div>
        <div className="field"><label>图片上传（合同/通知单，可选）</label>
          <input type="file" multiple accept="image/*" onChange={e => setImages(Array.from(e.target.files))} /></div>
        <button className="btn" type="submit" style={{ width: '100%', padding: 12 }}>提交</button>
      </form>
      {msg && <p style={{ marginTop: 12, fontWeight: 600 }}>{msg}</p>}
    </div>
  )
}
