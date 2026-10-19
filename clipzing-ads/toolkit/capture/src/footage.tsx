// "Footage" for the phones in an ad: Zing's own podcast and the landing page's drawn scenes
// (shortn-fe/components/landing/story/footage.tsx). No real people, ever: the landing's showcase clips show
// celebrities and must never appear in an ad.
// URL: harness.html?e=footage&w=720&h=1280#<scene>
import { useState } from 'react'
import { createRoot } from 'react-dom/client'
import { flushSync } from 'react-dom'
import { MOODS, type MoodSpec } from '@/components/mascot/moods'
import { CloseUp, Coffee, Rocket, WideShot } from '@/components/landing/story/footage'

const talk = { ...MOODS.happy, name: 'talk', act: 'talk' } as MoodSpec
const joy = { ...MOODS.celebrate, name: 'joy', act: 'talk' } as MoodSpec
const serious = { ...MOODS.happy, name: 'serious', brow: [4, 9], mouth: 'open', act: 'talk', gaze: [0, 0] } as MoodSpec
const laugh = { ...MOODS.joy, name: 'laugh', act: 'bounce' } as MoodSpec

const SCENES: Record<string, () => JSX.Element> = {
  closeup: () => <CloseUp mood={talk} animated sign={false} />,                                          // talking to camera
  closeup_onair: () => <CloseUp mood={joy} animated star="left-[-22cqw] top-[30cqw] [--s:140cqw]" />,   // tighter, ON AIR sign, laughing
  closeup_serious: () => <CloseUp mood={serious} animated sign={false} star="left-[-18cqw] top-[33cqw] [--s:134cqw]" />,
  closeup_laugh: () => <CloseUp mood={laugh} animated />,
  wide: () => <WideShot mood={talk} animated />,                                                         // 16:9-ish source recording
  coffee: () => <Coffee />,
  rocket: () => <Rocket />,
}
const name = decodeURIComponent(location.hash.slice(1) || 'closeup')
const q = new URLSearchParams(location.search)
function App() {
  const [, setT] = useState(0)
  ;(window as unknown as { __setT: (x: number) => void }).__setT = (x: number) => flushSync(() => setT(x))
  const Scene = SCENES[name]
  return (
    <div style={{ width: Number(q.get('w') || 720), height: Number(q.get('h') || 1280), position: 'relative', overflow: 'hidden', background: '#0b0817', containerType: 'inline-size' }}>
      <Scene />
    </div>
  )
}
;(window as unknown as { __POSES: string[] }).__POSES = Object.keys(SCENES)
createRoot(document.getElementById('root')!).render(<App />)
;(window as unknown as { __READY: boolean }).__READY = true
