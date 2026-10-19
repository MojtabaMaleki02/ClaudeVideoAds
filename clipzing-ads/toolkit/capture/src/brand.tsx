// Brand marks exactly as the site draws them: the navbar lock-up (logo-sidebar.svg + "Clipzing", Plus Jakarta Sans
// 700, #A855F7 → #9333EA), a white single-colour version, and the icon alone.
// URL: harness.html?e=brand&w=1400&h=520#wordmark | wordmark-white | icon
import { createRoot } from 'react-dom/client'

const variant = location.hash.slice(1) || 'wordmark'
function App() {
  const text: React.CSSProperties =
    variant === 'wordmark-white'
      ? { color: '#ffffff' }
      : { background: 'linear-gradient(90deg,#A855F7,#9333EA)', WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent' }
  return (
    <div id="mark" style={{ display: 'inline-flex', alignItems: 'center', padding: '0 40px 0 0' }}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="/logo-sidebar.svg" alt="" style={{ width: 448, height: 448 }} />
      {variant !== 'icon' && <span style={{ font: "700 144px/1 'Plus Jakarta Sans'", paddingBottom: 12, ...text }}>Clipzing</span>}
    </div>
  )
}
createRoot(document.getElementById('root')!).render(<App />)
// the harness's virtual clock owns setTimeout; wait on the real one
document.fonts.ready.then(() => (window as unknown as { __realSetTimeout: typeof setTimeout }).__realSetTimeout(() => { (window as unknown as { __READY: boolean }).__READY = true }, 400))
;(window as unknown as { __setT: (x: number) => void }).__setT = () => {}
