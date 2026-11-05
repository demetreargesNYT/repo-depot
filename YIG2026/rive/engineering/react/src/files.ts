import type { FileNumber } from './types'

export type FileDef = {
  src: string
  // the empty room the file opens on and the one it ends on; neighbouring files share these pictures
  opens: string
  ends: string
  // scenes with no intro of their own: the copy for these arrives when the pan ends
  noIntro: string[]
  // only File 2 has the lockup property
  hasLockup: boolean
}

export const FILES: Record<FileNumber, FileDef> = {
  1: { src: '/yig/start-chapter-1.riv', opens: 'loading', ends: 'ad', noIntro: ['loading', 'ad'], hasLockup: false },
  2: { src: '/yig/chapter-2.riv', opens: 'from-chapter-1', ends: 'to-chapter-3', noIntro: ['from-chapter-1', 'to-chapter-3', 'chapter-2-community-intro'], hasLockup: true },
  3: { src: '/yig/chapters-3-4-end.riv', opens: 'ad', ends: 'end', noIntro: ['ad'], hasLockup: false },
}

export const FILE_NUMBERS: FileNumber[] = [1, 2, 3]

// Scenes that share one room or picture. A move between two of them is not a room change: no pan, the room keeps looping,
// and the copy swaps after the usual 0.34 s. Each list starts with the scene that owns the room; every other scene is its own room.
const ROOMS: Array<[FileNumber, string[]]> = [
  [3, ['ad', 'chapter-3-personal-badges', 'chapter-3-event-badges']], // the plain wall and floor
  [3, ['chapter-3', 'chapter-3-2']],
  [3, ['chapter-4', 'chapter-4-top-game', 'chapter-4-editor-video']],
  [3, ['end', 'share']],
]

// the scene that owns a scene's room (the scene itself when it has its own)
export const roomOf = (file: FileNumber, scene: string): string =>
  ROOMS.find(([f, list]) => f === file && list.includes(scene))?.[1][0] ?? scene
