'use client'

import { useEffect, useState } from 'react'
import { fetchTimeline } from '../services/timeline'

export default function Timeline() {
  const [events, setEvents] = useState([])

  useEffect(() => {
  loadTimeline()

  const interval = setInterval(() => {
    loadTimeline()
  }, 5000)

  return () => clearInterval(interval)
}, [])

  const loadTimeline = async () => {
    try {
      const data = await fetchTimeline()

      setEvents(data)
    } catch (error) {
      console.error(error)
    }
  }

  return (
    <div className="mt-10">
      <h2 className="text-3xl font-bold mb-6">
        Operational Timeline
      </h2>

      <div className="space-y-4">
        {events.map((event: any, index) => (
          <div
            key={index}
            className="bg-gray-900 border border-gray-800 p-5 rounded-2xl"
          >
            <div className="flex justify-between">
              <div>
                <p className="font-bold">
                  {event.source}
                </p>

                <p className="text-gray-400 mt-1">
                  {event.actor}
                </p>
              </div>

              <div className="text-right">
                <p>{event.action}</p>

                <p className="text-gray-500 text-sm mt-1">
                  {event.target}
                </p>
              </div>
            </div>

            <p className="text-gray-500 text-sm mt-4">
              {event.timestamp}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}