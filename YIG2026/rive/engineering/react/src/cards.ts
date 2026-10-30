import type { Card, Game, Stats } from './types'

// Chapter 2.5's community cards go in this order, leaving out the player's own game
const COMMUNITY_ORDER: Game[] = ['wordle', 'connections', 'spelling-bee', 'mini', 'strands']
// the anonymous flow's Chapter 2 mock shows these four
const ANONYMOUS_COMMUNITY: Game[] = ['connections', 'spelling-bee', 'mini', 'strands']

// The whole card list for one player, in order. This is the logic of engineering-guide.md, section 6.
export function buildCards(stats: Stats): Card[] {
  const anonymous = stats.flow === 'anonymous'
  const cards: Card[] = [
    { file: 1, scene: 'loading' },
    { file: 1, scene: 'start' },
    { file: 1, scene: 'ad' }, // Ad 1, on the empty Chapter 1 room
  ]

  for (let n = 1; n <= stats.chapter1Cards; n += 1) cards.push({ file: 1, scene: `chapter-1-card-${n}` })
  cards.push({ file: 1, scene: 'ad' }) // Ad 2

  // Chapter 2
  cards.push({ file: 2, scene: 'intro' })
  if (anonymous) {
    for (const game of ANONYMOUS_COMMUNITY) cards.push({ file: 2, scene: game, community: true, icon: game })
    cards.push({ file: 2, scene: 'to-chapter-3' }) // Ad 3, on the empty Chapter 3 room
  } else {
    for (const game of stats.games) {
      for (let n = 0; n < (stats.cardsPerGame[game] ?? 0); n += 1) cards.push({ file: 2, scene: game, icon: game })
    }
    if (stats.games.length === 1) {
      cards.push({ file: 2, scene: 'bridge' })
      for (const game of COMMUNITY_ORDER.filter((g) => g !== stats.games[0])) {
        cards.push({ file: 2, scene: game, community: true, icon: game })
      }
    }
    // no card on the empty Chapter 3 room: the tap on the last Chapter 2 card plays both moves
  }

  // Chapter 3
  if (anonymous) {
    cards.push({ file: 3, scene: 'chapter-3' }, { file: 3, scene: 'chapter-3' })
  } else {
    cards.push({ file: 3, scene: 'chapter-3' }, { file: 3, scene: 'chapter-3-bird' })
    if (stats.eventBadges > 0) cards.push({ file: 3, scene: 'ad' })
    if (stats.achievementBadges > 0) cards.push({ file: 3, scene: 'ad' })
  }

  // Chapter 4: the first card is the lighter blue wall (reveal false); the next two keep the top game's colour (reveal true)
  const top: Game = anonymous ? 'wordle' : stats.topGame
  cards.push({ file: 3, scene: 'chapter-4', topGame: top, reveal: false })
  cards.push({ file: 3, scene: 'chapter-4', icon: top, reveal: true })
  cards.push({ file: 3, scene: 'chapter-4', reveal: true }) // the video, in HTML

  // End, then the Share card on the same room
  cards.push({ file: 3, scene: 'end' })
  if (!anonymous) cards.push({ file: 3, scene: 'end' })
  return cards
}
