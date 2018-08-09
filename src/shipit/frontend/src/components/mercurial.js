/**
 * Get latest mercurial pushes.
 */
export async function getPushes(repo) {
  const url = `${repo}/json-pushes?version=2&full=1&tipsonly=1`;
  const req = await fetch(url);
  return req.json();
}

/**
 * Get in-tree product "display" version.
 */
export async function getVersion(repo, revision, appName) {
  const url = `${repo}/raw-file/${revision}/${appName}/config/version_display.txt`;
  const res = await fetch(url);
  if (res.ok) {
    const version = await res.text();
    return version.trim();
  }
  return '';
}

/**
 * Get in-tree "shipped" locales.
 */
export async function getLocales(repo, revision, appName) {
  const url = `${repo}/raw-file/${revision}/${appName}/locales/l10n-changesets.json`;
  const res = await fetch(url);
  const locales = await res.json();
  return Object.keys(locales);
}
