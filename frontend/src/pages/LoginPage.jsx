import { useState } from 'react'
import { useNavigate } from 'react-router'

import apiClient from '../api/client.js'

function LoginPage() {
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()

    setErrorMessage('')
    setIsLoading(true)

    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)

    try {
      const response = await apiClient.post(
        '/auth/login',
        formData,
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        },
      )

      localStorage.setItem(
        'accessToken',
        response.data.access_token,
      )

      navigate('/dashboard')
    } catch (error) {
      if (error.response?.status === 401) {
        setErrorMessage('Invalid email or password.')
      } else {
        setErrorMessage(
          'Unable to sign in. Please check that the backend is running.',
        )
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="flex min-h-screen bg-slate-100">
      <section className="hidden w-1/2 flex-col justify-between bg-slate-900 p-12 text-white lg:flex">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-blue-400">
            AI Hotel Platform
          </p>

          <h1 className="mt-6 max-w-xl text-5xl font-bold leading-tight">
            Smarter hotel operations and better guest experiences.
          </h1>

          <p className="mt-6 max-w-lg text-lg leading-8 text-slate-300">
            Manage reservations, rooms, staff workflows, housekeeping tasks,
            and AI-powered guest requests from one platform.
          </p>
        </div>

        <p className="text-sm text-slate-400">
          Secure role-based access for hotel teams and guests.
        </p>
      </section>

      <section className="flex w-full items-center justify-center px-6 py-12 lg:w-1/2">
        <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl sm:p-10">
          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-blue-600">
              Welcome back
            </p>

            <h2 className="mt-3 text-3xl font-bold text-slate-900">
              Sign in to your account
            </h2>

            <p className="mt-2 text-sm text-slate-500">
              Enter your hotel platform credentials.
            </p>
          </div>

          <form
            className="mt-8 space-y-5"
            onSubmit={handleSubmit}
          >
            <div>
              <label
                htmlFor="email"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Email address
              </label>

              <input
                id="email"
                name="email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                autoComplete="email"
                placeholder="manager@hotel.com"
                required
                className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Password
              </label>

              <input
                id="password"
                name="password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="current-password"
                placeholder="Enter your password"
                required
                className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
              />
            </div>

            {errorMessage && (
              <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
                {errorMessage}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white transition hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-200 disabled:cursor-not-allowed disabled:bg-blue-400"
            >
              {isLoading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <p className="mt-8 text-center text-xs text-slate-400">
            AI Hotel Operations &amp; Guest Experience Platform
          </p>
        </div>
      </section>
    </main>
  )
}

export default LoginPage