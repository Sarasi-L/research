const params = new URLSearchParams(window.location.search);
const filename = params.get("file");

const status = document.getElementById("status");
const resultDiv = document.getElementById("result");

document.getElementById("analyzeBtn").onclick = async () => {
    if (!filename) {
        status.innerHTML = "❌ No file provided";
        return;
    }

    status.innerHTML = "🎼 Running monophonic pipeline...";

    try {
        const res = await fetch(
            `http://127.0.0.1:8000/analyze/monophonic/?filename=${filename}`,
            { method: "POST" }
        );

        if (!res.ok) throw new Error(await res.text());
        const result = await res.json();

        status.innerHTML = `
            ✅ Analysis complete<br>
            <strong>Instrument:</strong> ${result.instrument.instrument}<br>
            <strong>Tempo:</strong> ${result.tempo.tempo.toFixed(1)} BPM<br>
            <strong>Key:</strong> ${result.key.key} ${result.key.mode}<br>
            <strong>Time Signature:</strong> ${result.beats_per_measure}/4
        `;

        resultDiv.innerHTML = `
            <a href="http://127.0.0.1:8000${result.musicxml_file}"
               download
               style="display:inline-block;margin-top:15px;
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
        status.innerHTML = `❌ Error: ${err.message}`;
    }
};
