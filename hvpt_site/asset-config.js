(function () {
  const VERSION = "20260705-cdn";
  const CDN_BASE = "https://cdn.jsdelivr.net/gh/RIKKA-ZZZ/jlpt-hvpt-trainer@main/hvpt_site/";
  const LOCAL_HOSTS = new Set(["", "localhost", "127.0.0.1", "::1"]);
  const params = new URLSearchParams(window.location.search);
  const forced = params.get("cdn");
  const isLocal = window.location.protocol === "file:" || LOCAL_HOSTS.has(window.location.hostname);
  const useCdn = forced === "1" || (forced !== "0" && !isLocal);

  function hasProtocol(path) {
    return /^(?:[a-z]+:)?\/\//i.test(path) || /^(?:data|blob):/i.test(path);
  }

  function encodePath(path) {
    return path
      .split("/")
      .map((part) => encodeURIComponent(part))
      .join("/");
  }

  function appendVersion(url, version) {
    if (!version) return url;
    const separator = url.includes("?") ? "&" : "?";
    return `${url}${separator}v=${encodeURIComponent(version)}`;
  }

  function assetUrl(path, options) {
    if (!path || hasProtocol(path)) return path;
    const opts = options || {};
    const cleanPath = String(path).replace(/\\/g, "/").replace(/^\.\//, "");
    const shouldUseCdn = opts.cdn !== false && (opts.cdn === true || useCdn) && /^(assets|data)\//.test(cleanPath);
    const base = shouldUseCdn ? CDN_BASE : "";
    const resolvedPath = shouldUseCdn ? encodePath(cleanPath) : cleanPath;
    const version = opts.version === undefined ? VERSION : opts.version;
    return appendVersion(`${base}${resolvedPath}`, version);
  }

  window.HVPT_ASSET_CONFIG = {
    cdnBase: CDN_BASE,
    useCdn,
    version: VERSION,
  };
  window.hvptAssetUrl = assetUrl;
})();
