import { useQuery } from '@tanstack/react-query'
import { getFollowUps } from '../api/leads'
import FollowUpBadge from '../components/FollowUpBadge'

export default function FollowUps() {
  const { data, isLoading } = useQuery({
    queryKey: ['follow-ups'],
    queryFn: () => getFollowUps().then((r) => r.data),
  })

  if (isLoading) return <div className="text-center py-12 text-gray-400">Loading follow-ups...</div>

  const leads = data?.items || data || []

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-gray-800">My Follow-ups</h1>
      {!leads.length ? (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-12 text-center text-gray-400">
          No follow-ups set. Open a lead and set a follow-up date.
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
              <tr>
                <th className="px-5 py-3 text-left">Seller / MID</th>
                <th className="px-5 py-3 text-left">Stage</th>
                <th className="px-5 py-3 text-left">Follow-up Date</th>
                <th className="px-5 py-3 text-left">Remark</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {leads.map((lead) => (
                <tr key={lead.id} className="hover:bg-gray-50">
                  <td className="px-5 py-3">
                    <div className="font-medium">{lead.seller_name}</div>
                    <div className="text-xs text-gray-400 font-mono">{lead.merchant_id}</div>
                  </td>
                  <td className="px-5 py-3 text-gray-600">{lead.stage_assigned}</td>
                  <td className="px-5 py-3">
                    <FollowUpBadge date={lead.follow_up_date} status={lead.follow_up_status} />
                  </td>
                  <td className="px-5 py-3 text-gray-600 max-w-xs truncate">{lead.remark || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
