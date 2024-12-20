var map = L.map("map").setView([10.795376, 106.661339], 12);
HOST = "https://vinhkyyy.duckdns.org/";

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
	const jsonPath = "assets/locations.json";

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
                        Theo dõi tình hình
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
	const globalLoader = document.getElementById("globalLoader");
	globalLoader.style.display = "flex";

	callAPI(lat, lng, (response) => {
		globalLoader.style.display = "none";

		let content = "";
		if (response && typeof response === "number") {
			if (response > 30) {
				content = `
                    <br>
                    Tốc độ trung bình hiện tại là: <strong>${response} km/h</strong>
                    <br>
                    <strong style="color: #169325;">Nhanh, có vẻ không kẹt lắm</strong>
                `;
			} else {
				content = `
                    <br>
                    Tốc độ trung bình hiện tại là: <strong>${response} km/h</strong>
                    <br>
                    <strong style="color: #c93c3c;">Chậm, đừng đi đường này, kẹt rồi!</strong>
                `;
			}
		} else {
			content = `
                <br>
                <strong style="color: #c93c3c;">Không thể lấy dữ liệu, vui lòng thử lại sau!</strong>
            `;
		}

		marker.setPopupContent(`${name} ${content}`);
		marker.openPopup();
	});
}

function callAPI(lat, lng, callback) {
	fetch(HOST + "/current", {
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
