import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router'

import apiClient from '../api/client.js'
import { getCurrentUser } from '../api/auth.js'

import {
  assignTask,
  completeTask,
  createTask,
  startTask,
} from '../api/tasks.js'

function TasksPage() {
  const navigate = useNavigate()

  const [currentUser, setCurrentUser] = useState(null)

  const [tasks, setTasks] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  const [errorMessage, setErrorMessage] = useState('')
  const [actionMessage, setActionMessage] = useState('')

  const [processingTaskId, setProcessingTaskId] =
    useState(null)

  const [showCreateForm, setShowCreateForm] =
    useState(false)

  const [newTask, setNewTask] = useState({
    title: '',
    description: '',
    task_type: 'HOUSEKEEPING',
    priority: 'MEDIUM',
    room_id: '1',
    reservation_id: '1',
    assigned_to: '5',
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
  // LOAD TASKS
  // --------------------------------------------------

  const loadTasks = useCallback(async () => {
    try {
      setErrorMessage('')

      const response = await apiClient.get('/tasks')

      setTasks(response.data)
    } catch (error) {
      setErrorMessage(
        error.response?.data?.detail ??
          'Unable to load operational tasks.',
      )
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadTasks()
  }, [loadTasks])

  // --------------------------------------------------
  // ROLE HELPERS
  // --------------------------------------------------

  const role = currentUser?.role

  const isOperations =
    role === 'OPERATIONS'

  const canManageTasks =
    role === 'MANAGER' ||
    role === 'FRONT_DESK'

  // --------------------------------------------------
  // CREATE TASK
  // --------------------------------------------------

  async function handleCreateTask(event) {
    event.preventDefault()

    if (!canManageTasks) {
      return
    }

    if (!newTask.title.trim()) {
      setErrorMessage('Task title is required.')
      return
    }

    try {
      setErrorMessage('')
      setActionMessage('')

      const taskData = {
        title: newTask.title.trim(),
        description: newTask.description.trim(),
        task_type: newTask.task_type,
        priority: newTask.priority,
        room_id: Number(newTask.room_id),
        reservation_id: Number(
          newTask.reservation_id,
        ),
        assigned_to: Number(
          newTask.assigned_to,
        ),
      }

      await createTask(taskData)

      setActionMessage(
        'Task created successfully.',
      )

      setNewTask({
        title: '',
        description: '',
        task_type: 'HOUSEKEEPING',
        priority: 'MEDIUM',
        room_id: '1',
        reservation_id: '1',
        assigned_to: '5',
      })

      setShowCreateForm(false)

      await loadTasks()
    } catch (error) {
      setErrorMessage(
        error.response?.data?.detail ??
          'Unable to create task.',
      )
    }
  }

  // --------------------------------------------------
  // ASSIGN TASK
  // --------------------------------------------------

  async function handleAssign(taskId) {
    if (!canManageTasks) {
      return
    }

    const staffId = window.prompt(
      'Enter the Operations staff user ID:',
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
      setProcessingTaskId(taskId)
      setErrorMessage('')
      setActionMessage('')

      await assignTask(
        taskId,
        parsedStaffId,
      )

      setActionMessage(
        `Task #${taskId} assigned successfully.`,
      )

      await loadTasks()
    } catch (error) {
      setErrorMessage(
        error.response?.data?.detail ??
          'Unable to assign task.',
      )
    } finally {
      setProcessingTaskId(null)
    }
  }

  // --------------------------------------------------
  // START TASK
  // --------------------------------------------------

  async function handleStart(taskId) {
    try {
      setProcessingTaskId(taskId)
      setErrorMessage('')
      setActionMessage('')

      await startTask(taskId)

      setActionMessage(
        `Task #${taskId} started successfully.`,
      )

      await loadTasks()
    } catch (error) {
      setErrorMessage(
        error.response?.data?.detail ??
          'Unable to start task.',
      )
    } finally {
      setProcessingTaskId(null)
    }
  }

  // --------------------------------------------------
  // COMPLETE TASK
  // --------------------------------------------------

  async function handleComplete(taskId) {
    const completionNotes = window.prompt(
      'Enter completion notes:',
    )

    if (!completionNotes?.trim()) {
      return
    }

    try {
      setProcessingTaskId(taskId)
      setErrorMessage('')
      setActionMessage('')

      await completeTask(
        taskId,
        completionNotes.trim(),
      )

      setActionMessage(
        `Task #${taskId} completed successfully.`,
      )

      await loadTasks()
    } catch (error) {
      setErrorMessage(
        error.response?.data?.detail ??
          'Unable to complete task.',
      )
    } finally {
      setProcessingTaskId(null)
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
              {isOperations
                ? 'My Operational Tasks'
                : 'Operational Tasks'}
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

        {/* PAGE TITLE */}

        <div className="mb-6">

          <h2 className="text-xl font-bold text-slate-900">
            {isOperations
              ? 'Assigned Work'
              : 'Staff Task Management'}
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            {isOperations
              ? 'View and complete operational tasks assigned to you.'
              : 'Monitor and manage housekeeping, maintenance and guest-service tasks.'}
          </p>

        </div>

        {/* CREATE BUTTON - MANAGER / FRONT DESK ONLY */}

        {canManageTasks && (
          <div className="mb-6">

            <button
              type="button"
              onClick={() =>
                setShowCreateForm(
                  (currentValue) =>
                    !currentValue,
                )
              }
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
            >
              {showCreateForm
                ? 'Cancel'
                : 'Create Task'}
            </button>

          </div>
        )}

        {/* CREATE FORM */}

        {canManageTasks &&
          showCreateForm && (
            <form
              onSubmit={handleCreateTask}
              className="mb-8 rounded-2xl bg-white p-6 shadow-sm"
            >

              <h3 className="text-lg font-bold text-slate-900">
                Create Operational Task
              </h3>

              <div className="mt-5 grid gap-4 md:grid-cols-2">

                {/* TITLE */}

                <div>
                  <label className="mb-1 block text-sm font-semibold text-slate-700">
                    Title
                  </label>

                  <input
                    type="text"
                    required
                    value={newTask.title}
                    onChange={(event) =>
                      setNewTask({
                        ...newTask,
                        title:
                          event.target.value,
                      })
                    }
                    placeholder="Inspect room 201"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-blue-500"
                  />
                </div>

                {/* TASK TYPE */}

                <div>
                  <label className="mb-1 block text-sm font-semibold text-slate-700">
                    Task Type
                  </label>

                  <select
                    value={newTask.task_type}
                    onChange={(event) =>
                      setNewTask({
                        ...newTask,
                        task_type:
                          event.target.value,
                      })
                    }
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-blue-500"
                  >
                    <option value="HOUSEKEEPING">
                      HOUSEKEEPING
                    </option>

                    <option value="MAINTENANCE">
                      MAINTENANCE
                    </option>

                    <option value="GUEST_SERVICE">
                      GUEST_SERVICE
                    </option>
                  </select>
                </div>

                {/* DESCRIPTION */}

                <div className="md:col-span-2">
                  <label className="mb-1 block text-sm font-semibold text-slate-700">
                    Description
                  </label>

                  <textarea
                    value={newTask.description}
                    onChange={(event) =>
                      setNewTask({
                        ...newTask,
                        description:
                          event.target.value,
                      })
                    }
                    rows="3"
                    placeholder="Describe the work to be completed..."
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-blue-500"
                  />
                </div>

                {/* PRIORITY */}

                <div>
                  <label className="mb-1 block text-sm font-semibold text-slate-700">
                    Priority
                  </label>

                  <select
                    value={newTask.priority}
                    onChange={(event) =>
                      setNewTask({
                        ...newTask,
                        priority:
                          event.target.value,
                      })
                    }
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-blue-500"
                  >
                    <option value="LOW">
                      LOW
                    </option>

                    <option value="MEDIUM">
                      MEDIUM
                    </option>

                    <option value="HIGH">
                      HIGH
                    </option>
                  </select>
                </div>

                {/* ROOM ID */}

                <div>
                  <label className="mb-1 block text-sm font-semibold text-slate-700">
                    Room ID
                  </label>

                  <input
                    type="number"
                    min="1"
                    required
                    value={newTask.room_id}
                    onChange={(event) =>
                      setNewTask({
                        ...newTask,
                        room_id:
                          event.target.value,
                      })
                    }
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-blue-500"
                  />
                </div>

                {/* RESERVATION */}

                <div>
                  <label className="mb-1 block text-sm font-semibold text-slate-700">
                    Reservation ID
                  </label>

                  <input
                    type="number"
                    min="1"
                    required
                    value={
                      newTask.reservation_id
                    }
                    onChange={(event) =>
                      setNewTask({
                        ...newTask,
                        reservation_id:
                          event.target.value,
                      })
                    }
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-blue-500"
                  />
                </div>

                {/* STAFF */}

                <div>
                  <label className="mb-1 block text-sm font-semibold text-slate-700">
                    Assigned Staff ID
                  </label>

                  <input
                    type="number"
                    min="1"
                    required
                    value={newTask.assigned_to}
                    onChange={(event) =>
                      setNewTask({
                        ...newTask,
                        assigned_to:
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
                Create Task
              </button>

            </form>
          )}

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

        {/* TASK LIST */}

        {isLoading ? (
          <div className="rounded-2xl bg-white p-6 text-slate-500 shadow-sm">
            Loading tasks...
          </div>
        ) : tasks.length === 0 ? (
          <div className="rounded-2xl bg-white p-6 text-slate-500 shadow-sm">
            {isOperations
              ? 'No tasks are currently assigned to you.'
              : 'No operational tasks found.'}
          </div>
        ) : (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">

            {tasks.map((task) => {
              const isProcessing =
                processingTaskId === task.id

              const canWorkTask =
                role === 'MANAGER' ||
                (
                  role === 'OPERATIONS' &&
                  task.assigned_to ===
                    currentUser?.id
                )

              return (
                <article
                  key={task.id}
                  className="rounded-2xl bg-white p-6 shadow-sm"
                >

                  {/* HEADER */}

                  <div className="flex items-start justify-between gap-4">

                    <div>

                      <p className="text-xs font-semibold uppercase tracking-wider text-blue-600">
                        {task.task_type}
                      </p>

                      <h3 className="mt-2 text-lg font-bold text-slate-900">
                        {task.title}
                      </h3>

                    </div>

                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                      {task.status}
                    </span>

                  </div>

                  {/* DESCRIPTION */}

                  {task.description && (
                    <p className="mt-4 text-sm leading-6 text-slate-600">
                      {task.description}
                    </p>
                  )}

                  {/* DETAILS */}

                  <div className="mt-5 space-y-2 text-sm text-slate-600">

                    <p>
                      Priority:{' '}
                      <span className="font-semibold text-slate-800">
                        {task.priority}
                      </span>
                    </p>

                    <p>
                      Room:{' '}
                      <span className="font-semibold text-slate-800">
                        {task.room_id ??
                          'Not linked'}
                      </span>
                    </p>

                    <p>
                      Reservation:{' '}
                      <span className="font-semibold text-slate-800">
                        {task.reservation_id ??
                          'Not linked'}
                      </span>
                    </p>

                    {!isOperations && (
                      <p>
                        Assigned staff:{' '}
                        <span className="font-semibold text-slate-800">
                          {task.assigned_to ??
                            'Unassigned'}
                        </span>
                      </p>
                    )}

                  </div>

                  {/* COMPLETION NOTES */}

                  {task.completion_notes && (
                    <div className="mt-5 rounded-lg bg-emerald-50 p-4">

                      <p className="text-xs font-semibold uppercase tracking-wider text-emerald-700">
                        Completion Notes
                      </p>

                      <p className="mt-2 text-sm text-emerald-900">
                        {task.completion_notes}
                      </p>

                    </div>
                  )}

                  {/* ACTIONS */}

                  <div className="mt-6 flex flex-wrap gap-3">

                    {/* MANAGER / FRONT DESK */}

                    {task.status === 'PENDING' &&
                      canManageTasks && (
                        <button
                          type="button"
                          disabled={isProcessing}
                          onClick={() =>
                            handleAssign(task.id)
                          }
                          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:opacity-50"
                        >
                          Assign
                        </button>
                      )}

                    {/* OPERATIONS / MANAGER */}

                    {task.status === 'ASSIGNED' &&
                      canWorkTask && (
                        <button
                          type="button"
                          disabled={isProcessing}
                          onClick={() =>
                            handleStart(task.id)
                          }
                          className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-amber-600 disabled:opacity-50"
                        >
                          Start
                        </button>
                      )}

                    {task.status ===
                      'IN_PROGRESS' &&
                      canWorkTask && (
                        <button
                          type="button"
                          disabled={isProcessing}
                          onClick={() =>
                            handleComplete(task.id)
                          }
                          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:opacity-50"
                        >
                          Complete
                        </button>
                      )}

                    {task.status === 'COMPLETED' && (
                      <span className="rounded-lg bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-700">
                        Completed
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

export default TasksPage