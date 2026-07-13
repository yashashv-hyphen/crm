import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getAdminDashboard } from '../api/dashboard'
import { getPleAgentSummary, getPleMcidDetail } from '../api/ple'
import PleMcidDrawer from '../components/PleMcidDrawer'

const stageName = (name) => name?.replace(/ Pending$/i, '') ?? name

function PleAgentMcidTable({ agentUserId, agentName, onBack }) {
  const [selectedMcid, setSelectedMcid] = useState(null)
  const { data: mcidDetail, isLoading } = useQuery({
    queryKey: ['ple-mcid-detail', agentUserId],
    queryFn: () => getPleMcidDetail({ agent_user_id: agentUserId }).then((r) => r.data),
  })

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      {selectedMcid && <PleMcidDrawer mcid={selectedMcid} onClose={() => setSelectedMcid(null)} />}
      <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-3">
        <button onClick={onBack} className="text-xs text-blue-600 hover:underline">← Back to agents</button>
        <h2 className="font-semibold text-gray-700">{agentName}'s MCIDs</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
            <tr>
              <th className="px-5 py-3 text-left">MCID</th>
              <th className="px-3 py-3 text-left">FBA Status</th>
              <th className="px-3 py-3 text-left">SP Status</th>
              <th className="px-3 py-3 text-left">CP Adoption</th>
              <th className="px-3 py-3 text-left">Cross Launch</th>
              <th className="px-3 py-3 text-left">Cross Launch Final Stage</th>
              <th className="px-3 py-3 text-left">CL</th>
              <th className="px-3 py-3 text-right">Buyable ASIN</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {isLoading ? (
              <tr><td colSpan={8} className="px-5 py-6 text-center text-gray-400">Loading...</td></tr>
            ) : !mcidDetail?.length ? (
              <tr><td colSpan={8} className="px-5 py-6 text-center text-gray-400">No MCIDs for this agent</td></tr>
            ) : (
              mcidDetail.map((row) => (
                <tr key={row.mcid} className="hover:bg-gray-50 cursor-pointer" onClick={() => setSelectedMcid(row.mcid)}>
                  <td className="px-5 py-3 font-mono text-blue-600 hover:underline">{row.mcid}</td>
                  <td className="px-3 py-3">{row.fba_status || '—'}</td>
                  <td className="px-3 py-3">{row.sp_status || '—'}</td>
                  <td className="px-3 py-3">{row.cp_adoption || '—'}</td>
                  <td className="px-3 py-3">{row.narf_cross_launch || '—'}</td>
                  <td className="px-3 py-3">{row.cross_launch_final_stage || '—'}</td>
                  <td className="px-3 py-3">{row.cl_status || '—'}</td>
                  <td className="px-3 py-3 text-right">{row.buyable_asin?.toLocaleString() ?? '—'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function PleTab() {
  const [selectedAgent, setSelectedAgent] = useState(null)
  const { data: agentSummary, isLoading: loadingAgents } = useQuery({
    queryKey: ['ple-agent-summary'],
    queryFn: () => getPleAgentSummary().then((r) => r.data),
  })

  if (selectedAgent) {
    return (
      <PleAgentMcidTable
        agentUserId={selectedAgent.agent_user_id}
        agentName={selectedAgent.agent}
        onBack={() => setSelectedAgent(null)}
      />
    )
  }

  return (
    <div className="space-y-6">
      {/* User-wise Breakdown */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-700">User-wise Breakdown</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
              <tr>
                <th className="px-5 py-3 text-left">Agent</th>
                <th className="px-3 py-3 text-right">Launches</th>
                <th className="px-3 py-3 text-right">FBA Status</th>
                <th className="px-3 py-3 text-right">FBA Live Selection</th>
                <th className="px-3 py-3 text-right">SP</th>
                <th className="px-3 py-3 text-right">Any Deal Adoption (CP)</th>
                <th className="px-3 py-3 text-right">NARF/Cross Launch (CL)</th>
                <th className="px-3 py-3 text-right">Buyable ASIN (Total Live Selection)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {loadingAgents ? (
                <tr><td colSpan={8} className="px-5 py-6 text-center text-gray-400">Loading...</td></tr>
              ) : !agentSummary?.length ? (
                <tr><td colSpan={8} className="px-5 py-6 text-center text-gray-400">No PLE launches data uploaded yet</td></tr>
              ) : (
                agentSummary.map((row) => (
                  <tr key={row.agent} className="hover:bg-gray-50 cursor-pointer" onClick={() => setSelectedAgent(row)}>
                    <td className="px-5 py-3 font-medium text-blue-600 hover:underline">{row.agent}</td>
                    <td className="px-3 py-3 text-right">{row.num_launches?.toLocaleString()}</td>
                    <td className="px-3 py-3 text-right">{row.fba_status_count?.toLocaleString()}</td>
                    <td className="px-3 py-3 text-right">{row.fba_live_selection?.toLocaleString()}</td>
                    <td className="px-3 py-3 text-right">{row.sp_status_count?.toLocaleString()}</td>
                    <td className="px-3 py-3 text-right">{row.cp_adoption_count?.toLocaleString()}</td>
                    <td className="px-3 py-3 text-right">{row.narf_cross_launch_count?.toLocaleString()}</td>
                    <td className="px-3 py-3 text-right">{row.buyable_asin?.toLocaleString()}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default function AdminDashboard() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('stages')
  const [filters, setFilters] = useState({ year: new Date().getFullYear() })
  const [appliedFilters, setAppliedFilters] = useState(filters)

  const { data, isLoading } = useQuery({
    queryKey: ['admin-dashboard', appliedFilters],
    queryFn: () => getAdminDashboard(appliedFilters).then((r) => r.data),
    refetchInterval: 30_000,
  })

  const drillDown = (activityId, fosId) => {
    const params = new URLSearchParams()
    if (activityId) params.set('activity_id', activityId)
    if (fosId) params.set('fos_id', fosId)
    navigate(`/admin/leads?${params}`)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-800">Admin Dashboard</h1>
        {data && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 px-5 py-3 text-center">
            <div className="text-2xl font-bold text-blue-600">{data.total_leads?.toLocaleString()}</div>
            <div className="text-xs text-gray-500 mt-0.5">Total Leads</div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200">
        {[
          { key: 'stages', label: 'Stages' },
          { key: 'ple', label: 'PLE' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
              activeTab === tab.key
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'ple' && <PleTab />}

      {activeTab === 'stages' && (
        <>
      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 flex items-end gap-4 flex-wrap">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Year</label>
          <input
            type="number"
            value={filters.year || ''}
            onChange={(e) => setFilters((f) => ({ ...f, year: e.target.value }))}
            className="border border-gray-300 rounded px-2 py-1 text-sm w-24"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">From Date</label>
          <input
            type="date"
            value={filters.from_date || ''}
            onChange={(e) => setFilters((f) => ({ ...f, from_date: e.target.value }))}
            className="border border-gray-300 rounded px-2 py-1 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">To Date</label>
          <input
            type="date"
            value={filters.to_date || ''}
            onChange={(e) => setFilters((f) => ({ ...f, to_date: e.target.value }))}
            className="border border-gray-300 rounded px-2 py-1 text-sm"
          />
        </div>
        <button
          onClick={() => setAppliedFilters({ ...filters })}
          className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700"
        >
          Apply
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : (
        <>
          {/* Overall Stage Summary */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-700">Overall Stage Summary (All Agents)</h2>
            </div>
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
                <tr>
                  <th className="px-5 py-3 text-left">Stage</th>
                  <th className="px-5 py-3 text-right">Total Assigned</th>
                  <th className="px-5 py-3 text-right">Moved to Next</th>
                  <th className="px-5 py-3 text-right">Pending</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {(data?.overall_stage_summary || []).map((row) => (
                  <tr key={row.activity_id ?? row.activity_name} className="hover:bg-gray-50">
                    <td className="px-5 py-3 font-medium">
                      {stageName(row.activity_name)}
                      {!row.activity_id && (
                        <span className="ml-1.5 text-[10px] bg-green-100 text-green-700 font-semibold px-1.5 py-0.5 rounded">Self</span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-right">
                      <button
                        onClick={() => row.activity_id ? drillDown(row.activity_id) : navigate(`/admin/leads?current_stage=${encodeURIComponent(row.activity_name)}`)}
                        className="text-blue-600 hover:underline font-semibold"
                      >
                        {row.total_assigned?.toLocaleString()}
                      </button>
                    </td>
                    <td className="px-5 py-3 text-right text-gray-700">{row.moved_to_next?.toLocaleString()}</td>
                    <td className="px-5 py-3 text-right text-gray-700">{row.pending?.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Agent-wise Breakdown */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-700">Agent-wise Breakdown</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
                  <tr>
                    <th className="px-5 py-3 text-left">Agent</th>
                    {(data?.overall_stage_summary || []).map((s) => (
                      <th key={s.activity_id ?? s.activity_name} className="px-3 py-3 text-right" colSpan={2}>
                        {stageName(s.activity_name)}
                      </th>
                    ))}
                  </tr>
                  <tr>
                    <th className="px-5 py-3"></th>
                    {(data?.overall_stage_summary || []).flatMap((s) => [
                      <th key={`${s.activity_id ?? s.activity_name}-a`} className="px-3 py-2 text-right text-xs">Assigned</th>,
                      <th key={`${s.activity_id ?? s.activity_name}-m`} className="px-3 py-2 text-right text-xs">Moved</th>,
                    ])}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {(data?.agent_wise_summary || []).map((agent) => {
                    const colKey = (s) => s.activity_id ?? s.activity_name
                    const byKey = Object.fromEntries(agent.stage_summary.map((s) => [colKey(s), s]))
                    return (
                    <tr key={agent.fos_id} className="hover:bg-gray-50">
                      <td className="px-5 py-3">
                        <button onClick={() => drillDown(null, agent.fos_id)} className="text-blue-600 hover:underline font-medium">
                          {agent.fos_name}
                        </button>
                      </td>
                      {(data?.overall_stage_summary || []).flatMap((col) => {
                        const s = byKey[col.activity_id ?? col.activity_name]
                        return [
                          <td key={`${col.activity_id ?? col.activity_name}-a`} className="px-3 py-3 text-right">
                            {s ? s.total_assigned?.toLocaleString() : '—'}
                          </td>,
                          <td key={`${col.activity_id ?? col.activity_name}-m`} className="px-3 py-3 text-right">
                            {s ? s.moved_to_next?.toLocaleString() : '—'}
                          </td>,
                        ]
                      })}
                    </tr>
                  )})}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
        </>
      )}
    </div>
  )
}
