# Year in Games 2026: card creator

A prototype for building the recap cards. You give it a **payload** (a player's stats) and a **card JSON** (which styles, in what order), and it draws the card.

## Open it

Double-click `configurator.html`. There is nothing to install and no server to run; it works from disk in any current browser.

Keep the folder together: the page loads the other files and the `icons/` and `ui-icons/` folders next to it.

## What's on the page

- **Lines in this card** (top left): change a line's style, edit its text, drag the grip to reorder, remove it, or add a line.
- **Available styles** (below it): every style a line can use, with an example.
- **Sample card** (right): edit the text right on the card. Shift+Enter adds a line break.
- **Payload** and **Card JSON** (below the sample): the two boxes the card is drawn from. Edit either one; the card updates as you type.
- **Saved recipes**: save the current Card JSON under a name, load or delete it later. Recipes are stored in your own browser. **Export recipes** downloads them as a file and **Import recipes** loads a file, which is how to share them.

## How it fits together

```
payload box + card JSON box  ->  renderCard()  ->  the card
```

| File | What it does |
|---|---|
| `configurator.html` | The page |
| `configurator.js` | The page's behavior: the boxes, lines panel, editing on the card, saved recipes |
| `renderer.js` | Turns card JSON plus a payload into a card. Knows nothing about the page |
| `sample-data.js` | Example payloads and the starting card |
| `styles.css` | Design tokens, the page, and one section per card style |
| `fonts/` | The Karnak and Franklin font files, loaded by `styles.css` |
| `icons/` | The seven game icons, from Figma |
| `ui-icons/` | Small icons for the page's controls |

To add a card style: write a renderer in `renderer.js`, add its CSS in `styles.css`, and add a row to `STYLES` in `configurator.js`.

## Card JSON

A card is a list of lines. Each line is one `style: value` pair. Text styles take the words, and `{placeholders}` are filled in from the payload.

```json
{
  "lines": [
    { "headline": "You played a streak of" },
    { "game-icon": "{streak.game}" },
    { "display": "{streak.days} days" },
    { "label-bold": "of {streak.game}" }
  ]
}
```

A placeholder that isn't in the payload shows as blank. Line styles: `headline`, `headline-strong`, `display`, `stat`, `body`, `label`, `label-bold`, `game-icon`, `spacer`, `wordle-grid`, `connections-color`, `games-chart`, `none`. Spacers take a Playbook spacing token (`"2"` is 16px).

## Things to know

- The NYT fonts are included in `fonts/` (Karnak Medium, Semibold and Bold; Franklin Light, Medium, Semibold and Bold), so the page looks the same on any machine. They are licensed NYT typefaces; use them under that license. If a file fails to load, the page falls back to Georgia and Helvetica.
- There is no Franklin Book (400) file. The `label` style is set at 400, so it shows in Franklin Light.
- Payloads, numbers and copy in `sample-data.js` are made up for the prototype.
- Sizes and colors marked `[figma]` in `styles.css` were read from the YIG Prototype and Playbook Figma files; `[provisional]` ones are guesses.
