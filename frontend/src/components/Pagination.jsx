export default function Pagination({ page, pages, total, size, onChange }) {
  if (pages <= 1) return null
  return (
    <div className="flex items-center justify-between mt-4 text-sm text-gray-600">
      <span>
        Showing {(page - 1) * size + 1}–{Math.min(page * size, total)} of {total} leads
      </span>
      <div className="flex gap-1">
        <button
          disabled={page === 1}
          onClick={() => onChange(page - 1)}
          className="px-3 py-1 rounded border border-gray-300 disabled:opacity-40 hover:bg-gray-100"
        >
          Prev
        </button>
        {Array.from({ length: Math.min(5, pages) }, (_, i) => {
          const p = Math.max(1, Math.min(pages - 4, page - 2)) + i
          return (
            <button
              key={p}
              onClick={() => onChange(p)}
              className={`px-3 py-1 rounded border ${p === page ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-300 hover:bg-gray-100'}`}
            >
              {p}
            </button>
          )
        })}
        <button
          disabled={page === pages}
          onClick={() => onChange(page + 1)}
          className="px-3 py-1 rounded border border-gray-300 disabled:opacity-40 hover:bg-gray-100"
        >
          Next
        </button>
      </div>
    </div>
  )
}
