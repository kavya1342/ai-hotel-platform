import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router'

import apiClient from '../api/client.js'
import { getCurrentUser } from '../api/auth.js'
import {
  assignGuestRequest,
  createGuestRequest,
  resolveGuestRequest,
  startGuestRequest,
} from '../api/guestRequests.js'

function GuestRequestsPage() {
  const navigate = useNavigate()

  const [currentUser, setCurrentUser] = useState(null)

  const [requests, setRequests] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  const [errorMessage, setErrorMessage] = useState('')
  const [actionMessage, setActionMessage] = useState('')

  const [processingRequestId, setProcessingRequestId] =
    useState(null)

  const [isCreating, setIsCreating] = useState(false)

  const [newRequest, setNewRequest] = useState({
    reservation_id: '',
    room_id: '',
    message: '',
  })

  // --------------------------------------------------
  // LOAD CURRENT USER
  // --------------------------------------------------

  useEffect(() => {
    async function loadCurrentUser() {
      try {
        const user = await getCurrentUser()
        setCurrentUser(user)
      } catch (error) {
        setErrorMessage(
          error.response?.data?.detail ??
            'Unable to load current user.',
        )
      }
    }

    loadCurrentUser()
  }, [])

  // --------------------------------------------------
  // LOAD GUEST REQUESTS
  // --------------------------------------------------

  const loadGuestRequests = useCallback(async () => {
    try {
      setErrorMessage('')

      const response = await apiClient.get('/guest-requests')

      setRequests(response.data)
    } catch (error) {
      setErrorMessage(
        error.response?.data?.detail ??
          'Unable to load guest requests.',
      )
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadGuestRequests()
  }, [loadGuestRequests])

  // --------------------------------------------------
  // CREATE GUEST REQUEST
  // --------------------------------------------------

  async function handleCreateRequest(event) {
    event.preventDefault()

    if (newRequest.message.trim().length < 3) {
      setErrorMessage(
        'Please enter a valid request message.',
      )
      return
    }

    try {
      setIsCreating(true)
      setErrorMessage('')
      setActionMessage('')

      const requestData = {
        reservation_id: newRequest.reservation_id
          ? Number(newRequest.reservation_id)
          : null,

        room_id: newRequest.room_id
          ? Number(newRequest.room_id)
          : null,

        message: newRequest.message.trim(),
      }

      await createGuestRequest(requestData)

      setActionMessage(
        'Guest request submitted successfully. AI classification has been applied.',
      )

      setNewRequest({
        reservation_id: '',
        room_id: '',
        message: '',
      })

      await loadGuestRequests()
    } catch (error) {
      setErrorMessage(
        error.response?.data?.detail ??
          'Unable to submit guest request.',
      )
    } finally {
      setIsCreating(false)
    }
  }

  // --------------------------------------------------
  // ASSIGN REQUEST
  // --------------------------------------------------

  async function handleAssign(requestId) {
    const staffId = window.prompt(
      'Enter the staff user ID:',
      '5',
    )

    if (!staffId) {
      return
    }

    const parsedStaffId = Number(staffId)

    if (
      !Number.isInteger(parsedStaffId) ||
      parsedStaffId <= 0
    ) {
      setErrorMessage(
        'Please enter a valid staff user ID.',
      )
      return
    }

    try {
      setProcessingRequestId(requestId)
      setErrorMessage('')
      setActionMessage('')

      await assignGuestRequest(
        requestId,
        parsedStaffId,
      )

      setActionMessage(
        `Request #${requestId} assigned successfully.`,
      )

      await loadGuestRequests()
    } catch (error) {
      setErrorMessage(
        error.response?.data?.detail ??
          'Unable to assign guest request.',
      )
    } finally {
      setProcessingRequestId(null)
    }
  }

  // --------------------------------------------------
  // START REQUEST
  // --------------------------------------------------

  async function handleStart(requestId) {
    try {
      setProcessingRequestId(requestId)
      setErrorMessage('')
      setActionMessage('')

      await startGuestRequest(requestId)

      setActionMessage(
        `Request #${requestId} started successfully.`,
      )

      await loadGuestRequests()
    } catch (error) {
      setErrorMessage(
        error.response?.data?.detail ??
          'Unable to start guest request.',
      )
    } finally {
      setProcessingRequestId(null)
    }
  }

  // --------------------------------------------------
  // RESOLVE REQUEST
  // --------------------------------------------------

  async function handleResolve(requestId) {
    const resolutionNotes = window.prompt(
      'Enter resolution notes:',
    )

    if (!resolutionNotes?.trim()) {
      return
    }

    try {
      setProcessingRequestId(requestId)
      setErrorMessage('')
      setActionMessage('')

      await resolveGuestRequest(
        requestId,
        resolutionNotes.trim(),
      )

      setActionMessage(
        `Request #${requestId} resolved successfully.`,
      )

      await loadGuestRequests()
    } catch (error) {
      setErrorMessage(
        error.response?.data?.detail ??
          'Unable to resolve guest request.',
      )
    } finally {
      setProcessingRequestId(null)
    }
  }

  const isGuest =
    currentUser?.role === 'GUEST'

  const canAssign =
    currentUser?.role === 'MANAGER' ||
    currentUser?.role === 'FRONT_DESK'

  // --------------------------------------------------
  // UI
  // --------------------------------------------------

  return (
    <div className="min-h-screen bg-slate-100">
      {/* HEADER */}

      <header className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-blue-600">
              AI Hotel Platform
            </p>

            <h1 className="mt-1 text-2xl font-bold text-slate-900">
              Guest Requests
            </h1>

            {currentUser && (
              <p className="mt-1 text-xs text-slate-500">
                Logged in as{' '}
                <span className="font-semibold">
                  {currentUser.full_name}
                </span>{' '}
                · {currentUser.role}
              </p>
            )}
          </div>

          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
          >
            Back to Dashboard
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8">

        {/* GUEST SUBMISSION FORM */}

        {isGuest && (
          <form
            onSubmit={handleCreateRequest}
            className="mb-8 rounded-2xl bg-white p-6 shadow-sm"
          >
            <div>
              <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
                Guest Service
              </p>

              <h2 className="mt-1 text-xl font-bold text-slate-900">
                Submit a Request
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Describe what you need. The AI system will
                automatically classify and prioritize your
                request.
              </p>
            </div>

            <div className="mt-5 grid gap-4 md:grid-cols-2">

              {/* RESERVATION ID */}

              <div>
                <label className="mb-1 block text-sm font-semibold text-slate-700">
                  Reservation ID
                </label>

                <input
                  type="number"
                  min="1"
                  value={newRequest.reservation_id}
                  onChange={(event) =>
                    setNewRequest({
                      ...newRequest,
                      reservation_id:
                        event.target.value,
                    })
                  }
                  placeholder="Optional"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-blue-500"
                />
              </div>

              {/* ROOM ID */}

              <div>
                <label className="mb-1 block text-sm font-semibold text-slate-700">
                  Room ID
                </label>

                <input
                  type="number"
                  min="1"
                  value={newRequest.room_id}
                  onChange={(event) =>
                    setNewRequest({
                      ...newRequest,
                      room_id:
                        event.target.value,
                    })
                  }
                  placeholder="Optional"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-blue-500"
                />
              </div>

              {/* MESSAGE */}

              <div className="md:col-span-2">
                <label className="mb-1 block text-sm font-semibold text-slate-700">
                  What can we help you with?
                </label>

                <textarea
                  required
                  minLength="3"
                  maxLength="2000"
                  rows="4"
                  value={newRequest.message}
                  onChange={(event) =>
                    setNewRequest({
                      ...newRequest,
                      message:
                        event.target.value,
                    })
                  }
                  placeholder="Example: The air conditioner is not cooling the room properly."
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isCreating}
              className="mt-6 rounded-lg bg-blue-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isCreating
                ? 'Submitting...'
                : 'Submit Request'}
            </button>
          </form>
        )}

        {/* PAGE TITLE */}

        <div className="mb-6">
          <h2 className="text-xl font-bold text-slate-900">
            {isGuest
              ? 'My Requests'
              : 'Guest Service Requests'}
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            {isGuest
              ? 'Track the progress of your hotel service requests.'
              : 'Monitor AI-classified guest requests, priorities and resolution status.'}
          </p>
        </div>

        {/* ERROR */}

        {errorMessage && (
          <div className="mb-6 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {errorMessage}
          </div>
        )}

        {/* SUCCESS */}

        {actionMessage && (
          <div className="mb-6 rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
            {actionMessage}
          </div>
        )}

        {/* REQUESTS */}

        {isLoading ? (
          <div className="rounded-2xl bg-white p-6 text-slate-500 shadow-sm">
            Loading guest requests...
          </div>
        ) : requests.length === 0 ? (
          <div className="rounded-2xl bg-white p-6 text-slate-500 shadow-sm">
            No guest requests found.
          </div>
        ) : (
          <div className="grid gap-5 lg:grid-cols-2">
            {requests.map((request) => {
              const isProcessing =
                processingRequestId === request.id

              const canWorkRequest =
                currentUser?.role === 'MANAGER' ||
                (
                  (
                    currentUser?.role ===
                      'FRONT_DESK' ||
                    currentUser?.role ===
                      'OPERATIONS'
                  ) &&
                  request.assigned_to ===
                    currentUser?.id
                )

              return (
                <article
                  key={request.id}
                  className="rounded-2xl bg-white p-6 shadow-sm"
                >
                  {/* HEADER */}

                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-blue-600">
                        Request #{request.id}
                      </p>

                      <h3 className="mt-2 text-lg font-bold text-slate-900">
                        {request.ai_summary ??
                          request.message}
                      </h3>
                    </div>

                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                      {request.status}
                    </span>
                  </div>

                  {/* AI CLASSIFICATION */}

                  <div className="mt-5 rounded-xl bg-blue-50 p-4">
                    <p className="text-xs font-semibold uppercase tracking-wider text-blue-600">
                      AI Classification
                    </p>

                    <div className="mt-3 flex flex-wrap gap-2">
                      <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700">
                        {request.category}
                      </span>

                      <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700">
                        {request.priority} priority
                      </span>
                    </div>
                  </div>

                  {/* DETAILS */}

                  <div className="mt-5 space-y-2 text-sm text-slate-600">
                    <p>
                      Original message:{' '}
                      <span className="text-slate-800">
                        {request.message}
                      </span>
                    </p>

                    <p>
                      Guest ID:{' '}
                      <span className="font-semibold text-slate-800">
                        {request.guest_id}
                      </span>
                    </p>

                    <p>
                      Room:{' '}
                      <span className="font-semibold text-slate-800">
                        {request.room_id ??
                          'Not linked'}
                      </span>
                    </p>

                    <p>
                      Reservation:{' '}
                      <span className="font-semibold text-slate-800">
                        {request.reservation_id ??
                          'Not linked'}
                      </span>
                    </p>

                    {!isGuest && (
                      <p>
                        Assigned staff:{' '}
                        <span className="font-semibold text-slate-800">
                          {request.assigned_to ??
                            'Unassigned'}
                        </span>
                      </p>
                    )}
                  </div>

                  {/* RESOLUTION */}

                  {request.resolution_notes && (
                    <div className="mt-5 rounded-lg bg-emerald-50 p-4">
                      <p className="text-xs font-semibold uppercase tracking-wider text-emerald-700">
                        Resolution
                      </p>

                      <p className="mt-2 text-sm text-emerald-900">
                        {request.resolution_notes}
                      </p>
                    </div>
                  )}

                  {/* ACTIONS */}

                  <div className="mt-6 flex flex-wrap gap-3">
                    {request.status ===
                      'SUBMITTED' &&
                      canAssign && (
                        <button
                          type="button"
                          disabled={isProcessing}
                          onClick={() =>
                            handleAssign(request.id)
                          }
                          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          Assign
                        </button>
                      )}

                    {request.status ===
                      'ACKNOWLEDGED' &&
                      canWorkRequest && (
                        <button
                          type="button"
                          disabled={isProcessing}
                          onClick={() =>
                            handleStart(request.id)
                          }
                          className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-amber-600 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          Start
                        </button>
                      )}

                    {request.status ===
                      'IN_PROGRESS' &&
                      canWorkRequest && (
                        <button
                          type="button"
                          disabled={isProcessing}
                          onClick={() =>
                            handleResolve(request.id)
                          }
                          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          Resolve
                        </button>
                      )}

                    {request.status ===
                      'RESOLVED' && (
                      <span className="rounded-lg bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-700">
                        Resolved
                      </span>
                    )}
                  </div>
                </article>
              )
            })}
          </div>
        )}
      </main>
    </div>
  )
}

export default GuestRequestsPage