'use client'

import { useState } from 'react'
import { askQuestion } from '../services/api'

export default function AIQueryBox() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)

  const handleAsk = async () => {
    if (!question) return

    try {
      setLoading(true)

      const data = await askQuestion(question)

      setAnswer(data.answer)
    } catch (error) {
      console.error(error)
      setAnswer('Backend connection failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-gray-900 p-6 rounded-2xl">
      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Why did payment-service fail yesterday?"
        className="w-full p-4 rounded-xl bg-black border border-gray-700"
      />

      <button
        onClick={handleAsk}
        className="mt-4 bg-white text-black px-6 py-3 rounded-xl"
      >
        Ask
      </button>

      {loading && (
        <p className="mt-4">
          Thinking...
        </p>
      )}

      {answer && (
        <div className="mt-6">
          <h2 className="font-bold mb-2">
            AI Response
          </h2>

          <p>{answer}</p>
        </div>
      )}
    </div>
  )
}