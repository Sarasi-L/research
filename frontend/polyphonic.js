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

    status.innerHTML = "🎚 Separating stems and analyzing polyphonic audio...";

    try {

        const res = await fetch(
            `http://127.0.0.1:8000/analyze/polyphonic/?filename=${filename}`,
            { method: "POST" }
        );

        if (!res.ok) throw new Error(await res.text());

        const result = await res.json();

        console.log("Polyphonic result:", result);

        status.innerHTML = "✅ Stem separation complete";

        stemsDiv.innerHTML = "";

        // --------------------------------------------------
        // DISPLAY STEMS (same as before)
        // --------------------------------------------------
        for (let [name, url] of Object.entries(result.stems)) {

            const insts = result.instruments[name] || [];

            let instHTML = insts.length
                ? insts.map(i =>
                    `${i.instrument} (${(i.confidence * 100).toFixed(0)}%)`
                  ).join(", ")
                : "Unknown";

            stemsDiv.innerHTML += `
                <div style="
                    margin-bottom:20px;
                    padding:15px;
                    background:white;
                    border-radius:8px;
                    box-shadow:0 3px 10px rgba(0,0,0,0.1);
                ">
                    <strong>${name.toUpperCase()}</strong><br>
                    <em>${instHTML}</em><br><br>

                    <audio controls
                        src="http://127.0.0.1:8000${url}"
                        style="width:100%;">
                    </audio>
                </div>
            `;
        }

        // --------------------------------------------------
        // SHOW NOTATION IF PIANO DETECTED
        // --------------------------------------------------
        if (result.piano_only && result.musicxml_file) {

            status.innerHTML += "<br>🎹 Piano detected — generating notation...";

            const notationDiv = document.createElement("div");

            notationDiv.style.marginTop = "40px";
            notationDiv.style.padding = "20px";
            notationDiv.style.background = "white";
            notationDiv.style.borderRadius = "10px";
            notationDiv.style.boxShadow = "0 4px 15px rgba(0,0,0,0.15)";

            notationDiv.innerHTML = `

                <h3 style="
                    font-size:22px;
                    margin-bottom:15px;
                    color:#333;
                ">
                    🎼 Generated Piano Notation
                </h3>

                <iframe
                    src="https://www.opensheetmusicdisplay.org/demo/?openUrl=http://127.0.0.1:8000${result.musicxml_file}"
                    style="
                        width:100%;
                        height:600px;
                        border:none;
                        background:white;
                    ">
                </iframe>

                <br><br>

                <a href="http://127.0.0.1:8000${result.musicxml_file}"
                   download
                   style="
                        display:inline-block;
                        padding:12px 20px;
                        background:#4CAF50;
                        color:white;
                        border-radius:6px;
                        text-decoration:none;
                        font-weight:bold;
                   ">
                   ⬇ Download MusicXML
                </a>

            `;

            stemsDiv.appendChild(notationDiv);
        }

    }
    catch (err) {

        console.error(err);

        status.innerHTML = `❌ Error: ${err.message}`;
    }
};