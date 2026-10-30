import { useEffect } from 'react'
import type { CSSProperties, ReactNode } from 'react'
import { useYigStage } from './useYigStage'
import styles from './YigStage.module.css'
import type { Card, CopyLayer, Game } from './types'

type Props = {
  cards: Card[]
  // true once the stats have arrived: the stage moves from Loading to Start as soon as File 1 has loaded too
  statsReady: boolean
  // your copy for a card (the block is wrapped in the yig-text element for you)
  renderCopy: (card: Card, index: number) => ReactNode
  // the small icon for a game
  renderIcon: (game: Game) => ReactNode
}

const classes = (...names: Array<string | false | undefined>) => names.filter(Boolean).join(' ')

// The Rive stage with the copy on top, and the Next and Back controls.
export function YigStage({ cards, statsReady, renderCopy, renderIcon }: Props) {
  const stage = useYigStage(cards)

  // Loading -> Start: the stats are in and File 1 has loaded. This is an ordinary Next (scene 'start').
  const { frame, loadedCount, onTap } = stage
  useEffect(() => {
    if (statsReady && loadedCount >= 1 && frame === 0) onTap()
  }, [statsReady, loadedCount, frame, onTap])

  return (
    <div className={styles.root}>
      <div className={styles.background}>
        <div className={styles.artboard}>
          {stage.states.map((state, i) => {
            const visible = i === stage.stack.shown || i === stage.stack.top
            const style: CSSProperties = { visibility: visible ? 'visible' : 'hidden', zIndex: i === stage.stack.top ? 1 : undefined }
            return (
              <div key={i} className={styles.file} style={style} ref={state.setContainerRef}>
                <state.RiveComponent />
              </div>
            )
          })}
        </div>
      </div>

      <div className={styles.column}>
        {stage.layers.map((layer) => (
          <Layer key={layer.id} layer={layer} withIcon={!!cards[layer.frame]?.icon}>
            {layer.kind === 'icon' && layer.game ? renderIcon(layer.game) : cards[layer.frame] && renderCopy(cards[layer.frame] as Card, layer.frame)}
          </Layer>
        ))}
      </div>

      {/* below 1025 px: tap zones, Back on the left 25% and Next on the right 75% */}
      <button type="button" className={classes(styles.tap, styles.tapBack)} aria-label="Back" onClick={stage.onBack} />
      <button type="button" className={classes(styles.tap, styles.tapNext)} aria-label="Next" onClick={stage.onTap} />
      {/* 1025 px and wider: arrow buttons at the window's edges */}
      <button type="button" className={classes(styles.arrow, styles.arrowBack)} aria-label="Back" onClick={stage.onBack} />
      <button type="button" className={classes(styles.arrow, styles.arrowNext)} aria-label="Next" onClick={stage.onTap} />
    </div>
  )
}

function Layer({ layer, withIcon, children }: { layer: CopyLayer; withIcon: boolean; children: ReactNode }) {
  const style = layer.delayMs === null ? undefined : ({ '--yig-delay': `${layer.delayMs}ms` } as CSSProperties)
  const motion = classes(
    layer.phase === 'in' && 'yig-in',
    layer.phase === 'out' && 'yig-out',
    layer.quick && 'yig-quick',
    layer.afterIcon && 'yig-after-icon',
    layer.back && 'yig-back',
  )
  if (layer.kind === 'icon') {
    return (
      <div className={classes('yig-icon', motion, styles.icon)} style={style}>
        <span className="yig-pop">{children}</span>
      </div>
    )
  }
  return (
    <div className={classes('yig-text', motion, styles.copy, withIcon && styles.copyBelowIcon)} style={style}>
      {children}
    </div>
  )
}
