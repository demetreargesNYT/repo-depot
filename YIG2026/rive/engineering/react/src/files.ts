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
  2: { src: '/yig/chapter-2.riv', opens: 'from-chapter-1', ends: 'to-chapter-3', noIntro: ['from-chapter-1', 'to-chapter-3', 'bridge'], hasLockup: true },
  3: { src: '/yig/chapters-3-4-end.riv', opens: 'ad', ends: 'end', noIntro: ['ad'], hasLockup: false },
}

export const FILE_NUMBERS: FileNumber[] = [1, 2, 3]
