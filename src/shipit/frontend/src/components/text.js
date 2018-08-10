/**
 * Shorten text if it is too long.
 */
export default function maybeShorten(str, length = 70) {
  if (str.length > length) {
    const reduced = str.substring(0, length - 4);
    return `${reduced} ...`;
  }
  return str;
}
