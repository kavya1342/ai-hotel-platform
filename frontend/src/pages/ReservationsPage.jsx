import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router'

import apiClient from '../api/client.js'
import { getCurrentUser } from '../api/auth.js'

import {
  assignReservationRoom,
  cancelReservation,
  checkInReservation,
  checkOutReservation,
  createReservation,
} from '../api/reservations.js'

function getApiErrorMessage(error, fallbackMessage) {
  const detail = error.response?.data?.detail

  if (typeof detail === 'string') {
    return detail
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => item.msg)
      .filter(Boolean)
      .join(' ')
  }

  return fallbackMessage
}

function ReservationsPage() {
  const navigate = useNavigate()

  const [currentUser, setCurrentUser] = useState(null)

  const [reservations, setReservations] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  const [errorMessage, setErrorMessage] = useState('')
  const [actionMessage, setActionMessage] = useState('')

  const [processingReservationId, setProcessingReservationId] =
    useState(null)

  const [showCreateForm, setShowCreateForm] =
    useState(false)

  const [newReservation, setNewReservation] = useState({
    guest_id: '2',
    room_id: '',
    check_in_date: '',
    check_out_date: '',
    number_of_guests: '1',
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
          getApiErrorMessage(
            error,
            'Unable to load current user.',
          ),
        )
      }
    }

    loadCurrentUser()
  }, [])

  // --------------------------------------------------
  // LOAD RESERVATIONS
  // --------------------------------------------------

  const loadReservations = useCallback(async () => {
    try {
      setErrorMessage('')

      const response = await apiClient.get('/reservations')

      setReservations(response.data)
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          'Unable to load reservations.',
        ),
      )
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadReservations()
  }, [loadReservations])

  // --------------------------------------------------
  // ROLE HELPERS
  // --------------------------------------------------

  const role = currentUser?.role

  const isGuest = role === 'GUEST'

  const canManageReservations =
    role === 'MANAGER' ||
    role === 'FRONT_DESK'

  // --------------------------------------------------
  // CREATE RESERVATION
  // --------------------------------------------------

  async function handleCreateReservation(event) {
    event.preventDefault()

    if (!canManageReservations) {
      return
    }

    setErrorMessage('')
    setActionMessage('')

    if (!newReservation.check_in_date) {
      setErrorMessage('Check-in date is required.')
      return
    }

    if (!newReservation.check_out_date) {
      setErrorMessage('Check-out date is required.')
      return
    }

    if (
      newReservation.check_out_date <=
      newReservation.check_in_date
    ) {
      setErrorMessage(
        'Check-out date must be after check-in date.',
      )
      return
    }

    try {
      const reservationData = {
        guest_id: Number(newReservation.guest_id),

        room_id: newReservation.room_id
          ? Number(newReservation.room_id)
          : null,

        check_in_date:
          newReservation.check_in_date,

        check_out_date:
          newReservation.check_out_date,

        number_of_guests: Number(
          newReservation.number_of_guests,
        ),
      }

      await createReservation(reservationData)

      setActionMessage(
        'Reservation created successfully.',
      )

      setNewReservation({
        guest_id: '2',
        room_id: '',
        check_in_date: '',
        check_out_date: '',
        number_of_guests: '1',
      })

      setShowCreateForm(false)

      await loadReservations()
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          'Unable to create reservation.',
        ),
      )
    }
  }

  // --------------------------------------------------
  // ASSIGN ROOM
  // --------------------------------------------------

  async function handleAssignRoom(reservation) {
    if (!canManageReservations) {
      return
    }

    const roomId = window.prompt(
      'Enter the room ID:',
      reservation.room_id?.toString() ?? '1',
    )

    if (!roomId) {
      return
    }

    const parsedRoomId = Number(roomId)

    if (
      !Number.isInteger(parsedRoomId) ||
      parsedRoomId <= 0
    ) {
      setErrorMessage(
        'Please enter a valid room ID.',
      )
      return
    }

    try {
      setProcessingReservationId(reservation.id)
      setErrorMessage('')
      setActionMessage('')

      await assignReservationRoom(
        reservation.id,
        parsedRoomId,
      )

      setActionMessage(
        `Room assigned to reservation #${reservation.id}.`,
      )

      await loadReservations()
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          'Unable to assign room.',
        ),
      )
    } finally {
      setProcessingReservationId(null)
    }
  }

  // --------------------------------------------------
  // CHECK IN
  // --------------------------------------------------

  async function handleCheckIn(reservationId) {
    if (!canManageReservations) {
      return
    }

    const confirmed = window.confirm(
      `Check in reservation #${reservationId}?`,
    )

    if (!confirmed) {
      return
    }

    try {
      setProcessingReservationId(reservationId)
      setErrorMessage('')
      setActionMessage('')

      await checkInReservation(reservationId)

      setActionMessage(
        `Reservation #${reservationId} checked in successfully.`,
      )

      await loadReservations()
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          'Unable to check in reservation.',
        ),
      )
    } finally {
      setProcessingReservationId(null)
    }
  }

  // --------------------------------------------------
  // CHECK OUT
  // --------------------------------------------------

  async function handleCheckOut(reservationId) {
    if (!canManageReservations) {
      return
    }

    const confirmed = window.confirm(
      `Check out reservation #${reservationId}?`,
    )

    if (!confirmed) {
      return
    }

    try {
      setProcessingReservationId(reservationId)
      setErrorMessage('')
      setActionMessage('')

      await checkOutReservation(reservationId)

      setActionMessage(
        `Reservation #${reservationId} checked out successfully. A housekeeping task was created automatically.`,
      )

      await loadReservations()
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          'Unable to check out reservation.',
        ),
      )
    } finally {
      setProcessingReservationId(null)
    }
  }

  // --------------------------------------------------
  // CANCEL RESERVATION
  // --------------------------------------------------

  async function handleCancel(reservationId) {
    if (!canManageReservations) {
      return
    }

    const confirmed = window.confirm(
      `Cancel reservation #${reservationId}?`,
    )

    if (!confirmed) {
      return
    }

    try {
      setProcessingReservationId(reservationId)
      setErrorMessage('')
      setActionMessage('')

      await cancelReservation(reservationId)

      setActionMessage(
        `Reservation #${reservationId} cancelled successfully.`,
      )

      await loadReservations()
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          'Unable to cancel reservation.',
        ),
      )
    } finally {
      setProcessingReservationId(null)
    }
  }

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
              {isGuest
                ? 'My Reservations'
                : 'Reservations'}
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

      {/* MAIN */}

      <main className="mx-auto max-w-7xl px-6 py-8">

        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">

          <div>
            <h2 className="text-xl font-bold text-slate-900">
              {isGuest
                ? 'My Stays'
                : 'Reservation Management'}
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              {isGuest
                ? 'View your current and previous hotel reservations.'
                : 'Create bookings, assign rooms and manage guest check-in and check-out.'}
            </p>
          </div>

          {/* STAFF ONLY */}

          {canManageReservations && (
            <button
              type="button"
              onClick={() => {
                setShowCreateForm(
                  (currentValue) => !currentValue,
                )

                setErrorMessage('')
                setActionMessage('')
              }}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
            >
              {showCreateForm
                ? 'Cancel'
                : 'Create Reservation'}
            </button>
          )}

        </div>

        {/* CREATE FORM - STAFF ONLY */}

        {canManageReservations &&
          showCreateForm && (
            <form
              onSubmit={handleCreateReservation}
              className="mt-6 rounded-2xl bg-white p-6 shadow-sm"
            >

              <h3 className="text-lg font-bold text-slate-900">
                New Reservation
              </h3>

              <div className="mt-5 grid gap-4 md:grid-cols-2">

                {/* GUEST ID */}

                <div>
                  <label className="mb-1 block text-sm font-semibold text-slate-700">
                    Guest ID
                  </label>

                  <input
                    type="number"
                    min="1"
                    required
                    value={newReservation.guest_id}
                    onChange={(event) =>
                      setNewReservation({
                        ...newReservation,
                        guest_id:
                          event.target.value,
                      })
                    }
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
                    value={newReservation.room_id}
                    onChange={(event) =>
                      setNewReservation({
                        ...newReservation,
                        room_id:
                          event.target.value,
                      })
                    }
                    placeholder="Optional"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-blue-500"
                  />

                  <p className="mt-1 text-xs text-slate-500">
                    Leave empty to assign a room later.
                  </p>
                </div>

                {/* CHECK IN */}

                <div>
                  <label className="mb-1 block text-sm font-semibold text-slate-700">
                    Check-in Date
                  </label>

                  <input
                    type="date"
                    required
                    value={
                      newReservation.check_in_date
                    }
                    onChange={(event) =>
                      setNewReservation({
                        ...newReservation,
                        check_in_date:
                          event.target.value,
                      })
                    }
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-blue-500"
                  />
                </div>

                {/* CHECK OUT */}

                <div>
                  <label className="mb-1 block text-sm font-semibold text-slate-700">
                    Check-out Date
                  </label>

                  <input
                    type="date"
                    required
                    value={
                      newReservation.check_out_date
                    }
                    onChange={(event) =>
                      setNewReservation({
                        ...newReservation,
                        check_out_date:
                          event.target.value,
                      })
                    }
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-blue-500"
                  />
                </div>

                {/* NUMBER OF GUESTS */}

                <div>
                  <label className="mb-1 block text-sm font-semibold text-slate-700">
                    Number of Guests
                  </label>

                  <input
                    type="number"
                    min="1"
                    max="20"
                    required
                    value={
                      newReservation.number_of_guests
                    }
                    onChange={(event) =>
                      setNewReservation({
                        ...newReservation,
                        number_of_guests:
                          event.target.value,
                      })
                    }
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-blue-500"
                  />
                </div>

              </div>

              <button
                type="submit"
                className="mt-6 rounded-lg bg-emerald-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700"
              >
                Create Reservation
              </button>

            </form>
          )}

        {/* ERROR */}

        {errorMessage && (
          <div className="mt-6 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {errorMessage}
          </div>
        )}

        {/* SUCCESS */}

        {actionMessage && (
          <div className="mt-6 rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
            {actionMessage}
          </div>
        )}

        {/* RESERVATION LIST */}

        <div className="mt-8">

          {isLoading ? (
            <div className="rounded-2xl bg-white p-6 text-slate-500 shadow-sm">
              Loading reservations...
            </div>
          ) : reservations.length === 0 ? (
            <div className="rounded-2xl bg-white p-6 text-slate-500 shadow-sm">
              No reservations found.
            </div>
          ) : (
            <div className="overflow-hidden rounded-2xl bg-white shadow-sm">

              <div className="overflow-x-auto">

                <table className="min-w-full divide-y divide-slate-200">

                  <thead className="bg-slate-50">

                    <tr>

                      <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                        ID
                      </th>

                      {!isGuest && (
                        <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                          Guest
                        </th>
                      )}

                      <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                        Room
                      </th>

                      <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                        Check-in
                      </th>

                      <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                        Check-out
                      </th>

                      <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                        Guests
                      </th>

                      <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                        Status
                      </th>

                      {canManageReservations && (
                        <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                          Actions
                        </th>
                      )}

                    </tr>

                  </thead>

                  <tbody className="divide-y divide-slate-200">

                    {reservations.map(
                      (reservation) => {
                        const isProcessing =
                          processingReservationId ===
                          reservation.id

                        const canModify =
                          reservation.status ===
                            'PENDING' ||
                          reservation.status ===
                            'CONFIRMED'

                        return (
                          <tr
                            key={reservation.id}
                            className="transition hover:bg-slate-50"
                          >

                            <td className="whitespace-nowrap px-5 py-4 text-sm font-medium text-slate-900">
                              #{reservation.id}
                            </td>

                            {!isGuest && (
                              <td className="whitespace-nowrap px-5 py-4 text-sm text-slate-600">
                                Guest #
                                {reservation.guest_id}
                              </td>
                            )}

                            <td className="whitespace-nowrap px-5 py-4 text-sm text-slate-600">
                              {reservation.room_id
                                ? `Room #${reservation.room_id}`
                                : 'Not assigned'}
                            </td>

                            <td className="whitespace-nowrap px-5 py-4 text-sm text-slate-600">
                              {
                                reservation.check_in_date
                              }
                            </td>

                            <td className="whitespace-nowrap px-5 py-4 text-sm text-slate-600">
                              {
                                reservation.check_out_date
                              }
                            </td>

                            <td className="whitespace-nowrap px-5 py-4 text-sm text-slate-600">
                              {
                                reservation.number_of_guests
                              }
                            </td>

                            <td className="whitespace-nowrap px-5 py-4">
                              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                                {reservation.status}
                              </span>
                            </td>

                            {/* STAFF ACTIONS */}

                            {canManageReservations && (
                              <td className="px-5 py-4">

                                <div className="flex min-w-56 flex-wrap gap-2">

                                  {canModify && (
                                    <button
                                      type="button"
                                      disabled={
                                        isProcessing
                                      }
                                      onClick={() =>
                                        handleAssignRoom(
                                          reservation,
                                        )
                                      }
                                      className="rounded-lg bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700 transition hover:bg-blue-100 disabled:opacity-50"
                                    >
                                      {reservation.room_id
                                        ? 'Change Room'
                                        : 'Assign Room'}
                                    </button>
                                  )}

                                  {reservation.status ===
                                    'CONFIRMED' &&
                                    reservation.room_id && (
                                      <button
                                        type="button"
                                        disabled={
                                          isProcessing
                                        }
                                        onClick={() =>
                                          handleCheckIn(
                                            reservation.id,
                                          )
                                        }
                                        className="rounded-lg bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-700 transition hover:bg-amber-100 disabled:opacity-50"
                                      >
                                        Check In
                                      </button>
                                    )}

                                  {reservation.status ===
                                    'CHECKED_IN' && (
                                    <button
                                      type="button"
                                      disabled={
                                        isProcessing
                                      }
                                      onClick={() =>
                                        handleCheckOut(
                                          reservation.id,
                                        )
                                      }
                                      className="rounded-lg bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700 transition hover:bg-emerald-100 disabled:opacity-50"
                                    >
                                      Check Out
                                    </button>
                                  )}

                                  {canModify && (
                                    <button
                                      type="button"
                                      disabled={
                                        isProcessing
                                      }
                                      onClick={() =>
                                        handleCancel(
                                          reservation.id,
                                        )
                                      }
                                      className="rounded-lg bg-red-50 px-3 py-2 text-xs font-semibold text-red-700 transition hover:bg-red-100 disabled:opacity-50"
                                    >
                                      Cancel
                                    </button>
                                  )}

                                  {reservation.status ===
                                    'CHECKED_OUT' && (
                                    <span className="rounded-lg bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700">
                                      Completed
                                    </span>
                                  )}

                                  {reservation.status ===
                                    'CANCELLED' && (
                                    <span className="rounded-lg bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-500">
                                      Cancelled
                                    </span>
                                  )}

                                </div>

                              </td>
                            )}

                          </tr>
                        )
                      },
                    )}

                  </tbody>

                </table>

              </div>

            </div>
          )}

        </div>

      </main>
    </div>
  )
}

export default ReservationsPage