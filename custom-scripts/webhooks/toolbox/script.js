(() => {
    let reloadWebhookLoaded = false;
    let iframeClickListener = null;
    let pollInterval = null;
    let msgTimeout = null;
    let fadeTimeout = null;

    /**
     * Checks localStorage for ongoing or completed reloads upon page load/refresh.
     */
    function checkPendingNotification() {
        const reloadState = localStorage.getItem("galaxy_toolbox_reload_state");

        if (reloadState === "complete") {
            showMessage("Toolbox reloaded successfully! New tools are now available.", 6000, false);
            localStorage.removeItem("galaxy_toolbox_reload_state");
        } else if (reloadState === "in_progress") {
            showMessage("Toolbox is currently reloading in the background...", 0, false);
            pollReloadStatus();
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", checkPendingNotification);
    } else {
        checkPendingNotification();
    }

    /**
     * Displays a fixed notification message banner at the bottom right of the screen.
     * 
     * @param {string} text - Message content to display.
     * @param {number} duration - Display time in ms (0 = permanent until dismissed/updated).
     * @param {boolean} isRed - Toggles red background state for countdown/errors if true, else default green.
     */
    function showMessage(text, duration = 4000, isRed = false) {
        let msg = document.getElementById("reload-toolbox-message");

        if (!msg) {
            msg = document.createElement("div");
            msg.id = "reload-toolbox-message";
            document.body.appendChild(msg);
        }

        // Clear existing dismissal timeouts to prevent early removal during active updates
        if (msgTimeout) clearTimeout(msgTimeout);
        if (fadeTimeout) clearTimeout(fadeTimeout);

        msg.textContent = text;
        msg.style.opacity = "1";

        // Toggle red alert styling defined in styles.css
        msg.classList.toggle("message-red", isRed);

        if (duration > 0) {
            msgTimeout = setTimeout(() => {
                msg.style.opacity = "0";
                fadeTimeout = setTimeout(() => {
                    if (msg) msg.remove();
                }, 1000);
            }, duration);
        }
    }

    /**
     * Periodically queries the backend status API endpoint to monitor toolbox reload progress.
     */
    function pollReloadStatus() {
        const statusUrl = `${Galaxy.root}api/webhooks/toolbox/data?action=status`;

        if (pollInterval) clearInterval(pollInterval);

        pollInterval = setInterval(() => {
            $.getJSON(statusUrl, function (data) {
                if (data && data.reloading === false) {
                    clearInterval(pollInterval);
                    pollInterval = null;

                    localStorage.setItem("galaxy_toolbox_reload_state", "complete");

                    // Initiate 5-second countdown banner (RED styling active ONLY during countdown)
                    let secondsLeft = 5;

                    const countdownInterval = setInterval(() => {
                        if (secondsLeft > 0) {
                            showMessage(`Toolbox reload complete! Refreshing interface in ${secondsLeft}s...`, 0, true);
                            secondsLeft--;
                        } else {
                            clearInterval(countdownInterval);
                            showMessage("Refreshing interface now...", 0, true);
                            window.location.reload();
                        }
                    }, 1000);

                } else if (data && data.reloading === true) {
                    // Ongoing background re-indexing updates remain green
                    showMessage("Reloading toolbox and rebuilding search index...", 0, false);
                }
            }).fail(function () {
                // Ignore transient network errors during background processing
            });
        }, 3000);
    }

    /**
     * Closes menu when clicking outside the target menu container or masthead button.
     */
    function outsideClickListener(event) {
        const menu = document.getElementById("reload-toolbox-menu");
        const toolboxBtn = event.target.closest("#toolbox, [data-description='toolbox']");

        if (menu && !menu.contains(event.target) && !toolboxBtn) {
            closeMenu();
        }
    }

    /**
     * Dynamically positions the dropdown menu relative to the Masthead button.
     */
    function updatePosition() {
        const menu = document.getElementById("reload-toolbox-menu");
        const targetEl = document.querySelector("#toolbox a") || document.querySelector("#toolbox") || document.querySelector("[data-description='toolbox']");

        if (menu && targetEl) {
            const rect = targetEl.getBoundingClientRect();
            let leftPos = rect.left;

            // Ensure menu remains within viewport bounds on smaller screens
            if (leftPos + 260 > window.innerWidth) {
                leftPos = window.innerWidth - 270;
            }

            menu.style.top = rect.bottom + "px";
            menu.style.left = Math.max(10, leftPos) + "px";
        }
    }

    /**
     * Opens the dropdown menu and attaches global dismissal listeners.
     */
    function showMenu() {
        const menu = document.getElementById("reload-toolbox-menu");
        if (menu) {
            updatePosition();
            menu.style.display = "block";

            setTimeout(() => {
                document.addEventListener("click", outsideClickListener, true);
            }, 0);

            const iframe = document.getElementById("frame");
            if (iframe && iframe.contentWindow) {
                iframeClickListener = () => closeMenu();
                iframe.contentWindow.document.addEventListener("click", iframeClickListener);
            }
        }
    }

    /**
     * Hides the dropdown menu and detaches outside click event listeners.
     */
    function closeMenu() {
        const menu = document.getElementById("reload-toolbox-menu");
        if (menu) {
            menu.style.display = "none";
            document.removeEventListener("click", outsideClickListener, true);
            const iframe = document.getElementById("frame");
            if (iframe && iframe.contentWindow && iframeClickListener) {
                iframe.contentWindow.document.removeEventListener("click", iframeClickListener);
            }
        }
    }

    /**
     * Constructs the menu DOM element and attaches click events to the reload trigger button.
     */
    function createMenu() {
        const menu = document.createElement("div");
        menu.id = "reload-toolbox-menu";

        const contentContainer = document.createElement("div");
        contentContainer.className = "reload-menu-content";

        const infoText = document.createElement("p");
        infoText.className = "reload-info-text";
        infoText.textContent = "The following will reload the Toolbox to include preset tools. This process could take up to 10 minutes.";

        const submitButton = document.createElement("button");
        submitButton.className = "reload-submit-btn";
        submitButton.textContent = "Reload Toolbox";

        submitButton.addEventListener("click", () => {
            submitButton.disabled = true;
            submitButton.textContent = "Reloading...";

            const url = `${Galaxy.root}api/webhooks/toolbox/data?action=reload`;

            $.getJSON(url, function (data) {
                if (data && data.status === "success") {
                    localStorage.setItem("galaxy_toolbox_reload_state", "in_progress");
                    showMessage("Toolbox reload task initiated...", 0, false);
                    pollReloadStatus();
                } else {
                    showMessage("Error: " + ((data && data.message) || "Failed to trigger reload."), 5000, true);
                }
                closeMenu();
                submitButton.disabled = false;
                submitButton.textContent = "Reload Toolbox";
            }).fail(function () {
                showMessage("Failed to communicate with server.", 5000, true);
                closeMenu();
                submitButton.disabled = false;
                submitButton.textContent = "Reload Toolbox";
            });
        });

        contentContainer.appendChild(infoText);
        contentContainer.appendChild(submitButton);
        menu.appendChild(contentContainer);
        document.body.appendChild(menu);

        reloadWebhookLoaded = true;
    }

    /**
     * Global capture-phase listener ensures the dropdown triggers reliably,
     * even if Galaxy re-renders masthead items dynamically.
     */
    document.addEventListener("click", (e) => {
        const toolboxBtn = e.target.closest("#toolbox, [data-description='toolbox']");
        if (toolboxBtn) {
            e.preventDefault();
            e.stopPropagation();

            if (!reloadWebhookLoaded) {
                createMenu();
            }

            const menu = document.getElementById("reload-toolbox-menu");
            if (menu && menu.style.display === "block") {
                closeMenu();
            } else {
                showMenu();
            }
        }
    }, true);
})();
