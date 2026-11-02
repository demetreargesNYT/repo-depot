// The card list is the one thing your page builds from the stats. A card names the Rive file and scene it shows, plus the
// tags its copy needs. See engineering-guide.md, section 6.

export type FileNumber = 1 | 2 | 3

export type Game = 'wordle' | 'connections' | 'strands' | 'spelling-bee' | 'mini' | 'midi' | 'daily'

export type Card = {
  file: FileNumber
  scene: string
  // Ad 1, Ad 2 and the anonymous Ad 3: shown the first time the player reaches them with Next, then skipped both ways
  ad?: boolean
  // File 2 only: a community card turns the game's Rive lockup off (the small HTML icon still shows)
  community?: boolean
  // the game whose small HTML icon this card's copy shows with
  icon?: Game
  // File 3: the player's top game, set once when File 3 has loaded
  topGame?: Game
  // File 3, Chapter 4: false on the first card (lighter blue wall), true from the top-game card on
  reveal?: boolean
}

export type Flow = 'subscriber' | 'anonymous'

export type Stats = {
  flow: Flow
  // the games the player has 10 or more completed puzzles in (their order here does not matter: GAME_ORDER decides it)
  games: Game[]
  // how many cards each of those games has for this player (from the ranked list and thresholds in the stats requirements)
  cardsPerGame: Partial<Record<Game, number>>
  eventBadges: number
  achievementBadges: number
  topGame: Game
}

// What a move asks the copy layer to do
export type CopyLayer = {
  id: number
  kind: 'copy' | 'icon'
  frame: number // the card index for a copy block; the card that brought the icon in for an icon block
  game?: Game
  phase: 'in' | 'out'
  delayMs: number | null
  quick: boolean
  afterIcon: boolean
  back: boolean
  settledAt: number
}
