import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getFosDashboard } from '../api/dashboard'
import { createNewRegistration } from '../api/leads'
import { getPleMcidDetail } from '../api/ple'
import { useAuth } from '../context/AuthContext'
import PleMcidDrawer from '../components/PleMcidDrawer'
import toast from 'react-hot-toast'

const stageName = (name) => name?.replace(/ Pending$/i, '') ?? name

function PleTab() {
  const [selectedMcid, setSelectedMcid] = useState(null)
  const { data: mcidDetail, isLoading } = useQuery({
    queryKey: ['ple-mcid-detail'],
    queryFn: () => getPleMcidDetail().then((r) => r.data),
  })

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      {selectedMcid && <PleMcidDrawer mcid={selectedMcid} onClose={() => setSelectedMcid(null)} />}
      <div className="px-5 py-4 border-b border-gray-100">
        <h2 className="font-semibold text-gray-700">MCID-wise Breakdown</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
            <tr>
              <th className="px-5 py-3 text-left">MCID</th>
              <th className="px-3 py-3 text-left">Marketplace ID</th>
              <th className="px-3 py-3 text-left">FBA Status</th>
              <th className="px-3 py-3 text-left">SP Status</th>
              <th className="px-3 py-3 text-left">CP Adoption</th>
              <th className="px-3 py-3 text-left">Cross Launch</th>
              <th className="px-3 py-3 text-left">Cross Launch Final Stage</th>
              <th className="px-3 py-3 text-left">Launch Y/N</th>
              <th className="px-3 py-3 text-left">SP Y/N</th>
              <th className="px-3 py-3 text-left">Coupons Y/N</th>
              <th className="px-3 py-3 text-left">Launch Date</th>
              <th className="px-3 py-3 text-left">Launch Week</th>
              <th className="px-3 py-3 text-left">FBA Launch Date</th>
              <th className="px-3 py-3 text-left">FBA Launch Week</th>
              <th className="px-3 py-3 text-left">SP Launch Date</th>
              <th className="px-3 py-3 text-left">SP Launch Week</th>
              <th className="px-3 py-3 text-right">SP Spend</th>
              <th className="px-3 py-3 text-left">CP Launch Date</th>
              <th className="px-3 py-3 text-left">Coupon Launch Week</th>
              <th className="px-3 py-3 text-left">CL</th>
              <th className="px-3 py-3 text-right">Total Live Selection</th>
              <th className="px-3 py-3 text-right">FBA Live Selection</th>
              <th className="px-3 py-3 text-right">Buyable ASIN</th>
              <th className="px-3 py-3 text-right">Total GMS</th>
              <th className="px-3 py-3 text-right">FBA GMS</th>
              <th className="px-3 py-3 text-right">SWAS</th>
              <th className="px-3 py-3 text-right">FBA SWAS</th>
              <th className="px-3 py-3 text-right">FBA Intransit</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {isLoading ? (
              <tr><td colSpan={28} className="px-5 py-6 text-center text-gray-400">Loading...</td></tr>
            ) : !mcidDetail?.length ? (
              <tr><td colSpan={28} className="px-5 py-6 text-center text-gray-400">No PLE data for your MCIDs yet</td></tr>
            ) : (
              mcidDetail.map((row) => (
                <tr key={row.mcid} className="hover:bg-gray-50 cursor-pointer" onClick={() => setSelectedMcid(row.mcid)}>
                  <td className="px-5 py-3 font-mono text-blue-600 hover:underline">{row.mcid}</td>
                  <td className="px-3 py-3">{row.marketplace_id || '—'}</td>
                  <td className="px-3 py-3">{row.fba_status || '—'}</td>
                  <td className="px-3 py-3">{row.sp_status || '—'}</td>
                  <td className="px-3 py-3">{row.cp_adoption || '—'}</td>
                  <td className="px-3 py-3">{row.narf_cross_launch || '—'}</td>
                  <td className="px-3 py-3">{row.cross_launch_final_stage || '—'}</td>
                  <td className="px-3 py-3">{row.launch_yn || '—'}</td>
                  <td className="px-3 py-3">{row.sp_yn || '—'}</td>
                  <td className="px-3 py-3">{row.coupons_yn || '—'}</td>
                  <td className="px-3 py-3">{row.launch_date || '—'}</td>
                  <td className="px-3 py-3">{row.launch_week || '—'}</td>
                  <td className="px-3 py-3">{row.fba_launch_date || '—'}</td>
                  <td className="px-3 py-3">{row.fba_launch_week || '—'}</td>
                  <td className="px-3 py-3">{row.sp_launch_date || '—'}</td>
                  <td className="px-3 py-3">{row.sp_launch_week || '—'}</td>
                  <td className="px-3 py-3 text-right">{row.sp_spend?.toLocaleString() ?? '—'}</td>
                  <td className="px-3 py-3">{row.cp_launch_date || '—'}</td>
                  <td className="px-3 py-3">{row.coupon_launch_week || '—'}</td>
                  <td className="px-3 py-3">{row.cl_status || '—'}</td>
                  <td className="px-3 py-3 text-right">{row.total_live_selection?.toLocaleString() ?? '—'}</td>
                  <td className="px-3 py-3 text-right">{row.fba_live_selection_wf?.toLocaleString() ?? '—'}</td>
                  <td className="px-3 py-3 text-right">{row.buyable_asin?.toLocaleString() ?? '—'}</td>
                  <td className="px-3 py-3 text-right">{row.total_gms?.toLocaleString() ?? '—'}</td>
                  <td className="px-3 py-3 text-right">{row.fba_gms?.toLocaleString() ?? '—'}</td>
                  <td className="px-3 py-3 text-right">{row.swas?.toLocaleString() ?? '—'}</td>
                  <td className="px-3 py-3 text-right">{row.fba_swas?.toLocaleString() ?? '—'}</td>
                  <td className="px-3 py-3 text-right">{row.fba_intransit?.toLocaleString() ?? '—'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function ClickableNumber({ value, onClick }) {
  return (
    <button onClick={onClick} className="text-blue-600 hover:underline font-semibold">
      {value?.toLocaleString()}
    </button>
  )
}

function NewRegistrationModal({ onClose, onSuccess }) {
  const [form, setForm] = useState({ mobile_number: '', email_id: '', seller_name: '' })
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.mobile_number.trim()) { toast.error('Mobile number is required'); return }
    try {
      setSaving(true)
      await createNewRegistration(form)
      toast.success('New registration saved')
      onSuccess()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save registration')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 p-6 space-y-5">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-800">New Registration</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Seller Name</label>
            <input
              type="text"
              value={form.seller_name}
              onChange={(e) => setForm((f) => ({ ...f, seller_name: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter seller name"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Mobile Number <span className="text-red-500">*</span></label>
            <input
              type="tel"
              value={form.mobile_number}
              onChange={(e) => setForm((f) => ({ ...f, mobile_number: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter mobile number"
              required
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Email ID</label>
            <input
              type="email"
              value={form.email_id}
              onChange={(e) => setForm((f) => ({ ...f, email_id: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter email address"
            />
          </div>
          <div className="flex gap-3 pt-1">
            <button type="button" onClick={onClose}
              className="flex-1 border border-gray-300 text-gray-700 rounded-lg py-2 text-sm hover:bg-gray-50">
              Cancel
            </button>
            <button type="submit" disabled={saving}
              className="flex-1 bg-blue-600 text-white rounded-lg py-2 text-sm hover:bg-blue-700 disabled:opacity-50">
              {saving ? 'Saving...' : 'Save Registration'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function FosDashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [activeTab, setActiveTab] = useState('stages')

  const { data, isLoading } = useQuery({
    queryKey: ['fos-dashboard'],
    queryFn: () => getFosDashboard().then((r) => r.data),
    refetchInterval: 30_000,
  })

  const goToLeads = (activityId, status, stageName) => {
    const params = new URLSearchParams()
    if (activityId) params.set('activity_id', activityId)
    if (stageName) params.set('current_stage', stageName)
    if (status === 'moved') params.set('has_final_stage', 'true')
    if (status === 'pending') params.set('has_final_stage', 'false')
    navigate(`/leads?${params}`)
  }

  if (isLoading) return <div className="text-center py-12 text-gray-400">Loading...</div>

  const followUpCount = data?.follow_up_today_count || 0

  return (
    <div className="space-y-6">
      {showModal && (
        <NewRegistrationModal
          onClose={() => setShowModal(false)}
          onSuccess={() => {
            setShowModal(false)
            queryClient.invalidateQueries(['fos-dashboard'])
          }}
        />
      )}

      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-800">Welcome, {user?.full_name}</h1>
        {followUpCount > 0 && (
          <button
            onClick={() => navigate('/follow-ups')}
            className="flex items-center gap-2 bg-red-50 text-red-700 border border-red-200 rounded-lg px-4 py-2 text-sm font-medium hover:bg-red-100"
          >
            🔴 {followUpCount} follow-up{followUpCount !== 1 ? 's' : ''} due today
          </button>
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
      {/* Stage Summary Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-700">Stage Summary</h2>
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
            {(data?.stage_summary || []).map((row) => (
              <tr key={row.activity_id ?? row.activity_name} className="hover:bg-gray-50">
                <td className="px-5 py-3 font-medium text-gray-800">
                  {stageName(row.activity_name)}
                  {!row.activity_id && (
                    <span className="ml-1.5 text-[10px] bg-green-100 text-green-700 font-semibold px-1.5 py-0.5 rounded">Self</span>
                  )}
                </td>
                <td className="px-5 py-3 text-right">
                  <ClickableNumber value={row.total_assigned} onClick={() => goToLeads(row.activity_id, 'all', !row.activity_id ? row.activity_name : null)} />
                </td>
                <td className="px-5 py-3 text-right">
                  <ClickableNumber value={row.moved_to_next} onClick={() => goToLeads(row.activity_id, 'moved', !row.activity_id ? row.activity_name : null)} />
                </td>
                <td className="px-5 py-3 text-right">
                  <ClickableNumber value={row.pending} onClick={() => goToLeads(row.activity_id, 'pending', !row.activity_id ? row.activity_name : null)} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Disposition Summary */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-700">Disposition Summary</h2>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
            <tr>
              <th className="px-5 py-3 text-left">Sub-Disposition</th>
              <th className="px-5 py-3 text-right">This Week</th>
              <th className="px-5 py-3 text-right">YTD</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {(data?.disposition_summary || []).map((row, i) => (
              <tr key={i} className="hover:bg-gray-50">
                <td className="px-5 py-3 text-gray-700">{row.sub_disposition}</td>
                <td className="px-5 py-3 text-right text-gray-700">{row.this_week?.toLocaleString()}</td>
                <td className="px-5 py-3 text-right text-gray-700">{row.ytd?.toLocaleString()}</td>
              </tr>
            ))}
            {!data?.disposition_summary?.length && (
              <tr><td colSpan={3} className="px-5 py-4 text-center text-gray-400">No disposition data yet</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <button
        onClick={() => setShowModal(true)}
        className="w-full bg-green-600 text-white rounded-xl py-3 text-sm font-medium hover:bg-green-700"
      >
        + New Registration
      </button>
        </>
      )}
    </div>
  )
}
