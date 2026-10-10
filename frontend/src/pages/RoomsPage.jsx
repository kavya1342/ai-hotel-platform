import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router'

import apiClient from '../api/client.js'

function RoomsPage() {
  const navigate = useNavigate()

  const [rooms, setRooms] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    let isMounted = true

    async function loadRooms() {
      try {
        setErrorMessage('')

        const response = await apiClient.get('/rooms')

        if (isMounted) {
          setRooms(response.data)
        }
      } catch (error) {
        if (!isMounted) {
          return
        }

        if (error.response?.status === 401) {
          localStorage.removeItem('accessToken')
          navigate('/login', { replace: true })
        } else {
          setErrorMessage('Unable to load rooms.')
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    loadRooms()

    return () => {
      isMounted = false
    }
  }, [navigate])

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-blue-600">
              AI Hotel Platform
            </p>

            <h1 className="mt-1 text-2xl font-bold text-slate-900">
              Rooms
            </h1>
          </div>

          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
          >
            Back to Dashboard
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8">
        <div className="mb-6">
          <h2 className="text-xl font-bold text-slate-900">
            Room inventory
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            View current room availability and operational status.
          </p>
        </div>

        {errorMessage && (
          <div className="mb-6 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {errorMessage}
          </div>
        )}

        {isLoading ? (
          <div className="rounded-2xl bg-white p-6 text-slate-500 shadow-sm">
            Loading rooms...
          </div>
        ) : rooms.length === 0 ? (
          <div className="rounded-2xl bg-white p-6 text-slate-500 shadow-sm">
            No rooms found.
          </div>
        ) : (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {rooms.map((room) => (
              <article
                key={room.id}
                className="rounded-2xl bg-white p-6 shadow-sm"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-medium text-slate-500">
                      Room
                    </p>

                    <h3 className="mt-1 text-2xl font-bold text-slate-900">
                      {room.room_number}
                    </h3>
                  </div>

                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                    {room.status}
                  </span>
                </div>

                <div className="mt-6 space-y-2 text-sm text-slate-600">
                  <p>
                    Category ID:{' '}
                    <span className="font-medium text-slate-800">
                      {room.category_id}
                    </span>
                  </p>

                  <p>
                    Active:{' '}
                    <span className="font-medium text-slate-800">
                      {room.is_active ? 'Yes' : 'No'}
                    </span>
                  </p>
                </div>
              </article>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

export default RoomsPage