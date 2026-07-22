(() => {
    // Detect the current URL prefix dynamically from Galaxy's runtime config
    var rootPrefix = Galaxy.root || "";

    // Create or target the favicon link elements
    var faviconUrl = rootPrefix + "static/favicon.ico";

    // Inject or overwrite the icon links in the true main document <head>
    ['icon', 'shortcut icon'].forEach(function(rel) {
        var link = document.querySelector("link[rel='" + rel + "']") || document.createElement('link');
        link.type = 'image/x-icon';
        link.rel = rel;
        link.href = faviconUrl;
        document.getElementsByTagName('head')[0].appendChild(link);
    });
})();
