import type { Card, Game, Stats } from './types'

// The order of the games in Chapter 2, and of Chapter 2.5's community cards. This is our default: change it here. Rive plays
// any order, because each move just sets the next scene.
export const GAME_ORDER: Game[] = ['wordle', 'connections', 'spelling-bee', 'mini', 'midi', 'daily', 'strands']

// The games that have community cards (The Midi and The Crossword have none)
export const COMMUNITY_GAMES: Game[] = ['wordle', 'connections', 'spelling-bee', 'mini', 'strands']

// Chapter 2.5's community cards: the community games in GAME_ORDER, leaving out the player's own game
const communityGames = (own?: Game): Game[] => GAME_ORDER.filter((game) => COMMUNITY_GAMES.includes(game) && game !== own)

// The whole card list for one player, in order. This is the logic of engineering-guide.md, section 5. A card that does not
// qualify is never added, so nothing is skipped when the player taps.
export function buildCards(stats: Stats): Card[] {
  // a subscriber with no qualifying game gets the anonymous flow
  const own = GAME_ORDER.filter((game) => stats.games.includes(game))
  const anonymous = stats.flow === 'anonymous' || own.length === 0
  const cards: Card[] = [
    { file: 1, scene: 'loading' },
    { file: 1, scene: 'start' },
    { file: 1, scene: 'ad', ad: true }, // Ad 1, on the empty Chapter 1 room
  ]

  // Chapter 1: always five cards, in both flows
  for (let n = 1; n <= 5; n += 1) cards.push({ file: 1, scene: `chapter-1-card-${n}` })
  cards.push({ file: 1, scene: 'ad', ad: true }) // Ad 2

  // Chapter 2
  cards.push({ file: 2, scene: 'intro' })
  if (anonymous) {
    // community cards for every community game but Wordle: Chapter 1 already covers Wordle (ADIEU and PSHAW)
    for (const game of communityGames('wordle')) cards.push({ file: 2, scene: game, community: true, icon: game })
    cards.push({ file: 2, scene: 'to-chapter-3', ad: true }) // Ad 3, on the empty Chapter 3 room
  } else {
    for (const game of own) {
      for (let n = 0; n < (stats.cardsPerGame[game] ?? 0); n += 1) cards.push({ file: 2, scene: game, icon: game })
    }
    if (own.length === 1) {
      // Chapter 2.5: the bridge, then a community card for each other community game
      cards.push({ file: 2, scene: 'bridge' })
      for (const game of communityGames(own[0])) cards.push({ file: 2, scene: game, community: true, icon: game })
    }
    // no card on the empty Chapter 3 room: the tap on the last Chapter 2 card plays both moves
  }

  // Chapter 3
  cards.push({ file: 3, scene: 'chapter-3' }, { file: 3, scene: 'chapter-3-bird' })
  if (anonymous) {
    // four cards, never skipped: the last two are on the empty Chapter 3 room
    cards.push({ file: 3, scene: 'ad' }, { file: 3, scene: 'ad' })
  } else {
    // the badge cards are added only when the player has some
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
