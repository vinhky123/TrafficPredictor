var map = L.map("map").setView([10.795376, 106.661339], 12);
HOST = "http://172.16.0.69:5000";

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
                        Theo dõi tình hình và dự đoán
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

		current = response.Current;
		predict = response.Predict;

		let content = "";
		if (response) {
			console.log(response);
			if (current > 25) {
				content = `
                    <br>
                    Tốc độ trung bình hiện tại là: <strong>${current} km/h</strong>
                    <br>
                    <strong style="color: #169325;">Nhanh, có vẻ không kẹt lắm</strong>
					<br>
                `;
			} else {
				content = `
                    <br>
                    Tốc độ trung bình hiện tại là: <strong>${current} km/h</strong>
                    <br>
                    <strong style="color: #c93c3c;">Chậm, đường khá đông!</strong>
					<br>
                `;
			}

			const first10 = predict.slice(0, 2);     // 10 phút đầu tiên
			const next10 = predict.slice(2, 4);     // 10-20 phút
			const next20 = predict.slice(4, 8);     // 20-40 phút
			const next40 = predict.slice(8, 12);  // 40-60 phút
		
			const averageSpeed = (arr) => arr.reduce((sum, val) => sum + val, 0) / arr.length;
		
			// Hàm xác định trạng thái giao thông
			const status = (avgSpeed) => {
				if (avgSpeed < 15) 
					return "<strong style='color: #c93c3c'>sẽ kẹt xe!</strong>";
				if (avgSpeed < 25) 
				return "<strong style='color: #FF8C00'>sẽ đông</strong>";
				return "<strong style='color: #169325'>sẽ thoáng</strong>";
			};
		
			// Xác định trạng thái từng khoảng
			const first10Status = status(averageSpeed(first10));
			const next10Status = status(averageSpeed(next10));
			const next20Status = status(averageSpeed(next20));
			const next40Status = status(averageSpeed(next40));
			
			content += `
			        10 phút tới ${first10Status}, trung bình ${Math.round(averageSpeed(first10))} km/h </strong>
					<br>
					10-20 phút tới ${next10Status}, trung bình ${Math.round(averageSpeed(next10))} km/h </strong>
					<br>
					20-40 phút tới ${next20Status}, trung bình ${Math.round(averageSpeed(next20))} km/h </strong>
					<br>
					40-60 phút tới ${next40Status}, trung bình ${Math.round(averageSpeed(next40))} km/h </strong>
			`;

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
	fetch(HOST + "/predict", {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify({ location: { lat, lng } }),
	})
		.then((response) => response.json())
		.then((data) => {
			callback(data); // Pass response data to the callback
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
