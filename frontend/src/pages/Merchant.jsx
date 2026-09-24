import React, { useState, useEffect } from 'react'
import client from '../api/client.js'

export default function Merchant() {
  const [siteId, setSiteId] = useState('')
  const [qrUrl, setQrUrl] = useState('')
  const [scanUrl, setScanUrl] = useState('')
  const [subs, setSubs] = useState([])
  const [toast, setToast] = useState('')

  const loadSubs = async () => {
    try {
      const res = await client.get('/merchant/list')
      setSubs(res.data.data.rows)
    } catch (e) { setToast('加载提交列表失败: ' + e.message) }
  }
  useEffect(() => { loadSubs() }, [])

  const genQr = async () => {
    if (!siteId) { setToast('请输入网点ID'); return }
    try {
      const res = await client.get('/merchant/qr?site_id=' + encodeURIComponent(siteId), { responseType: 'blob' })
      if (qrUrl) URL.revokeObjectURL(qrUrl)
      const url = URL.createObjectURL(res.data)
      setQrUrl(url)
      // derive the scan URL from current origin + token embedded in QR (display hint)
      const base = window.location.origin
      setScanUrl(base + '/scan?site_id=' + encodeURIComponent(siteId) + ' (含限时token，见二维码)')
    } catch (e) {
      setToast('生成二维码失败: ' + e.message + '（管理接口需 ADMIN_TOKEN）')
    }
  }

  return (
    <div>
      <div className="topbar"><h1>商户信息录入（扫码）</h1></div>
      <div className="panel">
        <h3>生成网点扫码二维码</h3>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <input placeholder="网点ID" value={siteId} onChange={(e) => setSiteId(e.target.value)} />
          <button className="btn" onClick={genQr}>生成二维码</button>
        </div>
        {qrUrl && (
          <div style={{ marginTop: 14 }}>
            <img className="qr-img" src={qrUrl} alt="scan qr" />
            <p className="muted">手机扫码打开 H5 表单，URL 含限时 token（默认 24h）。公网仅暴露 /scan 与只读看板。</p>
            <p className="muted">{scanUrl}</p>
          </div>
        )}
      </div>

      <div className="panel">
        <h3>扫码提交记录（{subs.length}）</h3>
        <table>
          <thead><tr><th>ID</th><th>网点ID</th><th>商户/物业</th><th>角色</th><th>提交时间</th><th>状态</th></tr></thead>
          <tbody>
            {subs.map((s) => (
              <tr key={s.id}>
                <td>{s.id}</td><td>{s.site_id}</td><td>{s.merchant_name}</td>
                <td>{s.submit_role}</td><td>{s.submit_time}</td>
                <td>{s.status}</td>
              </tr>
            ))}
            {subs.length === 0 && <tr><td colSpan={6} className="muted">暂无提交</td></tr>}
          </tbody>
        </table>
      </div>
      {toast && <div className="toast" onClick={() => setToast('')}>{toast}</div>}
    </div>
  )
}
