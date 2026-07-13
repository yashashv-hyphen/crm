import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getPleMcidDetail, getPleMcidHistory, updatePleMcid } from '../api/ple'
import toast from 'react-hot-toast'

function DetailRow({ label, value }) {
  if (!value && value !== 0) return null
  return (
    <div className="flex gap-2 py-1.5 border-b border-gray-50 last:border-0">
      <span className="text-xs text-gray-500 w-40 shrink-0">{label}</span>
      <span className="text-xs text-gray-800 font-medium break-all">{value}</span>
    </div>
  )
}

const PENDING_CHECKS = [
  { label: 'FBA Status', field: 'fba_status' },
  { label: 'SP Status', field: 'sp_status' },
  { label: 'CL Status', field: 'cl_status' },
  { label: 'CP Adoption', field: 'cp_adoption' },
  { label: 'Cross Launch', field: 'narf_cross_launch' },
  { label: 'Cross Launch Final Stage', field: 'cross_launch_final_stage' },
  { label: 'Launch Y/N', field: 'launch_yn' },
  { label: 'SP Y/N', field: 'sp_yn' },
  { label: 'Coupons Y/N', field: 'coupons_yn' },
  { label: 'Launch Date', field: 'launch_date' },
  { label: 'FBA Launch Date', field: 'fba_launch_date' },
  { label: 'SP Launch Date', field: 'sp_launch_date' },
  { label: 'CP Launch Date', field: 'cp_launch_date' },
]

function PendingChecklist({ record }) {
  return (
    <div className="grid grid-cols-1 gap-1 mb-4 bg-gray-50 rounded-lg p-3">
      {PENDING_CHECKS.map(({ label, field }) => {
        const done = !!record[field]
        return (
          <div key={field} className="flex items-center gap-2 text-xs">
            <span className={done ? 'text-green-600' : 'text-red-500'}>{done ? '✔' : '✖'}</span>
            <span className="text-gray-700">{label}</span>
          </div>
        )
      })}
    </div>
  )
}

function HistoryTab({ mcid }) {
  const { data: history, isLoading } = useQuery({
    queryKey: ['ple-mcid-history', mcid],
    queryFn: () => getPleMcidHistory(mcid).then((r) => r.data),
  })

  if (isLoading) return <p className="text-sm text-gray-400 py-4 text-center">Loading history…</p>
  if (!history?.length) return <p className="text-sm text-gray-400 py-4 text-center">No changes recorded yet.</p>

  return (
    <div className="space-y-2 mt-2">
      {history.map((entry, i) => (
        <div key={i} className="bg-gray-50 rounded-lg px-3 py-2 text-xs">
          <div className="flex items-center justify-between mb-1">
            <span className="font-semibold text-gray-700">{entry.field_name}</span>
            <span className="text-gray-400">{new Date(entry.performed_at).toLocaleString()}</span>
          </div>
          <div className="text-gray-500">
            {entry.performed_by_name && <span className="font-medium text-gray-600">{entry.performed_by_name} · </span>}
            {entry.old_value != null && (
              <span><span className="line-through text-red-400">{entry.old_value}</span> → </span>
            )}
            <span className="text-green-700 font-medium">{entry.new_value ?? '—'}</span>
          </div>
        </div>
      ))}
    </div>
  )
}

const EDITABLE_STATUS_FIELDS = [
  { label: 'FBA Status', field: 'fba_status' },
  { label: 'SP Status', field: 'sp_status' },
  { label: 'CL Status', field: 'cl_status' },
  { label: 'CP Adoption', field: 'cp_adoption' },
  { label: 'Cross Launch', field: 'narf_cross_launch' },
  { label: 'Cross Launch Final Stage', field: 'cross_launch_final_stage' },
  { label: 'Launch Y/N', field: 'launch_yn' },
  { label: 'SP Y/N', field: 'sp_yn' },
  { label: 'Coupons Y/N', field: 'coupons_yn' },
]

const EDITABLE_DATE_FIELDS = [
  { label: 'Launch Date', field: 'launch_date' },
  { label: 'FBA Launch Date', field: 'fba_launch_date' },
  { label: 'SP Launch Date', field: 'sp_launch_date' },
  { label: 'CP Launch Date', field: 'cp_launch_date' },
]

export default function PleMcidDrawer({ mcid, onClose }) {
  const [tab, setTab] = useState('details')
  const [form, setForm] = useState({})
  const queryClient = useQueryClient()

  const { data: records } = useQuery({
    queryKey: ['ple-mcid-record', mcid],
    queryFn: () => getPleMcidDetail({}).then((r) => r.data),
  })
  const record = records?.find((r) => r.mcid === mcid)

  useEffect(() => {
    if (record) {
      const next = {}
      for (const { field } of [...EDITABLE_STATUS_FIELDS, ...EDITABLE_DATE_FIELDS]) {
        next[field] = record[field] || ''
      }
      setForm(next)
    }
  }, [record?.mcid])

  const mutation = useMutation({
    mutationFn: (updates) => updatePleMcid(mcid, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ple-mcid-record', mcid] })
      queryClient.invalidateQueries({ queryKey: ['ple-mcid-history', mcid] })
      queryClient.invalidateQueries({ queryKey: ['ple-mcid-detail'] })
      queryClient.invalidateQueries({ queryKey: ['ple-agent-summary'] })
      toast.success('Saved')
    },
    onError: () => toast.error('Save failed'),
  })

  const handleSave = () => {
    if (!record) return
    const updates = {}
    for (const { field } of [...EDITABLE_STATUS_FIELDS, ...EDITABLE_DATE_FIELDS]) {
      if ((form[field] || '') !== (record[field] || '')) updates[field] = form[field] || null
    }
    if (!Object.keys(updates).length) { toast('No changes to save', { icon: 'ℹ️' }); return }
    mutation.mutate(updates)
  }

  if (!record) {
    return (
      <div className="fixed inset-0 z-50 flex">
        <div className="flex-1 bg-black/30" onClick={onClose} />
        <div className="w-full max-w-lg bg-white shadow-2xl flex items-center justify-center h-full">
          <span className="text-gray-400 text-sm">Loading…</span>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="flex-1 bg-black/30" onClick={onClose} />
      <div className="w-full max-w-lg bg-white shadow-2xl flex flex-col h-full overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 shrink-0">
          <div>
            <p className="text-xs text-gray-500">MCID</p>
            <p className="font-mono text-sm font-bold text-gray-800">{record.mcid}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
        </div>

        <div className="flex border-b border-gray-100 shrink-0">
          {['details', 'update', 'history'].map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-5 py-2.5 text-sm font-medium capitalize transition-colors ${
                tab === t ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {tab === 'details' && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Pending Checklist</p>
              <PendingChecklist record={record} />

              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Identity</p>
              <DetailRow label="Agent" value={record.agent_name} />
              <DetailRow label="Marketplace ID" value={record.marketplace_id} />

              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mt-3 mb-1">Status Fields</p>
              <DetailRow label="FBA Status" value={record.fba_status} />
              <DetailRow label="SP Status" value={record.sp_status} />
              <DetailRow label="CL Status" value={record.cl_status} />
              <DetailRow label="CP Adoption" value={record.cp_adoption} />
              <DetailRow label="Cross Launch" value={record.narf_cross_launch} />
              <DetailRow label="Cross Launch Final Stage" value={record.cross_launch_final_stage} />
              <DetailRow label="Launch Y/N" value={record.launch_yn} />
              <DetailRow label="SP Y/N" value={record.sp_yn} />
              <DetailRow label="Coupons Y/N" value={record.coupons_yn} />

              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mt-3 mb-1">Dates</p>
              <DetailRow label="Launch Date" value={record.launch_date} />
              <DetailRow label="Launch Week" value={record.launch_week} />
              <DetailRow label="FBA Launch Date" value={record.fba_launch_date} />
              <DetailRow label="FBA Launch Week" value={record.fba_launch_week} />
              <DetailRow label="SP Launch Date" value={record.sp_launch_date} />
              <DetailRow label="SP Launch Week" value={record.sp_launch_week} />
              <DetailRow label="CP Launch Date" value={record.cp_launch_date} />
              <DetailRow label="Coupon Launch Week" value={record.coupon_launch_week} />

              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mt-3 mb-1">Metrics</p>
              <DetailRow label="SP Spend" value={record.sp_spend?.toLocaleString()} />
              <DetailRow label="Total Live Selection" value={record.total_live_selection?.toLocaleString()} />
              <DetailRow label="FBA Live Selection" value={record.fba_live_selection?.toLocaleString()} />
              <DetailRow label="FBA Live Selection (WF)" value={record.fba_live_selection_wf?.toLocaleString()} />
              <DetailRow label="Buyable ASIN" value={record.buyable_asin?.toLocaleString()} />
              <DetailRow label="Total GMS" value={record.total_gms?.toLocaleString()} />
              <DetailRow label="FBA GMS" value={record.fba_gms?.toLocaleString()} />
              <DetailRow label="SWAS" value={record.swas?.toLocaleString()} />
              <DetailRow label="FBA SWAS" value={record.fba_swas?.toLocaleString()} />
              <DetailRow label="FBA Intransit" value={record.fba_intransit?.toLocaleString()} />
            </div>
          )}

          {tab === 'update' && (
            <div className="space-y-4">
              {EDITABLE_STATUS_FIELDS.map(({ label, field }) => (
                <div key={field}>
                  <label className="block text-xs text-gray-500 mb-1">{label}</label>
                  <input
                    type="text"
                    value={form[field] || ''}
                    onChange={(e) => setForm((f) => ({ ...f, [field]: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              ))}
              {EDITABLE_DATE_FIELDS.map(({ label, field }) => (
                <div key={field}>
                  <label className="block text-xs text-gray-500 mb-1">{label}</label>
                  <input
                    type="date"
                    value={form[field] || ''}
                    onChange={(e) => setForm((f) => ({ ...f, [field]: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              ))}
              <button
                onClick={handleSave}
                disabled={mutation.isPending}
                className="w-full bg-blue-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {mutation.isPending ? 'Saving…' : 'Save Changes'}
              </button>
            </div>
          )}

          {tab === 'history' && <HistoryTab mcid={mcid} />}
        </div>
      </div>
    </div>
  )
}
