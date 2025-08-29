(() => {
	let slurmWebhookLoaded = false;

	// Function to monitor click outside menu
	function outsideClickListener(event) {
		const menu = document.getElementById("slurm-menu");
		if(!menu.contains(event.target)){
			closeMenu();
		}


	}


	// Function to display menu
	function showMenu() {
		const menu = document.getElementById("slurm-menu");
		if (menu && menu.style.display !== "block") {
			menu.style.display = "block";
			setTimeout(() => {
				document.addEventListener("click", outsideClickListener, true);
			}, 0);
			// For iframe
			const iframe = document.getElementById("frame");
			if (iframe) {
				iframeClickListener = () => closeMenu();
				iframe.contentWindow.document.addEventListener("click", iframeClickListener);
			}

		 }
	}

	// Function to close menu
	function closeMenu() {
		const menu = document.getElementById("slurm-menu");
		if (menu) {
			console.log("Closing menu")
			menu.style.display = "none";
			document.removeEventListener("click", outsideClickListener, true);
			// For iframe
			const iframe = document.getElementById("frame");
			if (iframe) {
				iframe.contentWindow.document.removeEventListener("click", iframeClickListener);
			}
		}
	}

	// Function for showing update message
	function showMessage() {
		const msg = document.createElement("div");
		msg.id = "slurm-message"
		msg.textContent = "Slurm parameters updated.";
		document.body.appendChild(msg);
		setTimeout(() => {
			msg.style.opacity = "0";
			setTimeout(() => {
				msg.remove();
			}, 1000); // In line with CSS timer
		}, 3000);


	}


	function createMenu() {
		// Create the menu container
		const menu = document.createElement("div");
		menu.id = "slurm-menu";

		// Position the menu based on the element's position
		const rect = document.querySelector("#slurm a").getBoundingClientRect();
		menu.style.top = rect.bottom + window.scrollY + "px";
		menu.style.left = rect.left + window.scrollX + "px";

		// Create the list of items
		const itemList = document.createElement("ul");

		const coreItem = document.createElement("li");
		const coreLabel = document.createElement("label");
		coreLabel.textContent = "Amount of cores";
		const coreValue = document.createElement("input");
		coreValue.type = "text";
		coreValue.placeholder = "2";

		coreItem.appendChild(coreLabel);
		coreItem.appendChild(coreValue);



		const memItem = document.createElement("li");
		const memLabel = document.createElement("label");
		memLabel.textContent = "Memory in MBs";
		const memValue = document.createElement("input");
		memValue.type = "text";
		memValue.placeholder = "2096";


		memItem.appendChild(memLabel);
		memItem.appendChild(memValue);


		const timeItem = document.createElement("li");
		const timeLabel = document.createElement("label");
		timeLabel.textContent = "Job runtime";
		const timeValue = document.createElement("input");
		timeValue.type = "text";
		timeValue.placeholder = "0-00:00:00";

		timeItem.appendChild(timeLabel);
		timeItem.appendChild(timeValue);


		const partitionItem = document.createElement("li");
		const partitionsAvil = document.createElement("select");
		const partitionsLabel = document.createElement("label");
		partitionsLabel.textContent = "Partitions"
		partitionItem.appendChild(partitionsLabel);
		partitionItem.appendChild(partitionsAvil);
		$.getJSON(Galaxy.root + "api/webhooks/slurm/data?getPartitions=true", function(data) {
			partitions = data.partitions;
			partitions.forEach(item => {
				const option = document.createElement("option");
				option.value = item;
				option.textContent = item;
				partitionsAvil.appendChild(option);
			});
		});


		const slurmItem = document.createElement("li");
		const slurmLabel = document.createElement("label");
		slurmLabel.textContent = "Additional Slurm Arguments";
		const slurmValue = document.createElement("input");
		slurmValue.type = "text";
		slurmValue.placeholder = "--gres=gpu:1";

		slurmItem.appendChild(slurmLabel);
		slurmItem.appendChild(slurmValue);


		const submitItem = document.createElement("li");
		const submitButton = document.createElement("button");
		submitButton.textContent = "Submit";


		submitButton.addEventListener("click", () => {
			const queryString = [
				"cores=" + encodeURIComponent(coreValue.value),
				"memory=" + encodeURIComponent(memValue.value),
				"runtime=" + encodeURIComponent(timeValue.value),
				"partition=" + encodeURIComponent(partitionsAvil.value),
				"args=" + encodeURIComponent(slurmValue.value)
			].join("&");

			const url = Galaxy.root + "api/webhooks/slurm/data?" + queryString;
			$.getJSON(url, function(data) {
					showMessage();
					closeMenu();
				});

			});


		submitItem.appendChild(submitButton);


		itemList.appendChild(coreItem);
		itemList.appendChild(memItem);
		itemList.appendChild(timeItem);
		itemList.appendChild(partitionItem);
		itemList.appendChild(slurmItem);
		itemList.appendChild(submitItem);

		// Append the item list to the menu container
		menu.appendChild(itemList);

		// Append the menu to the body
		document.body.appendChild(menu);

		slurmWebhookLoaded = true;


	}

	function elementReady(selector) {
		return new Promise((resolve, reject) => {
		    let el = document.querySelector(selector);
		    if (el) {
			resolve(el);
		    }
		    new MutationObserver((mutationRecords, observer) => {
			// Query for elements matching the specified selector
			Array.from(document.querySelectorAll(selector)).forEach((element) => {
			    resolve(element);
			    //Once we have resolved we don't need the observer anymore.
			    observer.disconnect();
			});
		    }).observe(document.documentElement, {
			childList: true,
			subtree: true,
		    });
		});
	}

	elementReady("#slurm a").then((el) => {
		// External stuff may also have attached a click handler here (vue-based masthead)
		// replace with a clean copy of the node to remove all that cruft.
		clean = el.cloneNode(true);
		el.parentNode.replaceChild(clean, el);
		clean.addEventListener("click", (e) => {
		    e.preventDefault();
		    e.stopPropagation();
		    if (!slurmWebhookLoaded) {
			console.log("Creating menu...");
			createMenu();
			showMenu();
		    } else {
			console.log("Showing menu...")
			showMenu();
		    }
		});
	});


})();
