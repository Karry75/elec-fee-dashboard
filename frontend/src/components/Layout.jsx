import React from 'react'
import { NavLink, Outlet } from 'react-router-dom'

const NAV = [
  { to: '/', label: '数据整合主看板', end: true },
  { to: '/board', label: '电费看板' },
  { to: '/merchant', label: '商户信息录入' },
  { to: '/expense', label: '费用支出看板' },
  { to: '/pending', label: '待提单管理' },
  { to: '/cancel', label: '注销网点管理' },
]

export default function Layout() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">⚡ 电费管理系统</div>
        <nav>
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to} end={n.end}>
              {n.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
