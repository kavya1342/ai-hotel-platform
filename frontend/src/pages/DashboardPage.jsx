import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router'

import { getCurrentUser } from '../api/auth.js'
import { getDashboardData } from '../api/dashboard.js'
import { getOccupancyForecast } from '../api/occupancyForecast.js'


function DashboardPage() {
  const navigate = useNavigate()

  const [currentUser, setCurrentUser] = useState(null)

  const [dashboardData, setDashboardData] = useState({
    rooms: [],
    reservations: [],
    tasks: [],
    guestRequests: [],
  })

  const [occupancyForecast, setOccupancyForecast] = useState(null)
  const [forecastError, setForecastError] = useState('')

  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState('')

  // --------------------------------------------------
  // LOAD USER + ROLE-SPECIFIC DASHBOARD DATA
  // --------------------------------------------------

  useEffect(() => {
    async function loadDashboard() {
      try {
        setIsLoading(true)
        setErrorMessage('')
        setForecastError('')

        const user = await getCurrentUser()

        setCurrentUser(user)

        const data = await getDashboardData(user.role)

        setDashboardData(data)

        // Load the ML forecast separately so that a forecast
        // failure does not break the entire dashboard.
        if (user.role === 'MANAGER') {
          try {
            const forecast = await getOccupancyForecast()
            setOccupancyForecast(forecast)
          } catch (forecastRequestError) {
            console.error(
              'Unable to load occupancy forecast:',
              forecastRequestError,
            )

            setForecastError(
              forecastRequestError.response?.data?.detail ??
                'Occupancy forecast is temporarily unavailable.',
            )
          }
        }
      } catch (error) {
        if (error.response?.status === 401) {
          localStorage.removeItem('accessToken')
          navigate('/login', { replace: true })
          return
        }

        setErrorMessage(
          error.response?.data?.detail ??
            'Unable to load dashboard data.',
        )
      } finally {
        setIsLoading(false)
      }
    }

    loadDashboard()
  }, [navigate])

  // --------------------------------------------------
  // LOGOUT
  // --------------------------------------------------

  function handleSignOut() {
    localStorage.removeItem('accessToken')
    navigate('/login', { replace: true })
  }

  // --------------------------------------------------
  // DASHBOARD COUNTS
  // --------------------------------------------------

  const availableRooms = dashboardData.rooms.filter(
    (room) => room.status === 'AVAILABLE',
  ).length

  const activeReservations =
    dashboardData.reservations.filter(
      (reservation) =>
        reservation.status === 'CONFIRMED' ||
        reservation.status === 'CHECKED_IN' ||
        reservation.status === 'PENDING',
    ).length

  const pendingTasks = dashboardData.tasks.filter(
    (task) =>
      task.status !== 'COMPLETED' &&
      task.status !== 'CANCELLED',
  ).length

  const unresolvedRequests =
    dashboardData.guestRequests.filter(
      (request) =>
        request.status !== 'RESOLVED' &&
        request.status !== 'CANCELLED',
    ).length

  const resolvedRequests =
    dashboardData.guestRequests.filter(
      (request) => request.status === 'RESOLVED',
    ).length

  // --------------------------------------------------
  // ROLE HELPERS
  // --------------------------------------------------

  const role = currentUser?.role

  const isManager = role === 'MANAGER'
  const isFrontDesk = role === 'FRONT_DESK'
  const isOperations = role === 'OPERATIONS'
  const isGuest = role === 'GUEST'

  // --------------------------------------------------
  // SUMMARY CARDS
  // --------------------------------------------------

  let summaryCards = []

  if (isGuest) {
    summaryCards = [
      {
        title: 'Active Reservations',
        value: activeReservations,
        description: 'Your current or upcoming stays',
      },
      {
        title: 'Open Requests',
        value: unresolvedRequests,
        description: 'Requests waiting for completion',
      },
      {
        title: 'Resolved Requests',
        value: resolvedRequests,
        description: 'Completed guest-service requests',
      },
    ]
  } else if (isOperations) {
    summaryCards = [
      {
        title: 'Available Rooms',
        value: availableRooms,
        description: 'Rooms currently ready for guests',
      },
      {
        title: 'Active Tasks',
        value: pendingTasks,
        description: 'Operational tasks requiring work',
      },
      {
        title: 'Guest Requests',
        value: unresolvedRequests,
        description: 'Assigned requests still open',
      },
    ]
  } else {
    summaryCards = [
      {
        title: 'Available Rooms',
        value: availableRooms,
        description: 'Rooms ready for guests',
      },
      {
        title: 'Active Reservations',
        value: activeReservations,
        description: 'Current and upcoming bookings',
      },
      {
        title: 'Pending Tasks',
        value: pendingTasks,
        description: 'Operational work still active',
      },
      {
        title: 'Guest Requests',
        value: unresolvedRequests,
        description: 'Guest requests still unresolved',
      },
    ]
  }

  // --------------------------------------------------
  // UI
  // --------------------------------------------------

  return (
    <div className="min-h-screen bg-slate-100">
      {/* HEADER */}

      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-blue-600">
              AI Hotel Platform
            </p>

            <h1 className="mt-1 text-2xl font-bold text-slate-900">
              Dashboard
            </h1>
          </div>

          <div className="flex items-center gap-4">
            {currentUser && (
              <div className="hidden text-right sm:block">
                <p className="text-sm font-semibold text-slate-900">
                  {currentUser.full_name}
                </p>

                <p className="text-xs font-medium text-slate-500">
                  {currentUser.role}
                </p>
              </div>
            )}

            <button
              type="button"
              onClick={handleSignOut}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* MAIN */}

      <main className="mx-auto max-w-7xl px-6 py-8">
        {isLoading ? (
          <div className="rounded-2xl bg-white p-6 text-slate-500 shadow-sm">
            Loading dashboard...
          </div>
        ) : errorMessage ? (
          <div className="rounded-xl bg-red-50 px-5 py-4 text-sm text-red-700">
            {errorMessage}
          </div>
        ) : (
          <>
            {/* WELCOME */}

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-slate-900">
                Welcome
                {currentUser?.full_name
                  ? `, ${currentUser.full_name}`
                  : ''}
              </h2>

              <p className="mt-2 text-sm text-slate-500">
                {isGuest
                  ? 'Manage your stay and request hotel services.'
                  : isOperations
                    ? 'Manage assigned hotel operations and guest-service work.'
                    : 'Monitor reservations, rooms, operations and guest experience.'}
              </p>
            </section>

            {/* SUMMARY CARDS */}

            <section className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
              {summaryCards.map((card) => (
                <article
                  key={card.title}
                  className="rounded-2xl bg-white p-6 shadow-sm"
                >
                  <p className="text-sm font-semibold text-slate-500">
                    {card.title}
                  </p>

                  <p className="mt-3 text-3xl font-bold text-slate-900">
                    {card.value}
                  </p>

                  <p className="mt-2 text-xs text-slate-500">
                    {card.description}
                  </p>
                </article>
              ))}
            </section>

            {/* MANAGER ML FORECAST */}

            {isManager && (
              <section className="mt-8">
                <div className="rounded-2xl bg-white p-6 shadow-sm">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-widest text-blue-600">
                        Machine Learning
                      </p>

                      <h2 className="mt-1 text-xl font-bold text-slate-900">
                        Historical Occupancy-Demand Forecast
                      </h2>

                      <p className="mt-2 max-w-3xl text-sm text-slate-500">
                        One-day-ahead occupied-room demand prediction
                        generated by the trained hotel-demand forecasting
                        model.
                      </p>
                    </div>

                    <span className="w-fit rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">
                      Historical ML Demo
                    </span>
                  </div>

                  {occupancyForecast ? (
                    <>
                      {/* FORECAST METRICS */}

                      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                        <div className="rounded-xl bg-blue-50 p-5">
                          <p className="text-xs font-semibold uppercase tracking-wide text-blue-600">
                            Forecast Demand
                          </p>

                          <p className="mt-2 text-3xl font-bold text-slate-900">
                            {
                              occupancyForecast.predicted_occupied_rooms
                            }
                          </p>

                          <p className="mt-1 text-xs text-slate-500">
                            occupied-room demand proxy
                          </p>
                        </div>

                        <div className="rounded-xl bg-slate-50 p-5">
                          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                            Forecast Date
                          </p>

                          <p className="mt-2 text-lg font-bold text-slate-900">
                            {occupancyForecast.forecast_date}
                          </p>

                          <p className="mt-1 text-xs text-slate-500">
                            one-day-ahead forecast
                          </p>
                        </div>

                        <div className="rounded-xl bg-slate-50 p-5">
                          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                            Validation MAE
                          </p>

                          <p className="mt-2 text-lg font-bold text-slate-900">
                            {
                              occupancyForecast.validation_mean_mae
                            }
                          </p>

                          <p className="mt-1 text-xs text-slate-500">
                            rolling validation
                          </p>
                        </div>

                        <div className="rounded-xl bg-green-50 p-5">
                          <p className="text-xs font-semibold uppercase tracking-wide text-green-700">
                            Baseline Improvement
                          </p>

                          <p className="mt-2 text-lg font-bold text-slate-900">
                            {
                              occupancyForecast.improvement_vs_baseline_percent
                            }
                            %
                          </p>

                          <p className="mt-1 text-xs text-slate-500">
                            versus persistence baseline
                          </p>
                        </div>
                      </div>

                      {/* DEMAND LEVEL + RECOMMENDATION */}

                      <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-5">
                        <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
                          <div>
                            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                              Predicted Demand Level
                            </p>

                            <span
                              className={`mt-2 inline-flex rounded-full px-3 py-1 text-sm font-bold ${
                                occupancyForecast.demand_level === 'HIGH'
                                  ? 'bg-red-100 text-red-700'
                                  : occupancyForecast.demand_level ===
                                      'MEDIUM'
                                    ? 'bg-amber-100 text-amber-700'
                                    : 'bg-green-100 text-green-700'
                              }`}
                            >
                              {occupancyForecast.demand_level}
                            </span>
                          </div>

                          <div className="max-w-3xl">
                            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                              Operational Recommendation
                            </p>

                            <p className="mt-2 text-sm font-medium leading-6 text-slate-700">
                              {
                                occupancyForecast.operational_recommendation
                              }
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* MODEL DETAILS */}

                      <div className="mt-5 rounded-xl border border-slate-200 p-5">
                        <div className="grid gap-4 md:grid-cols-3">
                          <div>
                            <p className="text-xs font-semibold text-slate-500">
                              Model
                            </p>

                            <p className="mt-1 text-sm font-semibold text-slate-900">
                              {occupancyForecast.model}
                            </p>
                          </div>

                          <div>
                            <p className="text-xs font-semibold text-slate-500">
                              Historical Data Through
                            </p>

                            <p className="mt-1 text-sm font-semibold text-slate-900">
                              {
                                occupancyForecast.historical_data_end
                              }
                            </p>
                          </div>

                          <div>
                            <p className="text-xs font-semibold text-slate-500">
                              Baseline MAE
                            </p>

                            <p className="mt-1 text-sm font-semibold text-slate-900">
                              {
                                occupancyForecast.baseline_mean_mae
                              }
                            </p>
                          </div>
                        </div>

                        <p className="mt-5 text-xs leading-5 text-slate-500">
                          {
                            occupancyForecast.target_definition
                          }{' '}
                          This is a historical model demonstration
                          based on the public training dataset and
                          must not be interpreted as the live
                          occupancy of this demo hotel.
                        </p>
                      </div>
                    </>
                  ) : forecastError ? (
                    <div className="mt-6 rounded-xl bg-amber-50 px-5 py-4 text-sm text-amber-800">
                      {forecastError}
                    </div>
                  ) : (
                    <div className="mt-6 text-sm text-slate-500">
                      Loading occupancy forecast...
                    </div>
                  )}
                </div>
              </section>
            )}

            {/* NAVIGATION */}

            <section className="mt-8">
              <h2 className="text-lg font-bold text-slate-900">
                Quick Actions
              </h2>

              <div className="mt-4 flex flex-wrap gap-3">
                {/* MANAGER / FRONT DESK */}

                {(isManager || isFrontDesk) && (
                  <>
                    <button
                      type="button"
                      onClick={() => navigate('/rooms')}
                      className="rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
                    >
                      View Rooms
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        navigate('/reservations')
                      }
                      className="rounded-lg bg-white px-5 py-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
                    >
                      View Reservations
                    </button>

                    <button
                      type="button"
                      onClick={() => navigate('/tasks')}
                      className="rounded-lg bg-white px-5 py-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
                    >
                      View Tasks
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        navigate('/guest-requests')
                      }
                      className="rounded-lg bg-white px-5 py-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
                    >
                      View Guest Requests
                    </button>
                  </>
                )}

                {/* OPERATIONS */}

                {isOperations && (
                  <>
                    <button
                      type="button"
                      onClick={() => navigate('/rooms')}
                      className="rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
                    >
                      View Rooms
                    </button>

                    <button
                      type="button"
                      onClick={() => navigate('/tasks')}
                      className="rounded-lg bg-white px-5 py-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
                    >
                      My Tasks
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        navigate('/guest-requests')
                      }
                      className="rounded-lg bg-white px-5 py-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
                    >
                      Assigned Guest Requests
                    </button>
                  </>
                )}

                {/* GUEST */}

                {isGuest && (
                  <>
                    <button
                      type="button"
                      onClick={() =>
                        navigate('/guest-requests')
                      }
                      className="rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
                    >
                      Submit Guest Request
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        navigate('/reservations')
                      }
                      className="rounded-lg bg-white px-5 py-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
                    >
                      My Reservations
                    </button>
                  </>
                )}
              </div>
            </section>

            {/* RECENT TASKS */}

            {!isGuest &&
              dashboardData.tasks.length > 0 && (
                <section className="mt-10">
                  <h2 className="text-lg font-bold text-slate-900">
                    Recent Tasks
                  </h2>

                  <div className="mt-4 grid gap-4 lg:grid-cols-3">
                    {dashboardData.tasks
                      .slice(0, 3)
                      .map((task) => (
                        <article
                          key={task.id}
                          className="rounded-2xl bg-white p-5 shadow-sm"
                        >
                          <p className="text-xs font-semibold uppercase tracking-wider text-blue-600">
                            {task.task_type}
                          </p>

                          <h3 className="mt-2 font-bold text-slate-900">
                            {task.title}
                          </h3>

                          <div className="mt-4 flex flex-wrap gap-2">
                            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                              {task.priority}
                            </span>

                            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                              {task.status}
                            </span>
                          </div>
                        </article>
                      ))}
                  </div>
                </section>
              )}

            {/* RECENT GUEST REQUESTS */}

            {dashboardData.guestRequests.length > 0 && (
              <section className="mt-10">
                <h2 className="text-lg font-bold text-slate-900">
                  {isGuest
                    ? 'My Recent Requests'
                    : 'Recent Guest Requests'}
                </h2>

                <div className="mt-4 grid gap-4 lg:grid-cols-3">
                  {dashboardData.guestRequests
                    .slice(0, 3)
                    .map((request) => (
                      <article
                        key={request.id}
                        className="rounded-2xl bg-white p-5 shadow-sm"
                      >
                        <p className="text-xs font-semibold uppercase tracking-wider text-blue-600">
                          Request #{request.id}
                        </p>

                        <h3 className="mt-2 font-bold text-slate-900">
                          {request.ai_summary ??
                            request.message}
                        </h3>

                        <div className="mt-4 flex flex-wrap gap-2">
                          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                            {request.category}
                          </span>

                          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                            {request.priority}
                          </span>

                          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                            {request.status}
                          </span>
                        </div>
                      </article>
                    ))}
                </div>
              </section>
            )}
          </>
        )}
      </main>
    </div>
  )
}


export default DashboardPage