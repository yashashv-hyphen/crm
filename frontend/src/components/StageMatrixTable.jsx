export function ClickableNumber({ value, onClick }) {
  if (value === null || value === undefined) {
    return <span className="text-gray-400">—</span>
  }
  return (
    <button onClick={onClick} className="text-blue-600 hover:underline font-semibold">
      {value.toLocaleString()}
    </button>
  )
}

export default function StageMatrixTable({ title, matrix, onCellClick }) {
  const stages = matrix?.stages || []
  const rows = matrix?.rows || []

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-100">
        <h2 className="font-semibold text-gray-700">{title}</h2>
        <p className="text-xs text-gray-400 mt-0.5">Rows: stage originally assigned · Columns: stage currently at</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
            <tr>
              <th className="px-5 py-3 text-left">Assigned \ Current</th>
              {stages.map((s) => (
                <th key={s} className="px-3 py-3 text-right">{s}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {rows.map((row) => (
              <tr key={row.assigned_stage} className="hover:bg-gray-50">
                <td className="px-5 py-3 font-medium text-gray-800">{row.assigned_stage}</td>
                {stages.map((s) => (
                  <td key={s} className="px-3 py-3 text-right">
                    <ClickableNumber
                      value={row.cells?.[s] ?? 0}
                      onClick={() => onCellClick?.(row.assigned_stage, s)}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
