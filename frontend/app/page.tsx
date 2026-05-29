import AIQueryBox from '../components/AIQueryBox'
import Timeline from '../components/Timeline'
import SemanticSearch from '../components/SemanticSearch'

export default function HomePage() {
  return (
    <main className="min-h-screen bg-black text-white p-10">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-5xl font-bold mb-10">
          Enterprise Decision Brain
        </h1>

        <AIQueryBox />

        <Timeline />
        <SemanticSearch />
      </div>
    </main>
  )
}