// frontend/polyphonic.js

const params = new URLSearchParams(window.location.search);
const filename = params.get("file");

const status = document.getElementById("status");
const stemsDiv = document.getElementById("stems");

document.getElementById("analyzeBtn").onclick = async () => {
    if (!filename) {
        status.innerHTML = "❌ No file provided";
        return;
    }

    status.innerHTML = "🎚 Separating stems...";

    try {
        const res = await fetch(
            `http://127.0.0.1:8000/analyze/polyphonic/?filename=${filename}`,
            { method: "POST" }
        );

        if (!res.ok) throw new Error(await res.text());
        const result = await res.json();

        status.innerHTML = "✅ Separation complete";

        stemsDiv.innerHTML = "";
        for (let [name, url] of Object.entries(result.stems)) {
            const insts = result.instruments[name] || [];
            let instHTML = insts.length
                ? insts.map(i =>
                    `${i.instrument} (${(i.confidence * 100).toFixed(0)}%)`
                  ).join(", ")
                : "Unknown";

            stemsDiv.innerHTML += `
                <div style="margin-bottom:20px;padding:15px;
                            background:white;border-radius:8px;
                            box-shadow:0 3px 10px rgba(0,0,0,0.1);">
                    <strong>${name.toUpperCase()}</strong><br>
                    <em>${instHTML}</em><br><br>
                    <audio controls
                           src="http://127.0.0.1:8000${url}"
                           style="width:100%;"></audio>
                </div>
            `;
        }

    } catch (err) {
        console.error(err);
        status.innerHTML = `❌ Error: ${err.message}`;
    }
};
