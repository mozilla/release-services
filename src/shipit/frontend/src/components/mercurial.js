/**
 * Get latest mercurial pushes.
 */
export async function getPushes(repo) {
  const url = `${repo}/json-pushes?version=2&full=1&tipsonly=1`;
  const req = await fetch(url);
  return req.json();
}

function buildUrl(repo, revision, appName, productKey) {
  const urlParts = [`${repo}/raw-file/${revision}`];
  if (productKey && productKey.startsWith('fennec_')) {
    urlParts.push('mobile/android/config/version-files');

    if (productKey === 'fennec_beta') {
      urlParts.push('beta');
    } else if (productKey === 'fennec_release') {
      urlParts.push('release');
    } else {
      throw new Error(`Unsupported productKey: ${productKey}`);
    }
  } else {
    urlParts.push(appName);
  }
  urlParts.push('version_display.txt');
  return urlParts.join('/');
}

/**
 * Get in-tree product "display" version.
 */
export async function getVersion(repo, revision, appName, productKey) {
  const url = buildUrl(repo, revision, appName, productKey);
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
