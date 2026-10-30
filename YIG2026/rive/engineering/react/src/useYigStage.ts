import { useCallback, useEffect, useRef, useState } from 'react'
import { useRive } from '@rive-app/react-canvas'
import type { Rive } from '@rive-app/react-canvas'
import { FILES, FILE_NUMBERS } from './files'
import { CLEAR_MS, COMMUNITY_COPY_MS, INTRO_MS, PAN_MS, RISE_SETTLED_MS } from './timing'
import type { Card, CopyLayer, FileNumber, Game } from './types'

type Step = 1 | -1

type Mutable = {
  frame: number // the card on screen
  shown: number // the file on screen, 0 to 2
  loaded: boolean[]
  waiters: Array<Array<() => void>>
  visited: Set<string> // 'file:scene' rooms whose intro has played (or that have none)
  copyFrom: Record<string, number> // 'file:scene': when a first visit's copy may arrive (performance.now() time)
  pan: { dir: number; endsAt: number }
  heldTimer: number
  holdToken: number
  swapTimer: number
  hopTimer: number
  hopRun: (() => void) | null
  nextId: number
}

const roomKey = (card: Card) => `${card.file}:${card.scene}`

// Drives the three Rive files from a card list: the rules of engineering-guide.md in one hook.
export function useYigStage(cards: Card[]) {
  const [layers, setLayers] = useState<CopyLayer[]>([])
  const [frame, setFrame] = useState(0)
  const [stack, setStack] = useState<{ shown: number; top: number | null }>({ shown: 0, top: null })
  const [loadedCount, setLoadedCount] = useState(0)

  // Files load one after the other: File 2 starts once File 1 has loaded, File 3 once File 2 has. Every one stays loaded.
  const file1 = useRive({ src: FILES[1].src, stateMachines: 'Backdrop', autoplay: true, autoBind: true })
  const file2 = useRive(loadedCount >= 1 ? { src: FILES[2].src, stateMachines: 'Backdrop', autoplay: true, autoBind: true } : null)
  const file3 = useRive(loadedCount >= 2 ? { src: FILES[3].src, stateMachines: 'Backdrop', autoplay: true, autoBind: true } : null)
  const states = [file1, file2, file3]
  const rives = useRef<Array<Rive | null>>([null, null, null])
  rives.current = states.map((s) => s.rive)

  const m = useRef<Mutable>({
    frame: 0,
    shown: 0,
    loaded: [false, false, false],
    waiters: [[], [], []],
    visited: new Set(FILE_NUMBERS.map((n) => `${n}:${FILES[n].opens}`)),
    copyFrom: {},
    pan: { dir: 0, endsAt: 0 },
    heldTimer: 0,
    holdToken: 0,
    swapTimer: 0,
    hopTimer: 0,
    hopRun: null,
    nextId: 1,
  })
  const cardsRef = useRef(cards)
  cardsRef.current = cards

  // ---- a file has loaded: set its top game, rest it if it is not on screen, let the next file start loading
  useEffect(() => {
    states.forEach((s, i) => {
      const rive = s.rive
      const mut = m.current
      if (!rive || mut.loaded[i]) return
      mut.loaded[i] = true
      rive.resizeDrawingSurfaceToCanvas()
      const top = cardsRef.current.find((c) => c.topGame)?.topGame
      const topProp = rive.viewModelInstance?.enum('topGame')
      if (top && topProp) topProp.value = top
      // let it draw its opening picture once, then rest until it is shown
      requestAnimationFrame(() => requestAnimationFrame(() => { if (i !== m.current.shown) rive.pause() }))
      setLoadedCount((n) => Math.max(n, i + 1))
      mut.waiters[i]?.splice(0).forEach((resolve) => resolve())
    })
  }) // runs after every render: it only acts the first time a file's Rive instance exists

  useEffect(() => {
    const onResize = () => rives.current.forEach((r) => r?.resizeDrawingSurfaceToCanvas())
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  const whenLoaded = useCallback((i: number) => new Promise<void>((resolve) => {
    if (m.current.loaded[i]) resolve()
    else m.current.waiters[i]?.push(resolve)
  }), [])

  // ---- properties: direction, lockup, reveal, then scene (the one that starts the move)
  const setScene = (file: FileNumber, scene: string, step: Step, community: boolean, reveal?: boolean) => {
    const vm = rives.current[file - 1]?.viewModelInstance
    if (!vm) return
    const direction = vm.enum('direction')
    if (direction) direction.value = step < 0 ? 'back' : 'forward'
    if (FILES[file].hasLockup) {
      const lockup = vm.boolean('lockup')
      if (lockup) lockup.value = !community
    }
    if (reveal !== undefined) {
      const prop = vm.boolean('reveal')
      if (prop) prop.value = reveal
    }
    const sceneProp = vm.enum('scene')
    if (sceneProp) sceneProp.value = scene
  }

  // ---- show file i on top of the one on screen, playing; the old one hides and rests once the new one has drawn
  const show = (i: number) => {
    const mut = m.current
    if (i === mut.shown) return
    const old = mut.shown
    rives.current[i]?.play()
    setStack({ shown: old, top: i })
    requestAnimationFrame(() => requestAnimationFrame(() => {
      rives.current[old]?.pause()
      setStack({ shown: i, top: null })
    }))
    mut.shown = i
  }

  // ---- copy: the old copy leaves at once, the new copy arrives after `delay` ms (null: right after the old has cleared)
  const showCopy = (n: number, opts: { changed: boolean; delay: number | null; back: boolean }) => {
    const card = cardsRef.current[n]
    if (!card) return
    const now = performance.now()
    const { changed, back } = opts
    let { delay } = opts
    setLayers((prev) => {
      const keep: CopyLayer[] = []
      const leaving: number[] = []
      for (const l of prev) {
        if (l.phase === 'out') { keep.push(l); continue }
        if (!changed && l.kind === 'icon') { keep.push(l); continue } // the game's icon stays while its cards change
        if (now >= l.settledAt) { keep.push({ ...l, phase: 'out', back }); leaving.push(l.id) } // finished rising: lifts out
        // still rising (or waiting to): just removed
      }
      const iconStays = !changed && !!card.icon && keep.some((l) => l.kind === 'icon' && l.game === card.icon && l.phase === 'in')
      if (delay === null && changed) delay = CLEAR_MS
      const out = [...keep]
      const base = { phase: 'in' as const, back, settledAt: now + (delay ?? CLEAR_MS) + RISE_SETTLED_MS }
      if (card.icon && !iconStays) {
        out.push({ ...base, id: m.current.nextId++, kind: 'icon', frame: n, game: card.icon as Game, delayMs: delay, quick: false, afterIcon: false })
      }
      out.push({ ...base, id: m.current.nextId++, kind: 'copy', frame: n, delayMs: delay, quick: delay === null, afterIcon: !!card.icon && !iconStays && delay !== null })
      if (leaving.length > 0) {
        window.setTimeout(() => setLayers((p) => p.filter((l) => !leaving.includes(l.id))), CLEAR_MS)
      }
      return out
    })
  }

  // ---- one move: Next or Back
  const move = useCallback((step: Step) => {
    const mut = m.current
    const list = cardsRef.current
    window.clearTimeout(mut.heldTimer)
    const token = ++mut.holdToken
    const target = mut.frame + step
    if (target < 1 && step < 0) return // Back never returns to Loading
    if (target < 0 || target > list.length - 1) return
    const from = list[mut.frame]
    const to = list[target]
    if (!from || !to) return
    const roomChange = to.file !== from.file || to.scene !== from.scene
    const now = performance.now()
    // crossing files from a card that is not on the empty room: the first move goes to that room, the second starts after it
    const legs = to.file !== from.file && (step > 0 ? from.scene !== FILES[from.file].ends : to.scene !== FILES[to.file].ends) ? 2 : 1
    // a Back during any pan, and a Next during a Back pan, wait for the pan to end; only the last tap held counts
    if (roomChange && mut.pan.endsAt > now && (step < 0 || mut.pan.dir < 0)) {
      mut.heldTimer = window.setTimeout(() => move(step), mut.pan.endsAt - now)
      return
    }
    const fi = to.file - 1
    if (step > 0 && !mut.loaded[fi]) {
      // the next file has not loaded yet: hold the tap on the empty room until it has
      void whenLoaded(fi).then(() => { if (token === mut.holdToken) move(step) })
      return
    }
    if (roomChange) window.clearTimeout(mut.swapTimer) // a new room change takes over from a Back's hand-back still to come
    if (roomChange && mut.hopRun) { window.clearTimeout(mut.hopTimer); mut.hopRun() } // and cuts a Next's two moves short
    mut.frame = target
    setFrame(target)
    const key = roomKey(to)
    const firstVisit = roomChange && step > 0 && !mut.visited.has(key) && !FILES[to.file].noIntro.includes(to.scene)
    if (roomChange) {
      mut.pan = { dir: step, endsAt: now + PAN_MS * legs }
      if (to.file === from.file) {
        setScene(to.file, to.scene, step, !!to.community, to.reveal)
      } else if (step > 0) {
        // Next into another file: it is already on the shared picture, so show it and set its scene on the same frame
        const takeOver = () => { mut.hopRun = null; show(fi); setScene(to.file, to.scene, step, !!to.community, to.reveal) }
        if (legs === 1) {
          takeOver()
        } else {
          // first the room pans out to the empty room, then the next file takes over
          setScene(from.file, FILES[from.file].ends, step, false)
          mut.hopRun = takeOver
          mut.hopTimer = window.setTimeout(takeOver, PAN_MS)
        }
      } else {
        // Back into the earlier file: pan back inside this file to the shared picture, then hand the stage back (and, if
        // the card is not on that picture, pan back into its room)
        setScene(from.file, FILES[from.file].opens, step, false)
        mut.swapTimer = window.setTimeout(() => {
          show(fi)
          if (legs === 2) setScene(to.file, to.scene, step, !!to.community, to.reveal)
        }, PAN_MS)
      }
    }
    if (firstVisit) {
      mut.visited.add(key)
      const wait = to.community && to.scene in COMMUNITY_COPY_MS ? COMMUNITY_COPY_MS[to.scene] ?? INTRO_MS : INTRO_MS
      mut.copyFrom[key] = now + (legs - 1) * PAN_MS + wait
    }
    const iconChange = to.icon !== from.icon
    const settleLeft = Math.max(0, (mut.copyFrom[key] ?? 0) - now) // an interrupted first visit still waits for its room
    let delay: number | null
    if (!roomChange) delay = settleLeft > 0 ? settleLeft : null // null: the quick swap after the old copy clears
    else if (firstVisit) delay = (mut.copyFrom[key] ?? now) - now
    else delay = Math.max(PAN_MS * legs, settleLeft)
    showCopy(target, { changed: roomChange || iconChange, delay, back: step < 0 })
  }, [whenLoaded])

  // the first card's copy is on screen from the start
  useEffect(() => { showCopy(0, { changed: true, delay: 0, back: false }) }, [])

  const onTap = useCallback(() => move(1), [move])
  const onBack = useCallback(() => move(-1), [move])

  return { states, stack, layers, frame, onTap, onBack, whenLoaded, loadedCount }
}
