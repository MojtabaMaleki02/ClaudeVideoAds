// Zing, rendered from Clipzing's own mascot rig (shortn-fe/components/mascot). Nothing is redrawn: a pose is data
// (brows, lids, pupils, mouth, arm reach, act, props), exactly as the product animates him.
// URL: harness.html?e=zing&w=900&h=900#<pose>   (POSES below, or any MOODS name)
import { useState } from 'react'
import { createRoot } from 'react-dom/client'
import { flushSync } from 'react-dom'
import { Zing } from '@/components/mascot/Zing'
import { MOODS, type MoodSpec } from '@/components/mascot/moods'
import { PROPS } from '@/components/mascot/scenes'

type Pose = { mood: MoodSpec; scene?: Record<string, readonly unknown[]> }
const m = (base: keyof typeof MOODS, name: string, extra: Partial<MoodSpec> = {}): MoodSpec =>
  ({ ...(MOODS[base] as MoodSpec), name, ...extra }) as MoodSpec

// The ad pose library. Gaze is fixed (no cursor follow); every loop sits on the rig's 4.2 s beat.
export const POSES: Record<string, Pose> = {
  // ── neutral / presenting ──
  idle: { mood: m('happy', 'idle', { gaze: [0, 0] }) },
  talk: { mood: m('happy', 'talk', { act: 'talk', gaze: [0, 0] }) },
  nod: { mood: m('happy', 'nod', { act: 'nod', gaze: [0, 0] }) },
  look_left: { mood: m('happy', 'look_left', { gaze: [-7, 0] }) },
  look_right: { mood: m('happy', 'look_right', { gaze: [7, 0] }) },
  look_down: { mood: m('happy', 'look_down', { gaze: [0, 6] }) },
  present_right: { mood: m('happy', 'present_right', { hr: [205, 120], tilt: -2, gaze: [5, 0] }) },
  present_left: { mood: m('happy', 'present_left', { hl: [15, 120], tilt: 2, gaze: [-5, 0] }) },
  wave: { mood: m('wave', 'wave', { gaze: [0, 0] }) },
  // ── the hook / hero moments ──
  slam: { mood: m('celebrate', 'slam', { arc: 0, lidU: [0, 0], lidL: 0, brow: [-10, -4], eye: 1.2, pupil: 0.85, mouth: 'o', mouthScale: 1.4, act: 'still', gaze: [0, 0] }) },
  land: { mood: m('happy', 'land', { brow: [4, 8], mouth: 'grin', act: 'still', gaze: [0, 0] }) },
  hop: { mood: m('happy', 'hop', { act: 'still', gaze: [-6, -2] }) },
  cheer: { mood: m('celebrate', 'cheer', { mouth: 'grin', gaze: [0, 0] }) },
  celebrate: { mood: m('celebrate', 'celebrate', { gaze: [0, 0] }) },
  joy: { mood: m('joy', 'joy', { act: 'bounce' }) },
  starstruck: { mood: m('starstruck', 'starstruck') },
  love: { mood: m('love', 'love') },
  wink: { mood: m('wink', 'wink', { gaze: [0, 0] }) },
  smug: { mood: m('smug', 'smug') },
  surprised: { mood: m('surprised', 'surprised', { gaze: [0, 0] }) },
  // ── work (determined, never cute over serious narration) ──
  determined: { mood: m('happy', 'determined', { brow: [5, 12], lidU: [7, 6], lidL: 5, pupil: 0.92, mouth: 'flat', gaze: [0, 0], act: 'still' }) },
  determined_talk: { mood: m('happy', 'determined_talk', { brow: [5, 12], lidU: [7, 6], lidL: 5, pupil: 0.92, mouth: 'open', gaze: [0, 0], act: 'talk' }) },
  focused: { mood: m('focused', 'focused', { gaze: [0, 4] }) },
  typing: { mood: m('focused', 'typing', { act: 'tap', gaze: [0, 5] }) },
  think: { mood: m('think', 'think') },
  scan: { mood: m('happy', 'scan', { act: 'scan', brow: [2, 6] }) },
  // ── the "before" (the pain a creator feels without Clipzing) ──
  tense: { mood: m('tense', 'tense', { gaze: [0, 2] }) },
  sleepy: { mood: m('sleepy', 'sleepy') },
  sad: { mood: m('sad', 'sad') },
  ashamed: { mood: m('ashamed', 'ashamed') },
  rage: { mood: m('rage', 'rage', { act: 'mash' }) },
  poker: { mood: m('poker', 'poker') },
  // ── with props (the product's own scene props) ──
  podcast: { mood: m('happy', 'podcast', { act: 'talk', gaze: [0, 0] }), scene: { body: [PROPS.headset], front: [PROPS.studioMic] } },
  podcast_listen: { mood: m('happy', 'podcast_listen', { act: 'nod', gaze: [-4, 0] }), scene: { body: [PROPS.headset], front: [PROPS.studioMic] } },
  gamer: { mood: m('focused', 'gamer', { act: 'mash' }), scene: { body: [PROPS.headset], held: [PROPS.controller] } },
  boss: { mood: m('smug', 'boss', { gaze: [0, 0] }), scene: { face: [PROPS.shades] } },
  // ── blinks (single frames, for hand-placed blinks) ──
  blink1: { mood: m('happy', 'blink1', { lidU: [13, 0], act: 'still', gaze: [0, 0] }) },
  blink2: { mood: m('happy', 'blink2', { lidU: [26, 0], lidL: 4, act: 'still', gaze: [0, 0] }) },
}

const name = decodeURIComponent(location.hash.slice(1) || 'idle')
const q = new URLSearchParams(location.search)
const W = Number(q.get('w') || 900)
function App() {
  const [, setT] = useState(0)
  ;(window as unknown as { __setT: (x: number) => void }).__setT = (x: number) => flushSync(() => setT(x))
  const pose = POSES[name] ?? { mood: { ...(MOODS as Record<string, MoodSpec>)[name], name } as MoodSpec }
  return (
    <div style={{ width: W, height: W, display: 'grid', placeItems: 'center' }}>
      {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
      <Zing size={Math.round(W * 0.9)} mood={pose.mood} scene={pose.scene as any} shadow={false} />
    </div>
  )
}
;(window as unknown as { __POSES: string[] }).__POSES = Object.keys(POSES)
createRoot(document.getElementById('root')!).render(<App />)
;(window as unknown as { __READY: boolean }).__READY = true
