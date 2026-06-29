import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { listActivities } from '../api/activities'

export default function Activities() {
  const navigate = useNavigate()
  const [selectedActivity, setSelectedActivity] = useState(null)

  const { data: activities = [], isLoading } = useQuery({
    queryKey: ['activities'],
    queryFn: () => listActivities().then((r) => r.data),
  })

  const openLeads = (activityId) => {
    navigate(`/leads?activity_id=${activityId}`)
  }

  if (isLoading) return <div className="text-center py-12 text-gray-400">Loading activities...</div>

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-gray-800">My Activities</h1>
      {!activities.length ? (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-12 text-center text-gray-400">
          No leads assigned to you yet. Please contact your admin.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {activities.map((activity) => (
            <button
              key={activity.id}
              onClick={() => openLeads(activity.id)}
              className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 text-left hover:border-blue-300 hover:shadow-md transition-all group"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-gray-400 uppercase">Stage {activity.position_order}</span>
                <svg className="w-4 h-4 text-gray-400 group-hover:text-blue-500 transition" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
              <h3 className="font-semibold text-gray-800 group-hover:text-blue-700 transition">{activity.name}</h3>
              <p className="text-xs text-gray-400 mt-1">{activity.sub_dispositions?.length || 0} sub-dispositions</p>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
