var map = L.map("map").setView([10.795376, 106.661339], 12);
HOST = "http://localhost:5000";

var tileLayer = L.tileLayer(
	"https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
	{
		maxZoom: 19,
		attribution:
			'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
	}
);

var locationsDataList = [];

function loadJSONData() {
	const jsonPath = "/tree/main/docs/assets/locations.json";

	fetch(jsonPath)
		.then((response) => {
			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}
			return response.json();
		})
		.then((data) => {
			var locationsData = data;

			locationsData.forEach((location) => {
				var marker = L.marker([
					location.coordinates.lat,
					location.coordinates.lng,
				]).addTo(map);

				locationsDataList.push(location);
				marker.bindPopup(`
                    ${location.name} 
                    <br>
                    <button class="marker-button" data-name="${location.name}">
                        Dự đoán
                    </button>
                `);

				marker.on("popupopen", function () {
					const popupElement = document.querySelector(
						`.marker-button[data-name="${location.name}"]`
					);

					if (popupElement) {
						popupElement.addEventListener("click", function () {
							handleButtonClick(
								location.name,
								location.coordinates.lat,
								location.coordinates.lng,
								marker
							);
						});
					}
				});
			});
		})
		.catch((error) => console.error("Error loading JSON data:", error));
}

function handleButtonClick(name, lat, lng, marker) {
	console.log(`Button clicked for location: ${name}`);

	const globalLoader = document.getElementById("globalLoader");
	globalLoader.style.display = "flex";

	callAPI(lat, lng, (response) => {
		globalLoader.style.display = "none";
		console.log(`API response for location ${name}:`, response);

		var alert = "";
		if (response > 40) {
			alert = "Nhanh vl, đi đường này đi";
		} else {
			alert = "Đang bị kẹt xe đừng có đi";
		}

		marker.setPopupContent(`
            ${name}
            <br>
			Tốc độ hiện tại là: <strong>${response} km/h</strong>
			<br>
            <strong>${alert}</strong>
        `);
		marker.openPopup();
	});
}

function callAPI(lat, lng, callback) {
	fetch(HOST + "/predict", {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify({ location: { lat, lng } }),
	})
		.then((response) => response.json())
		.then((data) => {
			callback(data.Current); // Pass response data to the callback
		})
		.catch((error) => {
			console.error("Error fetching data:", error);
			callback({ result: "Error fetching data" });
		});
}

function initializeMap() {
	tileLayer.addTo(map);
	setTimeout(() => {
		map.invalidateSize();
	}, 0);
	loadJSONData();
}
