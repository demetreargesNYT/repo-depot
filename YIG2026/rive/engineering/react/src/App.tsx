import { useEffect, useMemo, useState } from 'react'
import { YigStage } from './YigStage'
import { buildCards } from './cards'
import type { Card, Game, Stats } from './types'

// An example player. Your page builds this from the stats payload.
const STATS: Stats = {
  flow: 'subscriber',
  games: ['wordle', 'connections'],
  cardsPerGame: { wordle: 4, connections: 5 },
  chapter1Cards: 5,
  eventBadges: 5,
  achievementBadges: 9,
  topGame: 'wordle',
}

function CopyBlock({ card, index }: { card: Card; index: number }) {
  // One designed line per mask: each line rises in its own, one step after the one before
  return (
    <>
      <span className="yig-mask">
        <span className="yig-line">{`Card ${index}`}</span>
      </span>
      <span className="yig-mask">
        <span className="yig-line">{`${card.scene} (file ${card.file})`}</span>
      </span>
    </>
  )
}

export function App() {
  const cards = useMemo(() => buildCards(STATS), [])
  const [statsReady, setStatsReady] = useState(false)

  // Loading: here the stats "arrive" after a moment. Fetch yours and set this when they are in.
  useEffect(() => {
    const timer = window.setTimeout(() => setStatsReady(true), 1500)
    return () => window.clearTimeout(timer)
  }, [])

  return (
    <YigStage
      cards={cards}
      statsReady={statsReady}
      renderCopy={(card, index) => <CopyBlock card={card} index={index} />}
      renderIcon={(game: Game) => <span style={{ display: 'grid', placeItems: 'center', width: 50, height: 49, border: '2px solid #121212', borderRadius: 10 }}>{game.slice(0, 1).toUpperCase()}</span>}
    />
  )
}
