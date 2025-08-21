;(function () {
  const root = document.documentElement
  const KEY = 'theme'
  function setTheme (t) { root.setAttribute('data-theme', t) }
  function getTheme () { return localStorage.getItem(KEY) || 'light' }
  setTheme(getTheme())
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('#theme-toggle')
    if (!btn) return
    const next = getTheme() === 'light' ? 'dark' : 'light'
    localStorage.setItem(KEY, next)
    setTheme(next)
  })
})()