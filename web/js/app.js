document.getElementById("enterApp").addEventListener("click", function () {
	const welcomePage = document.getElementById("welcomePage");
	const mainPage = document.getElementById("mainPage");

	welcomePage.classList.add("fade-out");

	setTimeout(() => {
		welcomePage.style.display = "none";
		mainPage.style.display = "block";
		mainPage.classList.add("fade-in");
		console.log("Welcome to the app");
		initializeMap();
	}, 300);
});
