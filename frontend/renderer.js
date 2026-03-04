// frontend/renderer.js

let uploadedFileName = null;
let detectedType = null;

document.getElementById("uploadBtn").onclick = async () => {
    const fileInput = document.getElementById("audioFile");
    const status = document.getElementById("status");
    const stemsDiv = document.getElementById("stems");

    if (!fileInput.files.length) {
        alert("Select a song first");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    // UI: detecting type only
    status.innerHTML = `
        <span>🔍 Detecting audio type...</span>
        <div style="margin-top: 10px;">
            <div style="width:100%;background:#ddd;border-radius:10px;overflow:hidden;">
                <div id="progressBar"
                     style="width:0%;height:18px;
                     background:linear-gradient(90deg,#4CAF50,#45a049);
                     transition:width 0.3s;"></div>
            </div>
        </div>
    `;
    stemsDiv.innerHTML = "";

    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += 5;
        if (progress <= 90) {
            const bar = document.getElementById("progressBar");
            if (bar) bar.style.width = progress + "%";
        }
    }, 200);

    try {
        const res = await fetch("http://127.0.0.1:8000/upload/", {
            method: "POST",
            body: formData
        });

        clearInterval(progressInterval);
        document.getElementById("progressBar").style.width = "100%";

        if (!res.ok) {
            throw new Error(await res.text());
        }

        const result = await res.json();
        console.log("[DEBUG] Upload response:", result);

        uploadedFileName = result.filename;
        detectedType = result.type;

        status.innerHTML = `
            <h3>✅ Audio Type Detected</h3>
            <p>
                <strong>Type:</strong> ${result.type}<br>
                <strong>Confidence:</strong> ${(result.confidence * 100).toFixed(1)}%
            </p>
            <button id="goDeepBtn"
                style="padding:12px 25px;
                       background:#764ba2;
                       color:white;
                       border:none;
                       border-radius:8px;
                       font-size:16px;
                       cursor:pointer;">
                ➡ Go Deeper
            </button>
        `;

        document.getElementById("goDeepBtn").onclick = () => {
            if (!uploadedFileName) return;

            if (detectedType === "monophonic") {
                window.location.href =
                    `monophonic.html?file=${encodeURIComponent(uploadedFileName)}`;
            } else {
                window.location.href =
                    `polyphonic.html?file=${encodeURIComponent(uploadedFileName)}`;
            }
        };


    } catch (err) {
        clearInterval(progressInterval);
        console.error(err);
        status.innerHTML = `❌ Error: ${err.message}`;
    }
};

// =======================
// MONOPHONIC PIPELINE
// =======================
async function runMonophonicPipeline() {
    const status = document.getElementById("status");
    const stemsDiv = document.getElementById("stems");

    status.innerHTML = "🎼 Running monophonic analysis...";
    stemsDiv.innerHTML = "";

    try {
        const res = await fetch(
            `http://127.0.0.1:8000/analyze/monophonic/?filename=${uploadedFileName}`,
            { method: "POST" }
        );

        if (!res.ok) throw new Error(await res.text());
        const result = await res.json();

        status.innerHTML = `
            <h3>🎵 Monophonic Analysis Complete</h3>
            <p>
                <strong>Instrument:</strong>
                ${result.instrument.instrument}
                (${(result.instrument.confidence * 100).toFixed(0)}%)
            </p>
            <p>
                <strong>Tempo:</strong> ${result.tempo.tempo.toFixed(1)} BPM<br>
                <strong>Key:</strong> ${result.key.key} ${result.key.mode}<br>
                <strong>Time Signature:</strong> ${result.beats_per_measure}/4
            </p>
            <a href="http://127.0.0.1:8000${result.musicxml_file}"
               download
               style="display:inline-block;
                      margin-top:10px;
                      padding:10px 18px;
                      background:#4CAF50;
                      color:white;
                      border-radius:6px;
                      text-decoration:none;">
                ⬇ Download MusicXML
            </a>
        `;

    } catch (err) {
        console.error(err);
        status.innerHTML = `❌ Monophonic analysis failed: ${err.message}`;
    }
}

// =======================
// POLYPHONIC PIPELINE
// =======================
async function runPolyphonicPipeline() {
    const status = document.getElementById("status");
    const stemsDiv = document.getElementById("stems");

    status.innerHTML = "🎚 Separating polyphonic stems...";
    stemsDiv.innerHTML = "";

    try {
        const res = await fetch(
            `http://127.0.0.1:8000/analyze/polyphonic/?filename=${uploadedFileName}`,
            { method: "POST" }
        );

        if (!res.ok) throw new Error(await res.text());
        const result = await res.json();

        status.innerHTML = `<h3>🎼 Polyphonic Analysis Complete</h3>`;
        displayStems(result.stems, result.instruments);

    } catch (err) {
        console.error(err);
        status.innerHTML = `❌ Polyphonic analysis failed: ${err.message}`;
    }
}

// =======================
// STEM DISPLAY (UNCHANGED)
// =======================
function displayStems(stems, instruments) {
    const stemsDiv = document.getElementById("stems");
    stemsDiv.innerHTML = "<h3>🎼 Separated Stems</h3>";

    for (let [name, url] of Object.entries(stems)) {
        const insts = instruments[name] || [];
        let instHTML = insts.length
            ? insts.map(i => `${i.instrument} (${(i.confidence * 100).toFixed(0)}%)`).join(", ")
            : "Unknown";

        stemsDiv.innerHTML += `
            <div style="margin-bottom:20px;
                        padding:15px;
                        background:white;
                        border-radius:8px;
                        box-shadow:0 3px 10px rgba(0,0,0,0.1);">
                <strong>${name.toUpperCase()}</strong><br>
                <em>${instHTML}</em><br><br>
                <audio controls
                       src="http://127.0.0.1:8000${url}"
                       style="width:100%;"></audio>
            </div>
        `;
    }
}
