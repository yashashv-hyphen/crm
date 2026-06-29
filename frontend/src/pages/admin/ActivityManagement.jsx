import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors,
} from '@dnd-kit/core'
import {
  SortableContext, sortableKeyboardCoordinates, verticalListSortingStrategy,
  useSortable, arrayMove,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { listActivities, createActivity, reorderActivities, deleteActivity } from '../../api/activities'
import toast from 'react-hot-toast'

function SortableActivity({ activity, onDelete }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: activity.id })
  const style = { transform: CSS.Transform.toString(transform), transition }

  return (
    <div ref={setNodeRef} style={style} className="flex items-center gap-3 bg-white border border-gray-200 rounded-lg p-3 group">
      <span {...attributes} {...listeners} className="cursor-grab text-gray-400 hover:text-gray-600">⠿</span>
      <span className="text-xs text-gray-400 w-6 text-center">{activity.position_order}</span>
      <span className="flex-1 font-medium text-gray-800">{activity.name}</span>
      <span className="text-xs text-gray-400">{activity.sub_dispositions?.length || 0} sub-dispos</span>
      <button
        onClick={() => onDelete(activity.id)}
        className="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-700 text-xs px-2 py-0.5 border border-red-200 rounded"
      >
        Delete
      </button>
    </div>
  )
}

export default function ActivityManagement() {
  const qc = useQueryClient()
  const [newName, setNewName] = useState('')
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  const { data: activities = [], isLoading } = useQuery({
    queryKey: ['activities'],
    queryFn: () => listActivities().then((r) => r.data),
  })

  const [localActivities, setLocalActivities] = useState(null)
  const displayed = localActivities ?? activities

  const createMutation = useMutation({
    mutationFn: () => createActivity({ name: newName }),
    onSuccess: () => {
      toast.success('Activity created')
      qc.invalidateQueries(['activities'])
      setNewName('')
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Failed'),
  })

  const reorderMutation = useMutation({
    mutationFn: (items) => reorderActivities(items),
    onSuccess: () => qc.invalidateQueries(['activities']),
    onError: () => toast.error('Reorder failed'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => deleteActivity(id),
    onSuccess: () => { toast.success('Activity deleted'); qc.invalidateQueries(['activities']) },
    onError: (err) => toast.error(err.response?.data?.detail || 'Cannot delete'),
  })

  const handleDragEnd = ({ active, over }) => {
    if (!over || active.id === over.id) return
    const oldIndex = displayed.findIndex((a) => a.id === active.id)
    const newIndex = displayed.findIndex((a) => a.id === over.id)
    const reordered = arrayMove(displayed, oldIndex, newIndex).map((a, i) => ({ ...a, position_order: i + 1 }))
    setLocalActivities(reordered)
    reorderMutation.mutate(reordered.map((a) => ({ id: a.id, position_order: a.position_order })))
  }

  if (isLoading) return <div className="text-center py-12 text-gray-400">Loading...</div>

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-gray-800">Activity Management</h1>

      <div className="flex gap-2">
        <input
          placeholder="New activity name..."
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm flex-1 max-w-xs"
        />
        <button
          onClick={() => createMutation.mutate()}
          disabled={!newName.trim() || createMutation.isPending}
          className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
        >
          Add Activity
        </button>
      </div>

      <p className="text-xs text-gray-400">Drag to reorder — order determines lead movement sequence</p>

      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={displayed.map((a) => a.id)} strategy={verticalListSortingStrategy}>
          <div className="space-y-2">
            {displayed.map((activity) => (
              <SortableActivity
                key={activity.id}
                activity={activity}
                onDelete={(id) => deleteMutation.mutate(id)}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>
    </div>
  )
}
