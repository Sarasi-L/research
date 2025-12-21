// frontend/renderer.js
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

    // Show processing
    status.innerHTML = `
        <span>Processing audio...</span>
        <br>
        <small>Analyzing audio type and detecting instruments...</small>
        <div style="margin-top: 10px;">
            <div style="width: 100%; background: #ddd; border-radius: 10px; overflow: hidden;">
                <div id="progressBar" style="width: 0%; height: 20px; background: linear-gradient(90deg, #4CAF50, #45a049); transition: width 0.3s;"></div>
            </div>
        </div>
    `;
    stemsDiv.innerHTML = "";

    // Progress simulation
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += 1;
        if (progress <= 90) {
            const bar = document.getElementById("progressBar");
            if (bar) bar.style.width = progress + "%";
        }
    }, 500);

    try {
        const res = await fetch("http://127.0.0.1:8000/upload/", {
            method: "POST",
            body: formData
        });

        clearInterval(progressInterval);
        const bar = document.getElementById("progressBar");
        if (bar) bar.style.width = "100%";

        if (!res.ok) {
            const errorText = await res.text();
            throw new Error(`HTTP error: ${res.status} - ${errorText}`);
        }

        const result = await res.json();
        console.log("[DEBUG] Full Response:", result);

        const confidenceText = result.confidence?.toFixed(2) || "N/A";
        
        // Check if monophonic or polyphonic
        if (result.is_monophonic) {
            // Monophonic: Show single instrument
            status.innerHTML = `✅ Audio type: <strong>${result.type}</strong>, Confidence: <strong>${confidenceText}</strong>`;
            displayMonophonicResult(result);
        } else {
            // Polyphonic: Show stems
            status.innerHTML = `✅ Audio type: <strong>${result.type}</strong>, Confidence: <strong>${confidenceText}</strong>`;
            displayStems(result.stems, result.instruments);
        }

    } catch (err) {
        clearInterval(progressInterval);
        console.error("[ERROR]", err);
        status.innerHTML = `❌ Error: ${err.message}`;
    }
};

function displayMonophonicResult(result) {
    const stemsDiv = document.getElementById("stems");
    
    stemsDiv.innerHTML = `
        <div style="background: white; padding: 30px; margin: 20px 0; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <h3 style="color: #764ba2; margin: 0 0 20px 0; font-size: 24px;">
                🎵 Monophonic Audio Detected
            </h3>
            
            <div style="background: linear-gradient(135deg, #e7f3ff 0%, #f0e7ff 100%); padding: 20px; border-radius: 12px; margin: 20px 0;">
                <p style="font-size: 16px; color: #555; margin-bottom: 15px;">
                    This audio contains a <strong>single instrument</strong>. No need for stem separation!
                </p>
                
                <div style="background: white; padding: 25px; border-radius: 10px; border-left: 5px solid #667eea;">
                    <div style="font-size: 28px; font-weight: bold; color: #333; margin-bottom: 15px;">
                        🎸 ${result.instrument.instrument.replace(/_/g, ' ').toUpperCase()}
                    </div>
                    
                    <div style="margin: 15px 0;">
                        <span style="background: #4CAF50; color: white; padding: 8px 16px; border-radius: 20px; font-size: 15px; font-weight: bold;">
                            ${(result.instrument.confidence * 100).toFixed(0)}% Confidence
                        </span>
                        <span style="background: #2196F3; color: white; padding: 8px 16px; border-radius: 20px; font-size: 15px; font-weight: bold; margin-left: 10px;">
                            ${result.instrument.category}
                        </span>
                    </div>
                    
                    ${result.instrument.characteristics ? `
                        <div style="margin-top: 20px; padding: 15px; background: #fff3cd; border-radius: 8px; border-left: 3px solid #ffc107;">
                            <strong style="color: #856404;">💡 Characteristics:</strong>
                            <p style="margin: 8px 0 0 0; color: #856404;">${result.instrument.characteristics}</p>
                        </div>
                    ` : ''}
                </div>
            </div>
            
            <div style="margin-top: 25px; padding: 15px; background: #e8f5e9; border-radius: 8px; border-left: 4px solid #4CAF50;">
                <strong style="color: #2e7d32;">ℹ️ Note:</strong>
                <p style="margin: 5px 0 0 0; color: #2e7d32;">
                    Monophonic audio doesn't require stem separation. The entire audio is from this single instrument.
                </p>
            </div>
        </div>
    `;

    /* ===================== ADDED CODE (ONLY THIS PART) ===================== */
    if (result.pitch_data && result.pitch_data.pitch_points) {
        const pitches = result.pitch_data.pitch_points.slice(0, 20);

        let pitchHTML = `
            <div style="margin-top: 25px; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <h4 style="margin-bottom: 15px;">🎼 Extracted Pitch Values (Hz)</h4>
                <table style="width:100%; border-collapse:collapse;">
                    <tr>
                        <th>Time (s)</th>
                        <th>Frequency (Hz)</th>
                        <th>Confidence</th>
                    </tr>
        `;

        for (let p of pitches) {
            pitchHTML += `
                <tr>
                    <td>${p.time.toFixed(2)}</td>
                    <td>${p.frequency.toFixed(1)}</td>
                    <td>${(p.confidence * 100).toFixed(0)}%</td>
                </tr>
            `;
        }

        pitchHTML += `
                </table>
                <p style="font-size:13px;color:#666; margin-top:10px;">
                    Showing first 20 pitch points
                </p>
            </div>
        `;

        stemsDiv.innerHTML += pitchHTML;
    }
    /* ===================== END OF ADDED CODE ===================== */

    /* ===================== ADD NOTE SEGMENTS ===================== */
if (result.note_data && result.note_data.notes) {
    const notes = result.note_data.notes; // array of {start, end, pitch}

    let notesHTML = `
        <div style="margin-top: 25px; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <h4 style="margin-bottom: 15px;">🎶 Detected Notes</h4>
            <table style="width:100%; border-collapse:collapse;">
                <tr>
                    <th>Start (s)</th>
                    <th>End (s)</th>
                    <th>Pitch (Hz)</th>
                </tr>
    `;

    for (let n of notes) {
        notesHTML += `
            <tr>
                <td>${n.start.toFixed(2)}</td>
                <td>${n.end.toFixed(2)}</td>
                <td>${n.pitch.toFixed(2)}</td>
            </tr>
        `;
    }

    notesHTML += `
            </table>
            <p style="font-size:13px;color:#666; margin-top:10px;">
                Showing all detected note segments
            </p>
        </div>
    `;

    stemsDiv.innerHTML += notesHTML;
}
/* ===================== END NOTE SEGMENTS ===================== */

}




function displayStems(stems, instruments) {
    const stemsDiv = document.getElementById("stems");
    stemsDiv.innerHTML = "<h3 style='color: #333; margin: 30px 0 20px 0; font-size: 24px;'>🎼 Separated Stems</h3>";

    console.log("[DEBUG] Displaying stems:", stems);
    console.log("[DEBUG] Instruments data:", instruments);

    for (let [name, url] of Object.entries(stems)) {
        const stemCard = document.createElement("div");
        stemCard.style.cssText = `
            background: white; 
            padding: 25px; 
            margin: 20px 0; 
            border-radius: 12px; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        `;

        let cardHTML = `
            <h4 style="color: #764ba2; margin: 0 0 15px 0; font-size: 20px; text-transform: uppercase;">
                ${name} ${getStemEmoji(name)}
            </h4>
            <audio controls style="width: 100%; margin-bottom: 15px;" src="http://127.0.0.1:8000${url}"></audio>
        `;

        // Check if we have instrument data
        if (instruments && instruments[name]) {
            console.log(`[DEBUG] ${name} stem has instruments:`, instruments[name]);
            
            if (name === "other") {
                // For "other" stem, show button to expand details
                cardHTML += `
                    <button 
                        onclick="toggleInstruments('${name}')" 
                        id="btn-${name}"
                        style="
                            padding: 12px 24px; 
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            color: white; 
                            border: none; 
                            border-radius: 8px; 
                            cursor: pointer; 
                            font-size: 16px;
                            font-weight: bold;
                            transition: transform 0.2s;
                        "
                        onmouseover="this.style.transform='translateY(-2px)'"
                        onmouseout="this.style.transform='translateY(0)'"
                    >
                        🔍 View Detected Instruments
                    </button>
                    <div id="instruments-${name}" style="display: none; margin-top: 20px;">
                    </div>
                `;
            } else {
                // For other stems, show instrument info directly
                const inst = instruments[name][0];
                const confidence = (inst.confidence * 100).toFixed(0);
                cardHTML += `
                    <div style="
                        margin-top: 15px; 
                        padding: 15px; 
                        background: linear-gradient(135deg, #e7f3ff 0%, #f0e7ff 100%); 
                        border-radius: 8px;
                        border-left: 4px solid #667eea;
                    ">
                        <div style="font-size: 16px; font-weight: bold; color: #333; margin-bottom: 8px;">
                            🎸 ${inst.instrument.replace(/_/g, ' ').toUpperCase()}
                        </div>
                        <div style="margin: 5px 0;">
                            <span style="background: #4CAF50; color: white; padding: 4px 12px; border-radius: 12px; font-size: 13px; font-weight: bold;">
                                ${confidence}% Confidence
                            </span>
                            <span style="background: #2196F3; color: white; padding: 4px 12px; border-radius: 12px; font-size: 13px; font-weight: bold; margin-left: 8px;">
                                ${inst.category}
                            </span>
                        </div>
                        ${inst.characteristics ? `
                            <div style="margin-top: 10px; font-size: 14px; color: #666; font-style: italic;">
                                💡 ${inst.characteristics}
                            </div>
                        ` : ''}
                    </div>
                `;
            }
        }

        stemCard.innerHTML = cardHTML;
        stemsDiv.appendChild(stemCard);
    }

    // Store instruments data globally for button handler
    window.instrumentsData = instruments;
}

function toggleInstruments(stemName) {
    const detailsDiv = document.getElementById(`instruments-${stemName}`);
    const button = document.getElementById(`btn-${stemName}`);
    
    if (detailsDiv.style.display === "none") {
        // Show instruments
        const instruments = window.instrumentsData[stemName];
        
        console.log(`[DEBUG] Showing instruments for ${stemName}:`, instruments);
        
        let html = `
            <div style="
                background: #f8f9fa; 
                padding: 20px; 
                border-radius: 8px;
                border: 2px solid #667eea;
            ">
                <h5 style="color: #333; margin: 0 0 20px 0; font-size: 18px;">
                    🎹 Detected Instruments in ${stemName.toUpperCase()} Stem:
                </h5>
        `;
        
        if (instruments && instruments.length > 0) {
            for (let inst of instruments) {
                const confidence = (inst.confidence * 100).toFixed(0);
                html += `
                    <div style="
                        background: white; 
                        padding: 20px; 
                        margin: 15px 0; 
                        border-radius: 8px; 
                        border-left: 5px solid #667eea;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    ">
                        <div style="font-size: 20px; font-weight: bold; color: #333; margin-bottom: 10px;">
                            🎵 ${inst.instrument.replace(/_/g, ' ').toUpperCase()}
                        </div>
                        <div style="margin: 10px 0;">
                            <span style="
                                background: #4CAF50; 
                                color: white; 
                                padding: 6px 14px; 
                                border-radius: 16px; 
                                font-size: 13px; 
                                font-weight: bold;
                            ">
                                ${confidence}% Confident
                            </span>
                            <span style="
                                background: #2196F3; 
                                color: white; 
                                padding: 6px 14px; 
                                border-radius: 16px; 
                                font-size: 13px; 
                                font-weight: bold; 
                                margin-left: 8px;
                            ">
                                ${inst.category}
                            </span>
                        </div>
                        ${inst.characteristics ? `
                            <div style="
                                margin-top: 15px; 
                                padding: 12px; 
                                background: #fff3cd; 
                                border-radius: 6px; 
                                font-size: 14px; 
                                color: #856404;
                                border-left: 3px solid #ffc107;
                            ">
                                💡 <strong>Characteristics:</strong> ${inst.characteristics}
                            </div>
                        ` : ''}
                    </div>
                `;
            }
        } else {
            html += "<p style='color: #666;'>No instruments detected in this stem.</p>";
        }
        
        html += "</div>";
        detailsDiv.innerHTML = html;
        detailsDiv.style.display = "block";
        button.textContent = "🔼 Hide Instruments";
    } else {
        // Hide instruments
        detailsDiv.style.display = "none";
        button.textContent = "🔍 View Detected Instruments";
    }
}

function getStemEmoji(stem) {
    const emojis = {
        'drums': '🥁',
        'bass': '🎸',
        'vocals': '🎤',
        'other': '🎹'
    };
    return emojis[stem] || '🎵';
}